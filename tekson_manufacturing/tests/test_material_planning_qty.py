"""
Unit Tests for Daily Material Planning quantity calculation (MP-002)

Business expectation (fixed in 15.1.36):
    MR Qty = (required incl. RM Loss, aggregated across ALL Work Orders of the
    day) - (stock already available in the target WIP warehouse)

Covers the regression where:
  1. full BOM qty was requested even when stock existed in WIP
  2. a requirement vanished when stock covered one WO but not the day's total
  3. the same stock was deducted once per source warehouse / Bin lookup
     depended on a '%WIP%' pattern instead of the exact warehouse

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
    """Minimal frappe facade covering what material_planning_service calls."""

    def __init__(self, wos=(), bom_items=None, bins=(), bom_qty=None):
        self.wos = list(wos)
        self.bom_items = bom_items or {}
        self.bins = list(bins)
        self.bom_qty = bom_qty or {}
        self.mrs = []
        self.defaults = types.SimpleNamespace(get_defaults=lambda: types.SimpleNamespace(company="Test Co"))
        self.db = types.SimpleNamespace(get_value=self._db_get_value, sql=self._db_sql)

    def get_all(self, doctype, filters=None, fields=None, **kwargs):
        if doctype == "Work Order":
            return list(self.wos)
        if doctype == "Job Card":
            return []
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
        return None

    def _db_sql(self, *args, **kwargs):
        return []  # no existing draft Material Requests


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


class TestMaterialPlanningRequiredQty(unittest.TestCase):
    PLANNED_DATE = "2026-10-26"

    def run_generate(self, wos, bom_items, bins=(), bom_qty=None):
        fake = FakeFrappe(wos=wos, bom_items=bom_items, bins=bins, bom_qty=bom_qty)
        with patch.object(mps, "frappe", fake), patch.object(mps, "_", lambda msg, *a, **k: msg):
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


if __name__ == "__main__":
    unittest.main()
