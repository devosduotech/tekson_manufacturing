"""
Unit Tests for Daily Material Planning quantity calculation (MP-002)
and operation-driven target warehouse resolution (15.1.37)

Business expectation (fixed in 15.1.36):
    MR Qty = (required incl. RM Loss, aggregated across ALL Work Orders of the
    day) - (stock already available in the target WIP warehouse)

Business expectation (fixed in 15.1.37):
    The MR target warehouse comes from the BOM Item's operation
    (BOM Operation -> workstation -> plant floor -> WIP-{floor} - TPL),
    falling back to the Job Card's WIP — never the Work Order header
    warehouse (derived from the first operation).

Covers the regressions where:
  1. full BOM qty was requested even when stock existed in WIP
  2. a requirement vanished when stock covered one WO but not the day's total
  3. the same stock was deducted once per source warehouse / Bin lookup
     depended on a '%WIP%' pattern instead of the exact warehouse
  4. an operation-bearing item's MR line targeted the first-operation WIP
     when the Job Card lookup missed (key mismatch) or no JC existed yet

Runs standalone (no bench/site required):
    python3 tekson_manufacturing/tests/test_material_planning_qty.py
"""

import os
import sys
import types
import unittest
from unittest.mock import patch

# Make the package importable when the file is executed directly
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _install_minimal_frappe():
    """Provide an import-time frappe stub when not running under bench."""
    if "frappe" in sys.modules:
        return sys.modules["frappe"]
    stub = types.ModuleType("frappe")
    stub.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    stub._ = lambda msg, *args, **kwargs: msg
    stub.get_all = lambda *args, **kwargs: []
    stub.log_error = lambda *args, **kwargs: None
    stub.db = types.SimpleNamespace(get_value=lambda *a, **k: None, sql=lambda *a, **k: [])
    stub.defaults = types.SimpleNamespace(get_defaults=lambda: types.SimpleNamespace(company="Test Co"))
    sys.modules["frappe"] = stub
    return stub


_install_minimal_frappe()

from tekson_manufacturing.planning import material_planning_service as mps
from tekson_manufacturing.utils import operation_warehouse as owh


class Row(dict):
    """frappe._dict-like row: supports both attribute and key access."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class FakeMR:
    def __init__(self, fake, doc):
        self._fake = fake
        self.doc = dict(doc)
        self.items = []
        self.name = f"MR-{len(fake.mrs) + 1:05d}"

    def set(self, field, value):
        if field == "items":
            self.items = list(value)
        else:
            self.doc[field] = value

    def append(self, field, row):
        assert field == "items", "Material Request only receives items"
        self.items.append(dict(row))

    def insert(self):
        self._fake.mrs.append(self)
        return self

    def save(self):
        if self not in self._fake.mrs:
            self._fake.mrs.append(self)
        return self


class FakeFrappe:
    """Minimal frappe facade covering what material_planning_service and
    utils.operation_warehouse call."""

    def __init__(self, wos=(), bom_items=None, bins=(), bom_qty=None,
                 jcs=(), bom_operations=None, workstations=(), warehouses=()):
        self.wos = list(wos)
        self.bom_items = bom_items or {}
        self.bins = list(bins)
        self.bom_qty = bom_qty or {}
        self.jcs = list(jcs)
        self.bom_operations = bom_operations or {}
        self.workstations = list(workstations)
        self.warehouses = set(warehouses)
        self.mrs = []
        self.defaults = types.SimpleNamespace(get_defaults=lambda: types.SimpleNamespace(company="Test Co"))
        self.db = types.SimpleNamespace(
            get_value=self._db_get_value, sql=self._db_sql, exists=self._db_exists
        )

    def get_all(self, doctype, filters=None, fields=None, **kwargs):
        if doctype == "Work Order":
            return list(self.wos)
        if doctype == "Job Card":
            return list(self.jcs)
        if doctype == "BOM Operation":
            return list(self.bom_operations.get((filters or {}).get("parent"), []))
        if doctype == "BOM Item":
            return list(self.bom_items.get((filters or {}).get("parent"), []))
        if doctype == "Bin":
            rows = self.bins
            item_filter = (filters or {}).get("item_code")
            wh_filter = (filters or {}).get("warehouse")
            if isinstance(item_filter, list) and item_filter and item_filter[0] == "in":
                wanted = set(item_filter[1])
                rows = [r for r in rows if r.item_code in wanted]
            if isinstance(wh_filter, list) and wh_filter and wh_filter[0] == "in":
                wanted = set(wh_filter[1])
                rows = [r for r in rows if r.warehouse in wanted]
            return list(rows)
        return []

    def get_doc(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict):
            return FakeMR(self, args[0])
        raise AssertionError(f"Unexpected get_doc call: {args!r}")

    def log_error(self, *args, **kwargs):
        pass

    def _db_get_value(self, doctype, filters, field=None, *args, **kwargs):
        if doctype == "BOM":
            if isinstance(filters, str):
                return self.bom_qty.get(filters, 1.0)
            return None  # default-BOM lookup: no sub-assemblies in these tests
        if doctype == "Warehouse":
            if isinstance(filters, str):
                # name -> warehouse_name: echo back so name-contains checks pass
                return filters
            return None
        if doctype == "Workstation":
            if isinstance(filters, dict):
                wanted = filters.get("workstation_type")
                matches = sorted(
                    (w for w in self.workstations if w.get("workstation_type") == wanted),
                    key=lambda w: w["name"],
                )
                return matches[0]["name"] if matches else None
            for w in self.workstations:
                if w["name"] == filters:
                    return w.get(field)
            return None
        return None

    def _db_sql(self, *args, **kwargs):
        return []  # no existing draft Material Requests

    def _db_exists(self, doctype, name):
        if doctype == "Warehouse":
            return name if name in self.warehouses else None
        if doctype == "Workstation":
            return name if any(w["name"] == name for w in self.workstations) else None
        return None


def make_wo(name, qty, wip_warehouse, bom_no="BOM-1",
            source_warehouse="Raw Material Stores - TPL", planned_start_date="2026-10-26"):
    return Row(
        name=name, qty=qty, wip_warehouse=wip_warehouse, bom_no=bom_no,
        source_warehouse=source_warehouse, planned_start_date=planned_start_date,
        status="In Process", docstatus=1, production_plan="PP-TEST",
    )


def make_bom_item(item_code, qty, rm_loss_pct=0,
                  source_warehouse="Raw Material Stores - TPL", operation=None, uom="Nos"):
    return Row(
        item_code=item_code, item_name=item_code, qty=qty, uom=uom,
        source_warehouse=source_warehouse, operation=operation,
        do_not_explode=0, bom_no=None, custom_rm_loss_pct=rm_loss_pct,
    )


def make_bin(item_code, warehouse, actual_qty):
    return Row(item_code=item_code, warehouse=warehouse, actual_qty=actual_qty)


def make_bom_operation(operation, workstation_type=None, workstation=None, idx=1):
    return Row(operation=operation, workstation_type=workstation_type,
               workstation=workstation, idx=idx)


def make_workstation(name, workstation_type, plant_floor):
    return Row(name=name, workstation_type=workstation_type, plant_floor=plant_floor)


class TestMaterialPlanningRequiredQty(unittest.TestCase):
    PLANNED_DATE = "2026-10-26"

    def run_generate(self, wos, bom_items, bins=(), bom_qty=None, **fake_kwargs):
        fake = FakeFrappe(wos=wos, bom_items=bom_items, bins=bins,
                          bom_qty=bom_qty, **fake_kwargs)
        with patch.object(mps, "frappe", fake), \
                patch.object(owh, "frappe", fake), \
                patch.object(mps, "_", lambda msg, *a, **k: msg):
            result = mps.generate_daily_material_requests("PP-TEST", self.PLANNED_DATE)
        return result, fake

    @staticmethod
    def all_lines(fake):
        return [line for mr in fake.mrs for line in mr.items]

    def test_partial_stock_requests_only_the_balance(self):
        """WIP holds 8 of 20 required → request 12 (not the full 20)."""
        result, fake = self.run_generate(
            wos=[make_wo("WO-1", qty=2, wip_warehouse="WIP-CNC")],
            bom_items={"BOM-1": [make_bom_item("ITEM-X", qty=10)]},
            bins=[make_bin("ITEM-X", "WIP-CNC", 8)],
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["qty"], 12)
        self.assertEqual(lines[0]["custom_bom_qty"], 12)
        self.assertEqual(lines[0]["from_warehouse"], "Raw Material Stores - TPL")
        self.assertEqual(result["total_items"], 1)

    def test_stock_covering_each_wo_individually_still_requests_balance(self):
        """Stock covers each WO alone but not both — balance must not vanish."""
        _result, fake = self.run_generate(
            wos=[make_wo("WO-1", 1, "WIP-CNC"), make_wo("WO-2", 1, "WIP-CNC")],
            bom_items={"BOM-1": [make_bom_item("ITEM-X", qty=10)]},
            bins=[make_bin("ITEM-X", "WIP-CNC", 10)],
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["qty"], 10)  # 20 required - 10 available

    def test_fully_covered_by_stock_creates_no_request(self):
        result, fake = self.run_generate(
            wos=[make_wo("WO-1", 2, "WIP-CNC")],
            bom_items={"BOM-1": [make_bom_item("ITEM-X", qty=10)]},
            bins=[make_bin("ITEM-X", "WIP-CNC", 25)],
        )
        self.assertEqual(fake.mrs, [])
        self.assertIn("All materials already in WIP", result["message"])

    def test_rm_loss_and_stock_keep_bom_loss_invariant(self):
        """Balance incl. loss = 12.6 → qty 13; custom fields split the balance."""
        _result, fake = self.run_generate(
            wos=[make_wo("WO-1", 2, "WIP-CNC")],
            bom_items={"BOM-1": [make_bom_item("ITEM-X", qty=10, rm_loss_pct=3)]},
            bins=[make_bin("ITEM-X", "WIP-CNC", 8)],
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        line = lines[0]
        # required = 20 x 1.03 = 20.6; balance = 20.6 - 8 = 12.6 → rounded up
        self.assertEqual(line["qty"], 13)
        self.assertAlmostEqual(line["custom_bom_qty"] + line["custom_rm_loss_qty"], 12.6, places=9)
        self.assertAlmostEqual(line["custom_rm_loss_pct"], 3.0, places=9)
        # client script formula: loss = qty x pct / (1 + pct)
        self.assertAlmostEqual(line["custom_rm_loss_qty"], 12.6 * 3 / 103, places=9)

    def test_same_item_from_two_sources_deducts_stock_once(self):
        """Stock must not be deducted once per source warehouse."""
        wos = [
            make_wo("WO-1", 1, "WIP-CNC", bom_no="BOM-1"),
            make_wo("WO-2", 1, "WIP-CNC", bom_no="BOM-2"),
        ]
        bom_items = {
            "BOM-1": [make_bom_item("ITEM-X", 10, source_warehouse="Raw Material Stores - TPL")],
            "BOM-2": [make_bom_item("ITEM-X", 10, source_warehouse="BOF Stores - TPL")],
        }
        _result, fake = self.run_generate(wos, bom_items, bins=[make_bin("ITEM-X", "WIP-CNC", 6)])
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 2)
        # 20 required - 6 available = 14, split across the two sources
        self.assertEqual(sorted(line["qty"] for line in lines), [7, 7])

    def test_stock_is_per_target_warehouse_and_matched_exactly(self):
        """Each target only sees its own stock; Bin lookup uses exact names."""
        wos = [make_wo("WO-1", 1, "WIP-CNC"), make_wo("WO-2", 1, "Assembly - TPL")]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10)]}
        bins = [make_bin("ITEM-X", "WIP-CNC", 5), make_bin("ITEM-X", "Assembly - TPL", 5)]
        _result, fake = self.run_generate(wos, bom_items, bins)
        by_wh = {line["warehouse"]: line["qty"] for line in self.all_lines(fake)}
        self.assertEqual(by_wh, {"WIP-CNC": 5, "Assembly - TPL": 5})

    def test_wo_without_wip_warehouse_reports_warning(self):
        result, fake = self.run_generate(
            wos=[make_wo("WO-1", 1, wip_warehouse="")],
            bom_items={"BOM-1": [make_bom_item("ITEM-X", 10)]},
        )
        self.assertEqual(fake.mrs, [])
        self.assertTrue(any("WO-1" in warning for warning in result["warnings"]))
        self.assertIn("No material requirements", result["message"])

    def test_no_work_orders_returns_empty(self):
        fake = FakeFrappe(wos=[])
        with patch.object(mps, "frappe", fake), patch.object(mps, "_", lambda msg, *a, **k: msg):
            result = mps.generate_daily_material_requests("PP-TEST", self.PLANNED_DATE)
        self.assertEqual(result["created_mrs"], [])
        self.assertIn("No Work Orders", result["message"])


class TestOperationTargetWarehouse(unittest.TestCase):
    """15.1.37: transfers target the BOM Item's operation warehouse.

    The Work Order header warehouse is derived from the BOM's FIRST
    operation and must never be used for operation-bearing items — BOMs
    span multiple plant floors.
    """

    PLANNED_DATE = "2026-10-26"
    WIP_FIRST_OP = "WIP-W - TPL"   # WO header = first-operation floor
    WIP_OP = "WIP-RP - TPL"        # Milling operation floor

    def run_generate(self, wos, bom_items, bins=(), **fake_kwargs):
        fake = FakeFrappe(wos=wos, bom_items=bom_items, bins=bins, **fake_kwargs)
        with patch.object(mps, "frappe", fake), \
                patch.object(owh, "frappe", fake), \
                patch.object(mps, "_", lambda msg, *a, **k: msg):
            result = mps.generate_daily_material_requests("PP-TEST", self.PLANNED_DATE)
        return result, fake

    @staticmethod
    def all_lines(fake):
        return [line for mr in fake.mrs for line in mr.items]

    @staticmethod
    def milling_config():
        return (
            {"BOM-1": [make_bom_operation("Milling", workstation_type="Milling-WS")]},
            [make_workstation("WS-Mill-1", "Milling-WS", "RP")],
        )

    def test_both_wos_target_operation_warehouse_despite_jc_key_whitespace(self):
        """Reported bug: WO-2's Job Card operation key had trailing
        whitespace → jc_map missed → MR line fell back to the WO header
        (first-operation) warehouse."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP), make_wo("WO-2", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        bom_ops, workstations = self.milling_config()
        _result, fake = self.run_generate(
            wos, bom_items,
            jcs=[
                Row(name="JC-1", work_order="WO-1", operation="Milling",
                    wip_warehouse=self.WIP_OP),
                Row(name="JC-2", work_order="WO-2", operation="Milling ",
                    wip_warehouse=self.WIP_OP),
            ],
            bom_operations=bom_ops,
            workstations=workstations,
            warehouses={self.WIP_FIRST_OP, self.WIP_OP},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)
        self.assertEqual(lines[0]["qty"], 20)

    def test_resolves_operation_warehouse_without_job_card(self):
        """Configuration alone (BOM Operation → workstation → plant floor)
        must resolve the target when no Job Card exists yet."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        bom_ops, workstations = self.milling_config()
        result, fake = self.run_generate(
            wos, bom_items,
            bom_operations=bom_ops,
            workstations=workstations,
            warehouses={self.WIP_FIRST_OP, self.WIP_OP},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)
        self.assertEqual(result["warnings"], [])

    def test_unresolvable_operation_is_skipped_never_wo_header(self):
        """No configuration, no Job Card → skip with a visible warning.
        Falling back to the WO header warehouse is never allowed."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        result, fake = self.run_generate(wos, bom_items)
        self.assertEqual(fake.mrs, [])
        self.assertTrue(any("could not be resolved" in w for w in result["warnings"]))
        self.assertIn("No material requirements", result["message"])

    def test_configuration_wins_over_stale_job_card_and_warns(self):
        """A Job Card still holding a stale WIP must not steer the transfer;
        configuration wins and the mismatch is surfaced."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        bom_ops, workstations = self.milling_config()
        result, fake = self.run_generate(
            wos, bom_items,
            jcs=[Row(name="JC-1", work_order="WO-1", operation="Milling",
                     wip_warehouse="WIP-STALE - TPL")],
            bom_operations=bom_ops,
            workstations=workstations,
            warehouses={self.WIP_FIRST_OP, self.WIP_OP, "WIP-STALE - TPL"},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)
        self.assertTrue(any("re-save the Job Card" in w for w in result["warnings"]))

    def test_job_card_warehouse_used_when_configuration_missing(self):
        """Configuration lookup fails but the Job Card has the warehouse —
        use the Job Card (execution ground truth)."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        _result, fake = self.run_generate(
            wos, bom_items,
            jcs=[Row(name="JC-1", work_order="WO-1", operation="Milling",
                     wip_warehouse=self.WIP_OP)],
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)

    def test_item_without_operation_uses_wo_header_with_warning(self):
        """No operation configured → the WO header is the only answer, but
        the gap is surfaced as a warning."""
        wos = [make_wo("WO-1", 1, "WIP-CNC")]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10)]}
        result, fake = self.run_generate(wos, bom_items)
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], "WIP-CNC")
        self.assertTrue(any("has no operation" in w for w in result["warnings"]))

    def test_operation_match_ignores_whitespace_on_bom_item(self):
        """BOM Item operation with trailing whitespace still matches the
        BOM Operation routing row."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling ")]}
        bom_ops, workstations = self.milling_config()
        _result, fake = self.run_generate(
            wos, bom_items,
            bom_operations=bom_ops,
            workstations=workstations,
            warehouses={self.WIP_FIRST_OP, self.WIP_OP},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)

    def test_operation_config_match_is_case_insensitive(self):
        """UAT: BOM Item 'Tank Assembly' vs BOM Operation 'TANK ASSEMBLY'."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Tank Assembly")]}
        _result, fake = self.run_generate(
            wos, bom_items,
            bom_operations={
                "BOM-1": [make_bom_operation("TANK ASSEMBLY", workstation_type="Tank-WS")]
            },
            workstations=[make_workstation("WS-Tank-1", "Tank-WS", "RP")],
            warehouses={self.WIP_OP},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)

    def test_job_card_fallback_matches_operation_case_insensitively(self):
        """No BOM Operation config → Job Card WIP fallback must still match
        when the JC stores the operation with different casing."""
        wos = [make_wo("WO-1", 1, self.WIP_FIRST_OP)]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Tank Assembly")]}
        _result, fake = self.run_generate(
            wos, bom_items,
            jcs=[Row(name="JC-1", work_order="WO-1", operation="tank assembly",
                     wip_warehouse=self.WIP_OP)],
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)

    def test_operation_item_resolves_even_when_wo_header_wip_missing(self):
        """Operation-bearing items no longer depend on the WO header WIP."""
        wos = [make_wo("WO-1", 1, "")]
        bom_items = {"BOM-1": [make_bom_item("ITEM-X", 10, operation="Milling")]}
        bom_ops, workstations = self.milling_config()
        result, fake = self.run_generate(
            wos, bom_items,
            bom_operations=bom_ops,
            workstations=workstations,
            warehouses={self.WIP_OP},
        )
        lines = self.all_lines(fake)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["warehouse"], self.WIP_OP)
        self.assertFalse(any("no WIP warehouse" in w for w in result["warnings"]))


class TestResolveTargetWarehouse(unittest.TestCase):
    """Direct contract tests for utils.operation_warehouse.resolve_target_warehouse."""

    WIP_OP = "WIP-RP - TPL"

    @staticmethod
    def resolve(*args, fake=None, **kwargs):
        with patch.object(owh, "frappe", fake if fake is not None else FakeFrappe()):
            return owh.resolve_target_warehouse(*args, **kwargs)

    def test_no_operation_returns_fallback(self):
        self.assertEqual(
            self.resolve("BOM-1", "", fallback_warehouse="WIP-CNC"), "WIP-CNC"
        )

    def test_unresolvable_operation_never_returns_wo_header_fallback(self):
        result = self.resolve(
            "BOM-1", "Milling", fallback_warehouse="WIP-W - TPL"
        )
        self.assertEqual(result, "")

    def test_unresolvable_operation_falls_back_to_job_card(self):
        result = self.resolve(
            "BOM-1", "Milling", jc_warehouse=self.WIP_OP,
            fallback_warehouse="WIP-W - TPL",
        )
        self.assertEqual(result, self.WIP_OP)

    def test_source_bom_preferred_over_wo_bom(self):
        """Operation lives in the child BOM's routing (leaf came from it)."""
        fake = FakeFrappe(
            bom_operations={
                "BOM-CHILD": [make_bom_operation("Milling", workstation_type="Milling-WS")]
            },
            workstations=[make_workstation("WS-Mill-1", "Milling-WS", "RP")],
            warehouses={self.WIP_OP},
        )
        result = self.resolve(
            "BOM-PARENT", "Milling", source_bom="BOM-CHILD", fake=fake
        )
        self.assertEqual(result, self.WIP_OP)

    def test_direct_workstation_link_resolves(self):
        """BOM Operation carries a direct workstation link, not a type."""
        fake = FakeFrappe(
            bom_operations={"BOM-1": [make_bom_operation("Drill", workstation="WS-D1")]},
            workstations=[make_workstation("WS-D1", "", "BOF")],
            warehouses={"WIP-BOF - TPL"},
        )
        self.assertEqual(self.resolve("BOM-1", "Drill", fake=fake), "WIP-BOF - TPL")

    def test_operation_match_is_case_insensitive(self):
        """Operation masters differ in casing between BOM Item and routing."""
        fake = FakeFrappe(
            bom_operations={
                "BOM-1": [make_bom_operation("TANK ASSEMBLY", workstation_type="Tank-WS")]
            },
            workstations=[make_workstation("WS-Tank-1", "Tank-WS", "RP")],
            warehouses={self.WIP_OP},
        )
        self.assertEqual(self.resolve("BOM-1", "Tank Assembly", fake=fake), self.WIP_OP)

    def test_missing_warehouse_returns_empty(self):
        """Plant floor resolves but the WIP warehouse does not exist."""
        fake = FakeFrappe(
            bom_operations={
                "BOM-1": [make_bom_operation("Milling", workstation_type="Milling-WS")]
            },
            workstations=[make_workstation("WS-Mill-1", "Milling-WS", "RP")],
        )
        result = self.resolve(
            "BOM-1", "Milling", fallback_warehouse="WIP-W - TPL", fake=fake
        )
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
