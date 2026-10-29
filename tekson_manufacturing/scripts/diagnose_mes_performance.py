"""
MES Performance Diagnostics - read-only

Post-deployment verification for the Job Card / Work Order slowness fix.
Nothing is written to the database; index creation is NEVER attempted
(candidates are reported for DBA review only).

Sections:
  1. Retired server scripts  - the 6 UAT scripts must be disabled, plus a
                               generic scan for any ENABLED Server Script
                               still wired to MES doctypes
  2. Error Log volume        - MES/Security titled Error Logs (last 7 days);
                               after the Phase 5 cleanup only genuine errors
                               should appear here
  3. Index candidates        - presence check for indexes backing the hot
                               queries (Job Card work_order, Stock Entry
                               work_order/purpose, Bin, BOM, child WO scan)
  4. Queue health            - short/default queue depths + failed jobs
                               (readiness refresh + inter-dept transfers run
                               on the short queue)
  5. Readiness snapshot      - open Job Card workload per Work Order (what a
                               refresh has to evaluate)
  6. Consistency spot-check  - sample open Job Cards: stored custom_* status
                               fields vs a fresh read-only evaluation
  7. Workstation routing     - capacity-planning setting, recent Job Cards
                               that still carry scheduled time logs, BOM
                               Operations with no Workstation Type, types with
                               no usable workstation, and machines above
                               production_capacity (read-only)

Usage:
    bench --site <site> execute tekson_manufacturing.scripts.diagnose_mes_performance.run
    bench --site <site> execute tekson_manufacturing.scripts.diagnose_mes_performance.run --args '[{"consistency_sample": 20}]'
"""

import frappe

SEP = "=" * 80

RETIRED_SERVER_SCRIPTS = [
    "job_card_status_update",
    "allocate_workstation_without_round_robin_flow",
    "job_card_material_availability",
    "stock_entry_wip_on_work_order_complete",
    "job_card_material_availability_check",
    "jc_start_control_validation_with_previous_job_card_check",
]

MES_DOCTYPES = ("Job Card", "Work Order", "Stock Entry")

# (table, columns) backing the hot-path queries. Candidates only.
INDEX_CANDIDATES = [
    ("tabJob Card", ["work_order"]),
    ("tabJob Card", ["work_order", "sequence_id"]),
    ("tabJob Card", ["work_order", "status"]),
    ("tabJob Card", ["workstation", "docstatus"]),
    ("tabJob Card", ["wip_warehouse"]),
    ("tabWork Order", ["production_item", "docstatus"]),
    ("tabWork Order", ["production_plan"]),
    ("tabStock Entry", ["work_order"]),
    ("tabStock Entry", ["purpose", "docstatus"]),
    ("tabStock Entry Detail", ["item_code"]),
    ("tabStock Entry Detail", ["item_code", "t_warehouse"]),
    ("tabBin", ["item_code", "warehouse"]),
    ("tabBOM", ["item", "is_active", "is_default"]),
    ("tabBOM Item", ["parent"]),
    ("tabBOM Item", ["item_code"]),
    ("tabStock Ledger Entry", ["item_code", "warehouse"]),
]


def _fmt_row(row):
    return " | ".join(f"{k}: {v}" for k, v in dict(row).items())


def _server_script_fields():
    """Server Script field names differ across Frappe versions."""
    meta = frappe.get_meta("Server Script")
    if meta.has_field("reference_doctype"):
        doctype_field = "reference_doctype"
    else:  # older Frappe
        doctype_field = "doc_type"
    if meta.has_field("doctype_event"):
        event_field = "doctype_event"
    else:  # older Frappe
        event_field = "event"
    return doctype_field, event_field


def section_retired_server_scripts():
    """Section 1: retired scripts disabled? any MES Server Script still enabled?"""
    lines = []
    still_enabled = []
    doctype_field, event_field = _server_script_fields()

    for script_name in RETIRED_SERVER_SCRIPTS:
        row = frappe.db.get_value(
            "Server Script",
            script_name,
            ["name", "disabled", doctype_field, event_field],
            as_dict=True,
        )
        if not row:
            lines.append(f"  OK   {script_name}: not present")
        elif row.disabled:
            lines.append(
                f"  OK   {script_name}: disabled "
                f"({doctype_field}={row.get(doctype_field)})"
            )
        else:
            lines.append(
                f"  FAIL {script_name}: STILL ENABLED "
                f"({doctype_field}={row.get(doctype_field)}, "
                f"{event_field}={row.get(event_field)})"
            )
            still_enabled.append(script_name)

    generic = frappe.get_all(
        "Server Script",
        filters={"disabled": 0, doctype_field: ("in", list(MES_DOCTYPES))},
        fields=["name", doctype_field, event_field],
    )
    for script in generic:
        lines.append(f"  FAIL enabled MES Server Script: {_fmt_row(script)}")
        if script.name not in still_enabled:
            still_enabled.append(script.name)

    if not generic and not still_enabled:
        lines.append("  No enabled Server Scripts touch MES doctypes.")

    return {"ok": not still_enabled, "still_enabled": still_enabled, "lines": lines}


def section_error_log_volume(days=7):
    """Section 2: how many Error Log docs MES logging was creating."""
    # Error Log stores the title in "method" on current Frappe; older versions
    # had a "title" column.
    if frappe.get_meta("Error Log").has_field("title"):
        title_field = "title"
    else:
        title_field = "method"
    rows = frappe.db.sql(
        f"""
        SELECT `{title_field}` AS title,
               COUNT(*) AS cnt,
               SUM(creation >= DATE_SUB(NOW(), INTERVAL 1 DAY)) AS cnt_24h,
               MAX(creation) AS latest
        FROM `tabError Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
          AND (`{title_field}` LIKE 'MES%%' OR `{title_field}` LIKE 'Security Event%%')
        GROUP BY `{title_field}`
        ORDER BY cnt DESC
        LIMIT 25
        """,
        (days,),
        as_dict=True,
    )
    total = sum(row.cnt for row in rows)
    total_24h = int(sum(row.cnt_24h or 0 for row in rows))
    # A large historical count is expected on a site that ran pre-v15.1.32
    # code; what matters is whether MES logging is still inserting rows now.
    lines = [
        f"  MES/Security Error Logs last {days} days: {total}",
        f"  MES/Security Error Logs last 24 hours: {total_24h}",
    ]
    for row in rows[:25]:
        lines.append(
            f"  {row.cnt:>6}  {row.title}  "
            f"(24h: {int(row.cnt_24h or 0)}, latest: {row.latest})"
        )
    if total == 0:
        lines.append("  OK   no MES/Security Error Logs — Phase 5 cleanup in effect")
    elif total_24h == 0:
        lines.append(
            "  OK   no new MES/Security Error Logs in the last 24 hours "
            "(the backlog above is historical)"
        )
    return {"total": total, "total_24h": total_24h, "lines": lines}


def _table_indexes(table):
    return frappe.db.sql(f"SHOW INDEX FROM `{table}`", as_dict=True)


def section_index_candidates():
    """Section 3: do the hot-path indexes exist? (report only, never create)"""
    lines = []
    missing = []
    table_cache = {}

    for table, columns in INDEX_CANDIDATES:
        if table not in table_cache:
            if not frappe.db.table_exists(table.replace("tab", "", 1)):
                table_cache[table] = None
            else:
                table_cache[table] = _table_indexes(table)
        indexes = table_cache[table]
        if indexes is None:
            lines.append(f"  SKIP {table} (table missing)")
            continue

        # existing composite/single indexes whose leading columns match candidates
        by_name = {}
        for row in indexes:
            by_name.setdefault(row.Key_name, []).append((row.Seq_in_index, row.Column_name))

        matched = False
        for name, cols in by_name.items():
            ordered = [c for _, c in sorted(cols)]
            if ordered[: len(columns)] == columns:
                lines.append(f"  OK   {table} ({', '.join(columns)}) -> index {name}")
                matched = True
                break
        if not matched:
            lines.append(f"  MISS {table} ({', '.join(columns)}) — candidate index not found")
            missing.append(f"{table}({', '.join(columns)})")

    lines.append("  (candidates only — create via migration/DBA after review)")
    return {"missing": missing, "lines": lines}


def section_queue_health():
    """Section 4: short/default queue depths and failed jobs."""
    from frappe.utils.background_jobs import get_queue, get_queue_list

    lines = []
    stats = {}
    for qname in get_queue_list(["short", "default"]):
        queue = get_queue(qname)
        queued = queue.count
        started = len(queue.started_job_registry.get_job_ids())
        failed_ids = queue.failed_job_registry.get_job_ids()
        failed = len(failed_ids)
        mes_failed = [jid for jid in failed_ids if "mes-" in (jid or "")]
        stats[qname] = {"queued": queued, "started": started, "failed": failed}
        flag = "OK  " if failed == 0 else "WARN"
        lines.append(
            f"  {flag} {qname}: queued={queued} started={started} failed={failed}"
            + (f" (MES jobs: {mes_failed[:10]})" if mes_failed else "")
        )
        if mes_failed:
            lines.append("        inspect with: bench --site <site> view-all-jobs --queue failed")
    return {"stats": stats, "lines": lines}


def section_readiness_snapshot():
    """Section 5: open JC workload — what one WO refresh has to evaluate."""
    by_status = frappe.get_all(
        "Job Card",
        filters={"docstatus": ["!=", 2]},
        fields=["status", "COUNT(*) AS cnt"],
        group_by="status",
    )
    lines = ["  Job Cards by status (docstatus != 2):"]
    for row in by_status:
        lines.append(f"    {row.status or 'Unspecified':<20} {row.cnt}")

    top_wos = frappe.get_all(
        "Job Card",
        filters={"docstatus": ["!=", 2], "work_order": ["is", "set"]},
        fields=["work_order", "COUNT(*) AS cnt"],
        group_by="work_order",
        order_by="cnt desc",
        limit=10,
    )
    lines.append("  Top Work Orders by open Job Card count (refresh cost):")
    for row in top_wos:
        lines.append(f"    {row.work_order}: {row.cnt} Job Cards")
    return {"by_status": by_status, "top_wos": top_wos, "lines": lines}


def section_consistency_spot_check(sample=10):
    """Section 6: stored custom_* fields vs fresh read-only evaluation."""
    from tekson_manufacturing.services.job_card_service import JobCardService

    jc_names = frappe.get_all(
        "Job Card",
        filters={"docstatus": ["!=", 2], "status": ["not in", ("Completed", "Work In Progress")]},
        fields=["name"],
        order_by="modified desc",
        limit=sample,
    )

    lines = []
    mismatches = []
    service = JobCardService()
    for row in jc_names:
        jc = frappe.get_doc("Job Card", row.name)
        computed = service.evaluate_status_fields(jc)
        for fieldname, expected in computed.items():
            stored = jc.get(fieldname)
            if stored != expected:
                mismatches.append(
                    {"job_card": jc.name, "field": fieldname, "stored": stored, "computed": expected}
                )

    if mismatches:
        lines.append(f"  WARN {len(mismatches)} field mismatch(es) in sample of {len(jc_names)}:")
        for mismatch in mismatches[:20]:
            lines.append(
                f"    {mismatch['job_card']} {mismatch['field']}: "
                f"stored={mismatch['stored']!r} computed={mismatch['computed']!r}"
            )
    else:
        lines.append(f"  OK   stored fields match evaluation for {len(jc_names)} sampled Job Cards")
    return {"mismatches": mismatches, "lines": lines}


def section_workstation_routing(scheduled_log_days=30, assignment_hours=24):
    """Section 7: is the BOM -> Workstation Type -> eligible machine chain intact?"""
    lines = []

    disable_planning = frappe.db.get_single_value(
        "Manufacturing Settings", "disable_capacity_planning"
    )
    if disable_planning:
        lines.append(
            "  OK   Capacity planning disabled — Job Card rotation is authoritative"
        )
    else:
        lines.append(
            "  WARN Capacity planning is enabled. ERPNext picks the first workstation "
            "while scheduling,\n"
            "       before the Job Card before_insert hook runs, and that pick is "
            "respected.\n"
            "       LRU rotation is therefore skipped for Job Cards created from a "
            "Work Order."
        )

    # The setting alone is not proof: check whether scheduling actually ran on
    # recent Job Cards created through Work Order submission.
    scheduled = frappe.db.sql(
        """
        SELECT jc.name, MAX(jc.creation) AS created
        FROM `tabJob Card Scheduled Time` st
        JOIN `tabJob Card` jc ON jc.name = st.parent
        WHERE jc.creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY jc.name
        ORDER BY created DESC
        LIMIT 5
        """,
        (scheduled_log_days,),
        as_dict=True,
    )
    if scheduled:
        names = ", ".join(row.name for row in scheduled)
        lines.append(
            f"  WARN Job Cards created in the last {scheduled_log_days} days carry "
            f"scheduled time logs (capacity planning ran): {names}"
        )
    else:
        lines.append(
            f"  OK   no Job Card from the last {scheduled_log_days} days carries "
            f"scheduled time logs"
        )

    missing_type = frappe.db.sql(
        """
        SELECT bo.operation, bo.workstation, COUNT(*) AS operations
        FROM `tabBOM Operation` bo
        JOIN `tabBOM` b ON b.name = bo.parent AND b.docstatus < 2
        WHERE IFNULL(bo.workstation_type, '') = ''
        GROUP BY bo.operation, bo.workstation
        ORDER BY operations DESC
        """,
        as_dict=True,
    )
    if missing_type:
        lines.append("  WARN BOM Operations without a Workstation Type:")
        for row in missing_type[:20]:
            suffix = f" (workstation={row.workstation})" if row.workstation else ""
            lines.append(f"    {row.operation}{suffix}: {row.operations} BOM line(s)")
    else:
        lines.append("  OK   every active BOM Operation has a Workstation Type")

    blocked_types = frappe.db.sql(
        """
        SELECT workstation_type,
               COUNT(*) AS total,
               SUM(CASE WHEN status IN ('Maintenance', 'Problem') THEN 1 ELSE 0 END) AS blocked
        FROM `tabWorkstation`
        WHERE IFNULL(workstation_type, '') != ''
        GROUP BY workstation_type
        """,
        as_dict=True,
    )
    unusable = [row for row in blocked_types if (row.total or 0) <= (row.blocked or 0)]
    if unusable:
        lines.append("  FAIL Workstation Types with no usable workstation:")
        for row in unusable:
            lines.append(
                f"    {row.workstation_type}: {row.total} workstation(s), "
                f"{row.blocked} blocked"
            )
    else:
        lines.append("  OK   every Workstation Type has at least one usable workstation")

    # Types with 2+ eligible machines are where rotation can be observed; a
    # single-machine type can never rotate.
    rotation_ready = frappe.db.sql(
        """
        SELECT workstation_type,
               COUNT(*) AS usable,
               GROUP_CONCAT(name ORDER BY name SEPARATOR ', ') AS machines
        FROM `tabWorkstation`
        WHERE IFNULL(workstation_type, '') != ''
          AND status NOT IN ('Maintenance', 'Problem')
        GROUP BY workstation_type
        HAVING usable > 1
        ORDER BY usable DESC, workstation_type
        """,
        as_dict=True,
    )
    if rotation_ready:
        lines.append("  INFO Workstation Types that can rotate (2+ eligible machines):")
        for row in rotation_ready[:20]:
            lines.append(
                f"    {row.workstation_type}: {int(row.usable)} — {row.machines}"
            )
    else:
        lines.append(
            "  NOTE no Workstation Type has more than one eligible machine — "
            "rotation cannot be observed until a sibling is added"
        )

    # Did recent Job Cards actually rotate? Group the assignments by type so a
    # single-machine result is visible immediately, without opening each card.
    assignments = frappe.db.sql(
        """
        SELECT IFNULL(NULLIF(jc.workstation_type, ''), ws.workstation_type)
                   AS workstation_type,
               jc.workstation,
               COUNT(*) AS cnt
        FROM `tabJob Card` jc
        LEFT JOIN `tabWorkstation` ws ON ws.name = jc.workstation
        WHERE jc.docstatus < 2
          AND jc.creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)
          AND IFNULL(jc.workstation, '') != ''
        GROUP BY workstation_type, jc.workstation
        ORDER BY workstation_type, cnt DESC, jc.workstation
        """,
        (assignment_hours,),
        as_dict=True,
    )
    by_type = {}
    for row in assignments:
        by_type.setdefault(row.workstation_type or "(no type)", []).append(row)

    if by_type:
        eligible_counts = {
            row.workstation_type: int(row.usable) for row in rotation_ready
        }
        lines.append(
            f"  INFO Workstation assignments for Job Cards created in the last "
            f"{assignment_hours}h:"
        )
        for ws_type, rows in list(by_type.items())[:15]:
            total = sum(int(row.cnt) for row in rows)
            machine_count = len(rows)
            detail = ", ".join(
                f"{row.workstation}({int(row.cnt)})" for row in rows[:10]
            )
            if len(rows) > 10:
                detail += f" (+{len(rows) - 10} more)"
            if total > 1 and machine_count == 1 and eligible_counts.get(ws_type, 0) > 1:
                lines.append(
                    f"  WARN {ws_type}: {total} Job Cards on one machine — {detail} "
                    f"(rotation was not applied)"
                )
            else:
                lines.append(
                    f"    {ws_type}: {total} Job Card(s) on {machine_count} "
                    f"machine(s) — {detail}"
                )
    else:
        lines.append(
            f"  NOTE no Job Card with a workstation was created in the last "
            f"{assignment_hours}h — rotation cannot be verified yet"
        )

    floor_split = frappe.db.sql(
        """
        SELECT workstation_type,
               COUNT(DISTINCT IFNULL(plant_floor, '')) AS floors
        FROM `tabWorkstation`
        WHERE IFNULL(workstation_type, '') != ''
        GROUP BY workstation_type
        HAVING floors > 1
        """,
        as_dict=True,
    )
    for row in floor_split:
        lines.append(
            f"  NOTE {row.workstation_type}: workstations span {row.floors} plant "
            f"floors; rotation can move a Job Card between WIP warehouses"
        )

    # Allocation never blocks Job Card creation, so report any machine that
    # ended up with more concurrent cards than its configured capacity.
    from tekson_manufacturing.utils.job_card_utils import workstation_workload

    workstations = frappe.get_all(
        "Workstation",
        fields=["name", "workstation_type", "production_capacity"],
    )
    workload = workstation_workload([ws.name for ws in workstations])
    overflow = []
    for ws in workstations:
        capacity = ws.production_capacity or 1
        active_load = workload[ws.name]["active_load"]
        if active_load > capacity:
            overflow.append(
                {
                    "workstation": ws.name,
                    "type": ws.workstation_type,
                    "active_load": active_load,
                    "capacity": capacity,
                    "queued": workload[ws.name]["open_load"] - active_load,
                }
            )

    if overflow:
        lines.append("  WARN workstations above production_capacity (concurrent Job Cards):")
        for row in overflow[:20]:
            lines.append(
                f"    {row['workstation']} ({row['type']}): "
                f"{row['active_load']} active / {row['capacity']} capacity, "
                f"{row['queued']} queued"
            )
    else:
        lines.append("  OK   no workstation is above its production_capacity")

    return {
        "capacity_planning_disabled": bool(disable_planning),
        "missing_type": missing_type,
        "unusable_types": unusable,
        "capacity_overflow": overflow,
        "lines": lines,
    }


def run(options=None):
    """
    Run all diagnostics and print a report.

    Args:
        options: dict, e.g. {"consistency_sample": 20, "scheduled_log_days": 30,
                 "assignment_hours": 24} (defaults: 10, 30, 24)
    """
    options = options or {}
    sample = int(options.get("consistency_sample", 10))

    report = {}
    sections = [
        ("Retired server scripts", section_retired_server_scripts),
        ("Error Log volume", lambda: section_error_log_volume(options.get("error_log_days", 7))),
        ("Index candidates", section_index_candidates),
        ("Queue health", section_queue_health),
        ("Readiness snapshot", section_readiness_snapshot),
        ("Consistency spot-check", lambda: section_consistency_spot_check(sample)),
        ("Workstation routing", lambda: section_workstation_routing(
            options.get("scheduled_log_days", 30),
            options.get("assignment_hours", 24),
        )),
    ]

    for title, fn in sections:
        print(SEP)
        print(title)
        print(SEP)
        try:
            result = fn()
        except Exception as exc:
            print(f"  ERROR running section: {exc}")
            frappe.logger("tekson").exception("diagnostics section failed: %s", title)
            report[title] = {"error": str(exc)}
            continue
        for line in result.pop("lines", []):
            print(line)
        report[title] = result

    print(SEP)
    ok_scripts = report.get("Retired server scripts", {}).get("ok", False)
    print(f"Summary: retired scripts clean={ok_scripts}")
    print("Read-only diagnostics complete — no changes were made.")
    return report
