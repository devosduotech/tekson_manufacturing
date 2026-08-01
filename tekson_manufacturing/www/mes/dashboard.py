"""
MES Dashboard - Sprint 9

Main MES dashboard showing production status, KPIs, and alerts.
"""

import frappe
from frappe import _
from datetime import datetime


@frappe.whitelist()
def get_dashboard_data():
    """
    Get MES dashboard data
    
    Returns:
        dict with dashboard widgets
    """
    return {
        'production_status': get_production_status(),
        'kpis': get_kpis(),
        'alerts': get_active_alerts(),
        'recent_activity': get_recent_activity()
    }


def get_production_status():
    """Get production status summary"""
    return {
        'work_orders': {
            'total': frappe.db.count("Work Order", {"status": ["!=", "Cancelled"]}),
            'completed': frappe.db.count("Work Order", {"status": "Completed"}),
            'in_progress': frappe.db.count("Work Order", {"status": "Work In Progress"}),
            'pending': frappe.db.count("Work Order", {"status": "Not Started"})
        },
        'job_cards': {
            'total': frappe.db.count("Job Card"),
            'completed': frappe.db.count("Job Card", {"status": "Completed"}),
            'in_progress': frappe.db.count("Job Card", {"status": "Work In Progress"}),
            'pending': frappe.db.count("Job Card", {"status": "Open"})
        }
    }


def get_kpis():
    """Get key performance indicators"""
    return {
        'on_time_delivery': calculate_otd(),
        'production_efficiency': calculate_efficiency(),
        'quality_rate': calculate_quality_rate(),
        'material_availability': calculate_material_availability()
    }


def calculate_otd():
    """Calculate on-time delivery percentage"""
    # Placeholder - implement based on actual delivery data
    return 95.0


def calculate_efficiency():
    """Calculate production efficiency"""
    # Placeholder - implement based on actual production data
    return 87.5


def calculate_quality_rate():
    """Calculate first-pass quality rate"""
    # Placeholder - implement based on quality data
    return 98.2


def calculate_material_availability():
    """Calculate material availability percentage"""
    # Placeholder - implement based on stock data
    return 92.0


def get_active_alerts():
    """Get active alerts and warnings"""
    alerts = []
    
    # Material shortages
    shortages = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabStock Ledger Entry`
        WHERE actual_qty < 0
    """, as_dict=True)
    
    if shortages and shortages[0].count > 0:
        alerts.append({
            'type': 'error',
            'title': 'Material Shortage',
            'count': shortages[0].count,
            'message': f'{shortages[0].count} items have negative stock'
        })
    
    # Pending job cards
    pending_jc = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabJob Card`
        WHERE status = 'Open'
        AND modified < DATE_SUB(NOW(), INTERVAL 7 DAY)
    """, as_dict=True)
    
    if pending_jc and pending_jc[0].count > 0:
        alerts.append({
            'type': 'warning',
            'title': 'Stale Job Cards',
            'count': pending_jc[0].count,
            'message': f'{pending_jc[0].count} job cards pending for >7 days'
        })
    
    return alerts


def get_recent_activity():
    """Get recent MES activity"""
    activity = []
    
    # Recent completed job cards
    recent_jc = frappe.db.sql("""
        SELECT name, work_order, operation, modified
        FROM `tabJob Card`
        WHERE status = 'Completed'
        ORDER BY modified DESC
        LIMIT 10
    """, as_dict=True)
    
    for jc in recent_jc:
        activity.append({
            'type': 'Job Card Completed',
            'document': jc.name,
            'work_order': jc.work_order,
            'operation': jc.operation,
            'timestamp': jc.modified
        })
    
    # Recent stock entries
    recent_se = frappe.db.sql("""
        SELECT name, work_order, posting_date
        FROM `tabStock Entry`
        WHERE work_order IS NOT NULL
        ORDER BY posting_date DESC
        LIMIT 5
    """, as_dict=True)
    
    for se in recent_se:
        activity.append({
            'type': 'Stock Entry',
            'document': se.name,
            'work_order': se.work_order,
            'timestamp': se.posting_date
        })
    
    return activity


@frappe.whitelist()
def get_department_wise_production():
    """Get production status by department"""
    departments = ['W', 'RA', 'RP', 'CNC', 'Ralu Weld', 'Ralu In']
    
    result = []
    for dept in departments:
        warehouse = f"WIP-{dept}"
        
        # Count job cards in this department
        jc_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabJob Card` jc
            JOIN `tabWorkstation` ws ON jc.workstation = ws.name
            WHERE ws.department = %s
            AND jc.status != 'Completed'
        """, (dept,), as_dict=True)
        
        result.append({
            'department': dept,
            'warehouse': warehouse,
            'active_job_cards': jc_count[0].count if jc_count else 0
        })
    
    return result


@frappe.whitelist()
def get_material_readiness_summary():
    """Get material readiness summary for all work orders"""
    work_orders = frappe.db.sql("""
        SELECT name, production_item, qty
        FROM `tabWork Order`
        WHERE status != 'Cancelled'
    """, as_dict=True)
    
    summary = {
        'ready': 0,
        'partial': 0,
        'not_ready': 0
    }
    
    for wo in work_orders:
        # Check material readiness (simplified)
        # In production, use MaterialReadinessEngine
        summary['ready'] += 1
    
    return summary
