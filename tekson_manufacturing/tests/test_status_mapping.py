"""
Pure unit tests for the Job Card slowness fix (no DB writes).

Covers the single-source-of-truth status mapping and the queued
inter-department transfer plumbing:

- compute_status_fields()           — the one mapping both validate hook and
                                      refresh use (Phase 1/2)
- map_readiness_result_to_fields()  — refresh writes exactly what save writes
- MaterialResult / ReadinessResult  — pending_transfers round-trip & factories
- enqueue_inter_department_transfers() — dedupe, validation, enqueue kwargs

Run with:
    bench --site <site> run-tests --module tekson_manufacturing.tests.test_status_mapping
    bench execute tekson_manufacturing.tests.test_status_mapping.run_tests
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tekson_manufacturing.mes.dataclasses import (
    MaterialResult,
    MaterialStatus,
    ReadinessResult,
    ReadinessStatus,
)
from tekson_manufacturing.readiness.job_card_readiness import (
    map_readiness_result_to_fields,
)
from tekson_manufacturing.readiness.material_readiness import (
    enqueue_inter_department_transfers,
)
from tekson_manufacturing.services.job_card_service import compute_status_fields


def _ready_view():
    return SimpleNamespace(is_ready=True, shortage_details=[])


def _short_view(shortages):
    return SimpleNamespace(is_ready=False, shortage_details=shortages)


class TestComputeStatusFields(unittest.TestCase):
    """compute_status_fields is the single mapping used by hook + refresh."""

    def test_completed_sets_only_three_fields(self):
        fields = compute_status_fields("Completed", {"status": "Completed"}, _ready_view(), True)
        self.assertEqual(fields, {
            "custom_start_status": "Completed",
            "custom_can_start_operation": 0,
            "custom_material_available_for_operation": 0,
        })

    def test_work_in_progress_sets_only_three_fields(self):
        fields = compute_status_fields("Work In Progress", None, _ready_view(), True)
        self.assertEqual(fields, {
            "custom_start_status": "In Progress",
            "custom_can_start_operation": 0,
            "custom_material_available_for_operation": 0,
        })

    def test_open_ready_to_start(self):
        fields = compute_status_fields("Open", None, _ready_view(), True)
        self.assertEqual(fields["custom_start_status"], "Ready to Start")
        self.assertEqual(fields["custom_dependency_check"], 1)
        self.assertEqual(fields["custom_can_start_operation"], 1)
        self.assertEqual(fields["custom_material_available_for_operation"], 1)
        self.assertEqual(fields["custom_material_status_details"], "Material available in WIP")

    def test_dependency_incomplete_wins_over_material(self):
        # DV-001 precedence: previous op incomplete even when materials are ready
        fields = compute_status_fields("Open", {"status": "In Progress"}, _ready_view(), True)
        self.assertEqual(fields["custom_start_status"], "Awaiting Previous Operation")
        self.assertEqual(fields["custom_dependency_check"], 0)
        self.assertEqual(fields["custom_can_start_operation"], 0)
        # material flag still reflects the material truth
        self.assertEqual(fields["custom_material_available_for_operation"], 1)

    def test_awaiting_material_lists_missing_items(self):
        shortages = [
            {"item_code": "ITEM-A"},
            {"item_code": "ITEM-B"},
            {"item_code": "ITEM-C"},
            {"item_code": "ITEM-D"},
        ]
        fields = compute_status_fields("Open", None, _short_view(shortages), True)
        self.assertEqual(fields["custom_start_status"], "Awaiting Material")
        self.assertEqual(fields["custom_dependency_check"], 1)
        self.assertEqual(fields["custom_can_start_operation"], 0)
        self.assertEqual(fields["custom_material_available_for_operation"], 0)
        self.assertEqual(
            fields["custom_material_status_details"],
            "Missing: ITEM-A, ITEM-B, ITEM-C (+1 more)",
        )

    def test_no_work_order_can_still_start_when_dependency_ok(self):
        fields = compute_status_fields("Open", None, None, False)
        self.assertEqual(fields["custom_start_status"], "Awaiting Material")
        self.assertEqual(fields["custom_dependency_check"], 1)
        self.assertEqual(fields["custom_can_start_operation"], 1)
        self.assertEqual(fields["custom_material_available_for_operation"], 0)
        self.assertEqual(fields["custom_material_status_details"], "Work Order not linked")

    def test_no_work_order_with_blocked_dependency(self):
        fields = compute_status_fields("Open", {"status": "Open"}, None, False)
        self.assertEqual(fields["custom_start_status"], "Awaiting Previous Operation")
        self.assertEqual(fields["custom_can_start_operation"], 0)


class TestMapReadinessResultToFields(unittest.TestCase):
    """Refresh (apply) must produce exactly what the validate hook produces."""

    def test_ready_result_maps_to_ready_fields(self):
        result = ReadinessResult.create_ready(MaterialStatus.AVAILABLE)
        fields = map_readiness_result_to_fields("Open", None, True, result)
        expected = compute_status_fields("Open", None, _ready_view(), True)
        self.assertEqual(fields, expected)
        self.assertEqual(fields["custom_start_status"], "Ready to Start")

    def test_waiting_material_result_carries_shortage_details(self):
        result = ReadinessResult.create_waiting_material("Waiting for material transfer")
        result.shortage_details = [{"item_code": "MISSING-1", "shortage_qty": 3}]
        fields = map_readiness_result_to_fields("Open", None, True, result)
        expected = compute_status_fields("Open", None, _short_view(result.shortage_details), True)
        self.assertEqual(fields, expected)
        self.assertIn("MISSING-1", fields["custom_material_status_details"])

    def test_completed_result_maps_to_status_fields_only(self):
        result = ReadinessResult.create_completed(MaterialStatus.AVAILABLE)
        fields = map_readiness_result_to_fields("Completed", {"status": "Completed"}, True, result)
        self.assertEqual(fields["custom_start_status"], "Completed")
        self.assertEqual(fields["custom_can_start_operation"], 0)
        self.assertNotIn("custom_dependency_check", fields)

    def test_dependency_row_precedence_independent_of_result_flags(self):
        # Even a "ready" ReadinessResult cannot override an incomplete prev-op ROW
        result = ReadinessResult.create_ready(MaterialStatus.AVAILABLE)
        fields = map_readiness_result_to_fields(
            "Open", {"status": "In Progress"}, True, result
        )
        self.assertEqual(fields["custom_start_status"], "Awaiting Previous Operation")
        self.assertEqual(fields["custom_can_start_operation"], 0)


class TestDataclasses(unittest.TestCase):
    def test_material_result_roundtrip_with_pending_transfers(self):
        transfers = [{
            "item_code": "RM-1",
            "qty": 5.0,
            "required_qty": 10.0,
            "source_warehouse": "WIP-Ralu In - TPL",
            "target_warehouse": "WIP-RP - TPL",
            "work_order": "WO-TEST-1",
        }]
        result = MaterialResult(
            is_ready=False,
            status=MaterialStatus.SHORT,
            available_qty=5.0,
            required_qty=10.0,
            shortage_qty=5.0,
            shortage_details=[{"item_code": "RM-1", "shortage_qty": 5.0}],
            warehouse="WIP-RP - TPL",
            message="Partial",
            pending_transfers=transfers,
        )
        restored = MaterialResult.from_dict(result.to_dict())
        self.assertEqual(restored.pending_transfers, transfers)
        self.assertEqual(restored.shortage_details, result.shortage_details)

    def test_readiness_factories(self):
        ready = ReadinessResult.create_ready(MaterialStatus.AVAILABLE)
        self.assertTrue(ready.can_start)
        self.assertTrue(ready.material_available)
        self.assertEqual(ready.readiness_status, ReadinessStatus.READY)

        waiting = ReadinessResult.create_waiting_material("msg")
        self.assertFalse(waiting.can_start)
        self.assertFalse(waiting.material_available)
        self.assertEqual(waiting.readiness_status, ReadinessStatus.WAITING_MATERIAL)

        prev_op = ReadinessResult.create_waiting_previous_op("JC-001")
        self.assertFalse(prev_op.previous_operation_complete)
        self.assertFalse(prev_op.can_start)

        blocked = ReadinessResult.create_blocked(MaterialStatus.WAITING, "Job Card not linked to Work Order")
        self.assertFalse(blocked.material_available)
        self.assertEqual(blocked.readiness_status, ReadinessStatus.BLOCKED)

    def test_completed_factory_allows_material_status(self):
        completed = ReadinessResult.create_completed(MaterialStatus.AVAILABLE)
        self.assertEqual(completed.material_status, MaterialStatus.AVAILABLE)
        self.assertTrue(completed.previous_operation_complete)


class TestEnqueueInterDepartmentTransfers(unittest.TestCase):
    """Queueing of transfer execution jobs (frappe.enqueue fully mocked)."""

    def _spec(self, **overrides):
        spec = {
            "item_code": "RM-1",
            "qty": 5.0,
            "required_qty": 10.0,
            "source_warehouse": "WIP-Ralu In - TPL",
            "target_warehouse": "WIP-RP - TPL",
            "work_order": "WO-TEST-1",
        }
        spec.update(overrides)
        return spec

    def test_empty_input_enqueues_nothing(self):
        with patch("frappe.enqueue") as mock_enqueue:
            self.assertEqual(enqueue_inter_department_transfers([]), [])
            self.assertEqual(enqueue_inter_department_transfers(None), [])
            mock_enqueue.assert_not_called()

    def test_deduplicates_same_wo_item_target(self):
        with patch("frappe.enqueue") as mock_enqueue:
            queued = enqueue_inter_department_transfers(
                [self._spec(), self._spec(qty=99.0)]
            )
            self.assertEqual(len(queued), 1)
            self.assertEqual(mock_enqueue.call_count, 1)
            self.assertEqual(
                queued[0],
                ("WO-TEST-1", "RM-1", "WIP-RP - TPL"),
            )

    def test_skips_incomplete_specs(self):
        with patch("frappe.enqueue") as mock_enqueue:
            queued = enqueue_inter_department_transfers([
                {"item_code": "RM-1"},  # missing target + WO
                self._spec(),
            ])
            self.assertEqual(len(queued), 1)
            self.assertEqual(mock_enqueue.call_count, 1)

    def test_accepts_result_object_with_pending_transfers(self):
        result = ReadinessResult.create_waiting_material("short")
        result.pending_transfers = [self._spec()]
        with patch("frappe.enqueue") as mock_enqueue:
            queued = enqueue_inter_department_transfers(result)
            self.assertEqual(len(queued), 1)
            mock_enqueue.assert_called_once()

    def test_enqueue_kwargs_and_after_commit_passthrough(self):
        with patch("frappe.enqueue") as mock_enqueue:
            enqueue_inter_department_transfers(
                [self._spec()], after_commit=False
            )
            kwargs = mock_enqueue.call_args.kwargs
            self.assertFalse(kwargs["enqueue_after_commit"])
            self.assertTrue(kwargs["deduplicate"])
            self.assertEqual(kwargs["queue"], "short")
            self.assertIn(
                "mes-inter-dept-transfer::WO-TEST-1::RM-1::WIP-RP - TPL",
                kwargs["job_id"],
            )
            self.assertEqual(kwargs["item_code"], "RM-1")
            self.assertEqual(kwargs["required_qty"], 10.0)
            self.assertEqual(kwargs["target_warehouse"], "WIP-RP - TPL")
            self.assertEqual(kwargs["work_order"], "WO-TEST-1")

    def test_enqueue_failure_is_swallowed(self):
        with patch("frappe.enqueue", side_effect=Exception("queue overloaded")):
            queued = enqueue_inter_department_transfers([self._spec()])
            self.assertEqual(queued, [])


def run_tests():
    """Run all status-mapping / queueing unit tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestComputeStatusFields))
    suite.addTests(loader.loadTestsFromTestCase(TestMapReadinessResultToFields))
    suite.addTests(loader.loadTestsFromTestCase(TestDataclasses))
    suite.addTests(loader.loadTestsFromTestCase(TestEnqueueInterDepartmentTransfers))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    run_tests()
