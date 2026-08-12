# Frappe Insights Setup for Tekson Manufacturing v15.2.0

## Architecture

**Tekson Manufacturing** owns business logic and calculations.
**Frappe Insights** owns visualization, dashboards, and reporting.

## Installation

1. Install Frappe Insights on your bench:
   ```bash
   cd ~/frappe-bench
   bench get-app insights
   bench --site teksons.dev install-app insights
   ```

2. Configure Insights to connect to teksons.dev database:
   - Go to `/app/insights`
   - Add Data Source: `teksons.dev` database
   - Connection: MariaDB/MySQL
   - Database name from site_config.json

## Planner Dashboard (Frappe Insights)

### KPIs (Number Charts)
1. **Total WOs**: `COUNT(Work Order) WHERE docstatus = 1`
2. **Completed**: `COUNT WHERE status = 'Completed'`
3. **In Process**: `COUNT WHERE status NOT IN ('Completed', 'Draft')`
4. **Readiness %**: Call API `tekson_manufacturing.api.intelligence.planner_kpis.readiness_pct`
5. **On-Time %**: Calculate from completed WOs
6. **Pending PPs**: `COUNT(Production Plan) WHERE docstatus = 1 AND status = 'Submitted'`

### Production Calendar (Table Chart)
- Query: Group WOs by `planned_start_date`
- Columns: Date, WO Count, Total Qty, Items
- Filter: Next 7 days

### Department Load (Bar Chart)
- Query: Group WOs by `wip_warehouse` (extract department name)
- Metric: Count of WOs per department

### FG Product Mix (Row Chart)
- Query: Group WOs by `production_item`
- Metric: Sum of qty
- Limit: Top 10

### Exceptions (4 Number Charts)
Use API: `tekson_manufacturing.api.intelligence.planner_exceptions`
- Overdue Count
- Blocked Count
- Material Short Count
- Dependency Wait Count

### Filters (Dashboard-wide)
- Date Range
- Production Plan
- FG Item
- Department
- WO Status

---

## Stores Dashboard (Frappe Insights)

### KPIs (Number Charts)
1. **Pending MRs**: Use API `stores_kpis.pending_mrs`
2. **Pick Lists**: `COUNT(Pick List) WHERE docstatus = 1 AND status = 'Open'`
3. **WIP Transfers Today**: Use API `stores_kpis.wip_transfers`
4. **Material Short**: Use API `stores_kpis.material_short`

### Department WIP (Table)
- Query: Group WOs by `wip_warehouse`
- Show: Department, WO Count, Total Qty

### Material Health (Table)
- Query: Job Cards with `custom_material_status = 'Waiting for Material'`
- Show: WO, Operation, Item, Qty

### Transfer Status (Table)
- Query: Stock Entries (Material Transfer for Manufacture)
- Show: Date, From Warehouse, To Warehouse, Status

---

## Complex Business Logic (Python APIs)

Some metrics require Tekson's business logic. Use Python APIs:

### Production Readiness %
```python
frappe.call({
    method: 'tekson_manufacturing.api.intelligence.planner_kpis',
    args: { planned_date: '2025-08-12' }
})
```

### Exceptions with Severity
```python
frappe.call({
    method: 'tekson_manufacturing.api.intelligence.planner_exceptions',
    args: { planned_date: '2025-08-12' }
})
```

### Department Workload
```python
frappe.call({
    method: 'tekson_manufacturing.api.intelligence.planner_workload',
    args: { planned_date: '2025-08-12' }
})
```

---

## Security & Access Control

Configure Insights roles to match Tekson roles:
- **Planner**: Manufacturing User → WOs, PPs, Planning data
- **Stores**: Stock User → MRs, Stock, Transfers
- **Production**: Manufacturing Manager → All production data
- **Management**: System Manager → Everything

---

## Benefits

✅ Faster Development - No custom dashboard JS
✅ Better Charts - Professional visualizations
✅ Customer Configurable - Each customer can customize
✅ Built-in Filters - Dashboard-wide filters
✅ Drill-down - Click charts to see details
✅ Role-based Access - Insights permissions
✅ Less Maintenance - Less custom code

---

## Next Steps

1. Install Frappe Insights on VM
2. Connect to teksons.dev database
3. Build Planner Dashboard POC (6 KPIs + Calendar + Workload + Exceptions)
4. Test with real data
5. Configure roles & permissions
6. Build Stores Dashboard
7. Document for customers

---

**Reference**: https://docs.frappe.io/insights
