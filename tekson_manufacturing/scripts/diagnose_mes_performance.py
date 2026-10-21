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


def section_retired_server_scripts():
    """Section 1: retired scripts disabled? any MES Server Script still enabled?"""
    lines = []
    still_enabled = []

    for script_name in RETIRED_SERVER_SCRIPTS:
        row = frappe.db.get_value(
            "Server Script",
            script_name,
            ["name", "disabled", "doc_type", "event"],
            as_dict=True,
        )
        if not row:
            lines.append(f"  OK   {script_name}: not present")
        elif row.disabled:
            lines.append(f"  OK   {script_name}: disabled (doc_type={row.doc_type})")
        else:
            lines.append(f"  FAIL {script_name}: STILL ENABLED (doc_type={row.doc_type}, event={row.event})")
            still_enabled.append(script_name)

    generic = frappe.get_all(
        "Server Script",
        filters={"disabled": 0, "doc_type": ("in", list(MES_DOCTYPES))},
        fields=["name", "doc_type", "event"],
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
    rows = frappe.db.sql(
        """
        SELECT title, COUNT(*) AS cnt
        FROM `tabError Log`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
          AND (title LIKE 'MES%%' OR title LIKE 'Security Event%%')
        GROUP BY title
        ORDER BY cnt DESC
        LIMIT 25
        """,
        (days,),
        as_dict=True,
    )
    total = sum(row.cnt for row in rows)
    lines = [f"  MES/Security Error Logs last {days} days: {total}"]
    for row in rows[:25]:
        lines.append(f"  {row.cnt:>6}  {row.title}")
    if total == 0:
        lines.append("  OK   no MES/Security Error Logs — Phase 5 cleanup in effect")
    return {"total": total, "lines": lines}


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


def run(options=None):
    """
    Run all diagnostics and print a report.

    Args:
        options: dict, e.g. {"consistency_sample": 20} (default 10)
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
