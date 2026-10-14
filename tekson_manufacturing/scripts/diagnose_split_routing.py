"""
Split Routing (Dual Target FG Warehouse) Diagnostic - read-only

Explains why a Production Plan did (or did not) create one Work Order per
Target FG Warehouse for components whose BOM has both target_fg_warehouse
and target_fg_warehouse_2 configured.

Sections:
  1. Environment - custom field present, override class active, app version
  2. BOM config  - every dual-target demand row vs its parent source_warehouse
  3. Prediction  - re-runs Production Plan.get_sub_assembly_items() IN MEMORY
                   (never saved) with the installed code, i.e. the Work Orders
                   that WOULD be created right now
  4. Verdict     - saved sub-assembly rows vs fresh prediction vs config

Usage:
    bench --site <site> execute tekson_manufacturing.scripts.diagnose_split_routing.diagnose --args '["MFG-PP-2026-00001"]'
    bench --site <site> execute tekson_manufacturing.scripts.diagnose_split_routing.diagnose_bom --args '["BOM-Core Assembly-001"]'

Read-only: nothing is written to the database. The plan is re-exploded on a
throwaway in-memory document only.
"""

import frappe

SEP = "=" * 80


def _bom_target_fields():
    fields = ["name", "item", "target_fg_warehouse"]
    if frappe.get_meta("BOM").has_field("target_fg_warehouse_2"):
        fields.append("target_fg_warehouse_2")
    return fields


def _env_report():
    """Section 1: is the split-routing code and field actually present?"""
    import tekson_manufacturing
    from tekson_manufacturing.overrides.production_plan import TeksonProductionPlan

    hook = frappe.get_hooks("override_doctype_class") or {}
    value = hook.get("Production Plan") or ""
    if isinstance(value, (list, tuple)):
        value = value[-1] if value else ""

    return {
        "version": getattr(tekson_manufacturing, "__version__", "unknown"),
        "field_ok": frappe.get_meta("BOM").has_field("target_fg_warehouse_2"),
        "method_ok": hasattr(TeksonProductionPlan, "_route_split_fg_warehouse"),
        "registered": "TeksonProductionPlan" in str(value),
        "hook_value": str(value),
    }


def _child_targets(bom_no):
    return frappe.db.get_value("BOM", bom_no, _bom_target_fields(), as_dict=True) or frappe._dict()


def _active_bom_for_item(item_code):
    return frappe.db.get_value(
        "BOM",
        {"item": item_code, "is_active": 1, "docstatus": 1},
        _bom_target_fields(),
        as_dict=True,
    )


def _walk_config(bom_no, state=None, seen=None):
    """Walk the BOM tree; record dual-target children and source mismatches.

    state["refs"][item] counts parent rows demanding a dual-target child
    (per unit of the top BOM) - the number of demands that must be routed.
    """
    if state is None:
        state = {"dual_children": {}, "checks": [], "flags": [], "refs": {}}
    if seen is None:
        seen = set()
    if not bom_no or bom_no in seen:
        return state
    seen.add(bom_no)

    rows = frappe.get_all(
        "BOM Item",
        filters={"parent": bom_no},
        fields=["item_code", "qty", "source_warehouse", "bom_no"],
        order_by="idx",
    )

    for row in rows:
        if not row.bom_no:
            own = _active_bom_for_item(row.item_code)
            if own and own.get("target_fg_warehouse_2"):
                state["flags"].append(
                    {
                        "type": "NOT_EXPANDABLE",
                        "parent_bom": bom_no,
                        "item": row.item_code,
                        "detail": "row has no BOM No linked - this demand is never exploded, "
                        "so no Work Order can be created for it",
                    }
                )
            continue

        targets = _child_targets(row.bom_no)
        secondary = targets.get("target_fg_warehouse_2")
        if secondary:
            primary = targets.get("target_fg_warehouse")
            source = row.source_warehouse
            if not source:
                verdict = "FAIL - Source Warehouse is empty"
            elif source in (primary, secondary):
                verdict = f"OK - routes to {source}"
            else:
                verdict = f"FAIL - {source} matches neither target"
            state["refs"][row.item_code] = state["refs"].get(row.item_code, 0) + 1
            state["dual_children"].setdefault(
                row.item_code,
                {"bom": row.bom_no, "primary": primary, "secondary": secondary},
            )
            state["checks"].append(
                {
                    "parent_bom": bom_no,
                    "item": row.item_code,
                    "source": source,
                    "primary": primary,
                    "secondary": secondary,
                    "verdict": verdict,
                }
            )

        _walk_config(row.bom_no, state, seen)

    return state


def _split_analysis(state, rows):
    """For each dual-target component: how many demands, into how many WIPs."""
    analysis = {}
    for item in state.get("refs", {}):
        matched = [r for r in rows if r["item"] == item]
        fgs = sorted({(r.get("fg_warehouse") or "(blank)") for r in matched})
        refs = state["refs"][item]
        analysis[item] = {
            "demands_expected": refs,
            "rows": len(matched),
            "distinct_fg": fgs,
            "split_ok": refs < 2 or len(fgs) >= 2,
            **state["dual_children"][item],
        }
    return analysis


def _print_analysis(title, analysis):
    print(f"\n{title}")
    print("-" * len(title))
    if not analysis:
        print("  (no dual-target BOMs in this tree - one WO with the primary target, as before)")
        return
    for item, info in analysis.items():
        status = "OK" if info["split_ok"] else "FAIL"
        print(f"  [{status}] {item}  ({info['bom']})")
        print(f"         targets       : {info['primary']} | {info['secondary']}")
        print(f"         demands in BOM: {info['demands_expected']}")
        print(f"         WO rows       : {info['rows']} -> {', '.join(info['distinct_fg']) or '-'}")
        if not info["split_ok"]:
            if info["rows"] == 0:
                print("         -> no WO rows exploded (check skip_available_sub_assembly_item / stock)")
            else:
                print("         -> demands merged into one WO: see config mismatches above")


def _saved_or_fresh_rows(rows):
    return [
        {
            "item": r.production_item,
            "qty": r.qty,
            "fg_warehouse": r.fg_warehouse,
            "bom_no": r.bom_no,
        }
        for r in rows
    ]


def _fg_rows(plan):
    rows = []
    for d in plan.po_items:
        bom = frappe.db.get_value("BOM", d.bom_no, _bom_target_fields(), as_dict=True) if d.bom_no else None
        fg = d.warehouse or (bom.get("target_fg_warehouse") if bom else None)
        rows.append(
            {
                "item": d.item_code,
                "qty": d.planned_qty,
                "fg_warehouse": fg,
                "bom_no": d.bom_no,
                "note": "" if d.warehouse else "plan row warehouse blank -> WO hook uses BOM target",
            }
        )
    return rows


def _print_wos(title, rows):
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("  (none)")
        return
    for r in rows:
        note = f"   ({r['note']})" if r.get("note") else ""
        print(f"  {r['item']}  qty {r['qty']}  ->  {r['fg_warehouse'] or '(blank)'}{note}")


def diagnose(plan_name):
    """Diagnose split routing for a Production Plan. Read-only."""
    print(SEP)
    print("SPLIT ROUTING DIAGNOSTIC (read-only)")
    print(f"Production Plan: {plan_name}")
    print(SEP)

    if not frappe.db.exists("Production Plan", plan_name):
        print(f"FAIL - Production Plan not found: {plan_name}")
        return {"verdict": "PLAN_NOT_FOUND"}

    plan = frappe.get_doc("Production Plan", plan_name)
    env = _env_report()

    print("\n1. ENVIRONMENT")
    print("-" * 16)
    print(f"  app version                 : {env['version']}")
    print(f"  BOM.target_fg_warehouse_2   : {'present' if env['field_ok'] else 'MISSING (run bench migrate)'}")
    print(f"  override class registered   : {'yes' if env['registered'] else 'NO'} ({env['hook_value'] or 'not set'})")
    print(f"  _route_split_fg_warehouse   : {'yes' if env['method_ok'] else 'NO (code not deployed)'}")
    print(f"  plan sub_assembly_warehouse : {plan.sub_assembly_warehouse or '(blank)'}")
    print(f"  plan combine_sub_items      : {'yes' if plan.combine_sub_items else 'no'}")
    print(f"  plan skip_available_sub_asm : {'yes' if plan.skip_available_sub_assembly_item else 'no'}")

    state = None
    if env["field_ok"]:
        seen = set()
        for po in plan.po_items:
            if po.bom_no:
                state = _walk_config(po.bom_no, state, seen)

    print("\n2. BOM CONFIGURATION")
    print("-" * 21)
    if state is None:
        print("  SKIP - custom field missing, cannot evaluate split routing")
    else:
        checks = state["checks"]
        if not checks:
            print("  No dual-target (Target FG Warehouse 2) BOMs referenced by this plan.")
        for c in checks:
            status = "OK  " if c["verdict"].startswith("OK") else "FAIL"
            print(f"  [{status}] {c['item']} in {c['parent_bom']}")
            print(f"          source : {c['source'] or '(empty)'}")
            print(f"          targets: {c['primary']} | {c['secondary']}")
            print(f"          {c['verdict']}")
        for flag in state["flags"]:
            print(f"  [FAIL] {flag['item']} in {flag['parent_bom']}: {flag['detail']}")

    saved = _saved_or_fresh_rows(plan.sub_assembly_items)
    try:
        plan.get_sub_assembly_items()
    except Exception as exc:
        print(f"\nFAIL - explosion error: {exc}")
        print(f"\n{SEP}\nVERDICT: EXPLOSION_ERROR - the plan itself cannot be exploded\n{SEP}")
        return {"verdict": "EXPLOSION_ERROR", "error": str(exc), "env": env, "saved_rows": saved}
    fresh = _saved_or_fresh_rows(plan.sub_assembly_items)

    _print_wos("3a. WORK ORDERS SAVED ON THIS PLAN (as-is)", saved)
    _print_wos("3b. WORK ORDERS A FRESH EXPLOSION WOULD CREATE NOW", _fg_rows(plan) + fresh)

    saved_analysis = _split_analysis(state, saved) if state else {}
    fresh_analysis = _split_analysis(state, fresh) if state else {}
    if saved:
        _print_analysis("4a. SPLIT OF SAVED ROWS", saved_analysis)
    else:
        print("\n4a. SPLIT OF SAVED ROWS\n----------------------\n  (plan has no saved sub-assembly rows yet)")
    _print_analysis("4b. SPLIT OF FRESH EXPLOSION", fresh_analysis)

    verdict, remedy = _verdict(env, state, saved, fresh, saved_analysis, fresh_analysis)

    print(f"\n{SEP}\nVERDICT: {verdict}\n{SEP}")
    if remedy:
        print("REMEDY:")
        for line in remedy:
            print(f"  - {line}")
    print("No data was saved - close this session and re-run Get Sub Assembly Items to apply.\n")

    return {
        "verdict": verdict,
        "remedy": remedy,
        "env": env,
        "config_checks": state["checks"] if state else [],
        "config_flags": state["flags"] if state else [],
        "saved_rows": saved,
        "fresh_rows": fresh,
        "saved_analysis": saved_analysis,
        "fresh_analysis": fresh_analysis,
    }


def _verdict(env, state, saved, fresh, saved_analysis, fresh_analysis):
    if not env["field_ok"]:
        return (
            "PATCH_NOT_RUN",
            ["run `bench --site <site> migrate` to create BOM.target_fg_warehouse_2"],
        )
    if not env["registered"] or not env["method_ok"]:
        return (
            "OVERRIDE_NOT_ACTIVE",
            [
                "TeksonProductionPlan is not registered/loaded - check hooks.py and redeploy",
                "run `bench --site <site> migrate` then `bench --site <site> restart`",
            ],
        )
    if state is None:
        return "PATCH_NOT_RUN", ["run `bench --site <site> migrate`"]

    not_expandable = [f for f in state["flags"] if f["type"] == "NOT_EXPANDABLE"]

    if not fresh_analysis:
        if not_expandable:
            remedy = [f"{f['item']} in {f['parent_bom']}: {f['detail']}" for f in not_expandable]
            remedy.append(
                "fix the BOM, then create a NEW Production Plan (or re-run Get Sub Assembly Items)"
            )
            return "CONFIG_MISMATCH - a dual-target demand is never exploded", remedy
        return "OK - no dual-target BOMs referenced; one WO per component with its primary target", []

    failed_cfg = [c for c in state["checks"] if not c["verdict"].startswith("OK")]
    fresh_fails = [i for i, a in fresh_analysis.items() if not a["split_ok"]]
    saved_fails = [i for i, a in saved_analysis.items() if not a["split_ok"]]

    if fresh_fails or not_expandable:
        remedy = []
        for item in fresh_fails:
            for c in failed_cfg:
                if c["item"] == item:
                    remedy.append(
                        f"{item} in {c['parent_bom']}: set Source Warehouse to "
                        f"{c['primary']} or {c['secondary']} (currently {c['source'] or '(empty)'})"
                    )
        for f in not_expandable:
            remedy.append(f"{f['item']} in {f['parent_bom']}: link the BOM No on that row")
        if not remedy:
            remedy.append(
                "demands did not split although sources match - inspect fresh rows above "
                "and confirm this app version is deployed on all workers"
            )
        remedy.append("fix the BOM, then create a NEW Production Plan (or re-run Get Sub Assembly Items)")
        return "CONFIG_MISMATCH - demands merge into one Work Order or are never exploded", remedy

    if not saved:
        return (
            "NO_SAVED_ROWS - plan has no sub-assembly rows yet",
            ["run Get Sub Assembly Items on the plan, then Make Work Order"],
        )

    if saved_fails and not fresh_fails:
        return (
            "STALE_ROWS - saved rows predate the current config/code",
            [
                "run `bench --site <site> restart` so workers load the current code",
                "re-run Get Sub Assembly Items on this plan (or create a new plan)",
                "then Make Work Order - fresh explosion already splits correctly",
            ],
        )

    return "OK - split routing predicts one Work Order per target warehouse", []


def diagnose_bom(bom_name):
    """Config-only check for one BOM tree (use before creating a plan). Read-only."""
    print(SEP)
    print("SPLIT ROUTING CONFIG CHECK (read-only)")
    print(f"BOM: {bom_name}")
    print(SEP)

    if not frappe.db.exists("BOM", bom_name):
        print(f"FAIL - BOM not found: {bom_name}")
        return {"verdict": "BOM_NOT_FOUND"}

    env = _env_report()
    print(f"\n  app version               : {env['version']}")
    print(f"  BOM.target_fg_warehouse_2 : {'present' if env['field_ok'] else 'MISSING (run bench migrate)'}")
    print(f"  _route_split_fg_warehouse : {'yes' if env['method_ok'] else 'NO (code not deployed)'}")

    if not env["field_ok"]:
        print("\nVERDICT: PATCH_NOT_RUN")
        return {"verdict": "PATCH_NOT_RUN"}

    state = _walk_config(bom_name)
    bom = frappe.db.get_value("BOM", bom_name, _bom_target_fields(), as_dict=True) or frappe._dict()
    print(f"\n  this BOM target 1         : {bom.get('target_fg_warehouse')}")
    print(f"  this BOM target 2         : {bom.get('target_fg_warehouse_2') or '(not set - single WO)'}")

    print("\nCONFIGURATION")
    print("-" * 13)
    for c in state["checks"]:
        status = "OK  " if c["verdict"].startswith("OK") else "FAIL"
        print(f"  [{status}] {c['item']} in {c['parent_bom']}")
        print(f"          source : {c['source'] or '(empty)'}")
        print(f"          targets: {c['primary']} | {c['secondary']}")
        print(f"          {c['verdict']}")
    for flag in state["flags"]:
        print(f"  [FAIL] {flag['item']} in {flag['parent_bom']}: {flag['detail']}")
    if not state["checks"] and not state["flags"]:
        print("  No dual-target BOMs referenced - workflow unchanged (one WO, primary target).")

    failed = [c for c in state["checks"] if not c["verdict"].startswith("OK")]
    verdict = "CONFIG_MISMATCH" if (failed or state["flags"]) else "OK"
    print(f"\n{SEP}\nVERDICT: {verdict}\n{SEP}")
    if verdict == "CONFIG_MISMATCH":
        print("Fix the [FAIL] rows above, then create the Production Plan.\n")

    return {
        "verdict": verdict,
        "config_checks": state["checks"],
        "config_flags": state["flags"],
        "dual_children": state["dual_children"],
    }
