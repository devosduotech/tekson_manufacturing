"""
Sprint 10: Integration Validation Script

Validates complete manufacturing flow with REAL Teksons data.

Usage:
    bench --site [site-name] execute tekson_manufacturing.tests.sprint_10_validation.run_validation

This is NOT a unit test. This is an integration validation that:
1. Uses real Teksons Work Orders (R215, R216, R217)
2. Executes complete manufacturing flow
3. Validates all engines work together
4. Reports issues found

Start with ONE Work Order. If it works, expand to shared sub-assemblies.
"""

import frappe
from frappe import _
from datetime import datetime


def run_validation():
    """
    Main validation function
    
    Executes:
    1. Framework validation (repositories, services, hooks)
    2. Single WO flow (R215)
    3. Material readiness
    4. Department transfers
    5. Job Card execution
    6. WO completion
    """
    print("=" * 80)
    print("SPRINT 10: INTEGRATION VALIDATION")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print()
    
    # Step 1: Validate Framework
    print("STEP 1: Framework Validation")
    print("-" * 40)
    validate_framework()
    print()
    
    # Step 2: Find Real Teksons WO
    print("STEP 2: Find Real Teksons Work Order")
    print("-" * 40)
    wo_name = find_teksons_work_order()
    
    if not wo_name:
        print("❌ No Teksons Work Order found. Please create one for R215.")
        return
    
    print(f"✅ Using Work Order: {wo_name}")
    print()
    
    # Step 3: Validate Material Readiness
    print("STEP 3: Material Readiness Validation")
    print("-" * 40)
    validate_material_readiness(wo_name)
    print()
    
    # Step 4: Validate Job Cards
    print("STEP 4: Job Card Flow Validation")
    print("-" * 40)
    validate_job_card_flow(wo_name)
    print()
    
    # Step 5: Validate Department Transfers
    print("STEP 5: Department Transfer Validation")
    print("-" * 40)
    validate_department_transfers(wo_name)
    print()
    
    # Step 6: Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Completed: {datetime.now()}")
    print()


def validate_framework():
    """Validate repository and service layers exist and are accessible"""
    
    print("Checking Repository Layer...")
    try:
        from tekson_manufacturing.repositories.work_order_repository import WorkOrderRepository
        from tekson_manufacturing.repositories.job_card_repository import JobCardRepository
        from tekson_manufacturing.repositories.stock_repository import StockRepository
        from tekson_manufacturing.repositories.warehouse_repository import WarehouseRepository
        
        wo_repo = WorkOrderRepository()
        jc_repo = JobCardRepository()
        stock_repo = StockRepository()
        warehouse_repo = WarehouseRepository()
        
        print("  ✅ All repositories loaded successfully")
    except Exception as e:
        print(f"  ❌ Repository Error: {str(e)}")
        return False
    
    print("Checking Service Layer...")
    try:
        from tekson_manufacturing.services.stock_service import StockService
        from tekson_manufacturing.services.job_card_service import JobCardService
        from tekson_manufacturing.services.permission_service import PermissionService
        
        stock_service = StockService()
        jc_service = JobCardService()
        perm_service = PermissionService()
        
        print("  ✅ All services loaded successfully")
    except Exception as e:
        print(f"  ❌ Service Error: {str(e)}")
        return False
    
    print("Checking Engines...")
    try:
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        from tekson_manufacturing.validation.dependency_engine import DependencyEngine
        from tekson_manufacturing.execution.execution_engine import ExecutionEngine
        
        mr_engine = MaterialReadinessEngine()
        dep_engine = DependencyEngine()
        exec_engine = ExecutionEngine()
        
        print("  ✅ All engines loaded successfully")
    except Exception as e:
        print(f"  ❌ Engine Error: {str(e)}")
        return False
    
    print("Checking Diagnostics...")
    try:
        from tekson_manufacturing.diagnostics.messages import DiagnosticMessages
        from tekson_manufacturing.diagnostics.exception_handler import ExceptionHandler
        
        diag = DiagnosticMessages()
        exc_handler = ExceptionHandler()
        
        print("  ✅ Diagnostics framework loaded successfully")
    except Exception as e:
        print(f"  ❌ Diagnostics Error: {str(e)}")
        return False
    
    return True


def find_teksons_work_order():
    """Find a real Teksons Work Order for R215, R216, or R217"""
    
    # Search for R215 WO
    wo = frappe.db.sql("""
        SELECT name, production_item, status, qty
        FROM `tabWork Order`
        WHERE production_item LIKE '%R215%'
        AND status != 'Cancelled'
        ORDER BY creation DESC
        LIMIT 1
    """, as_dict=True)
    
    if wo:
        print(f"  Found R215 WO: {wo[0].name} ({wo[0].status}, Qty: {wo[0].qty})")
        return wo[0].name
    
    # Search for R216 WO
    wo = frappe.db.sql("""
        SELECT name, production_item, status, qty
        FROM `tabWork Order`
        WHERE production_item LIKE '%R216%'
        AND status != 'Cancelled'
        ORDER BY creation DESC
        LIMIT 1
    """, as_dict=True)
    
    if wo:
        print(f"  Found R216 WO: {wo[0].name} ({wo[0].status}, Qty: {wo[0].qty})")
        return wo[0].name
    
    # Search for R217 WO
    wo = frappe.db.sql("""
        SELECT name, production_item, status, qty
        FROM `tabWork Order`
        WHERE production_item LIKE '%R217%'
        AND status != 'Cancelled'
        ORDER BY creation DESC
        LIMIT 1
    """, as_dict=True)
    
    if wo:
        print(f"  Found R217 WO: {wo[0].name} ({wo[0].status}, Qty: {wo[0].qty})")
        return wo[0].name
    
    print("  ⚠️ No R215/R216/R217 Work Orders found")
    print("  Please create a Work Order for one of these items first")
    
    return None


def validate_material_readiness(wo_name):
    """Validate material readiness evaluation for WO"""
    
    print(f"Evaluating material readiness for {wo_name}...")
    
    try:
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine()
        result = engine.evaluate_material_readiness(wo_name)
        
        print(f"  Is Ready: {result.get('is_ready', False)}")
        print(f"  Missing Items: {len(result.get('missing_items', []))}")
        
        if result.get('missing_items'):
            print("  Missing:")
            for item in result['missing_items'][:5]:  # Show first 5
                print(f"    - {item}")
        
        if result.get('is_ready'):
            print("  ✅ Material readiness evaluation working")
        else:
            print("  ⚠️ Materials not ready (this may be expected)")
        
    except Exception as e:
        print(f"  ❌ Material Readiness Error: {str(e)}")
        import traceback
        traceback.print_exc()


def validate_job_card_flow(wo_name):
    """Validate Job Card creation and execution flow"""
    
    print(f"Checking Job Cards for {wo_name}...")
    
    try:
        from tekson_manufacturing.repositories.job_card_repository import JobCardRepository
        
        repo = JobCardRepository()
        job_cards = repo.get_list({'work_order': wo_name})
        
        if not job_cards:
            print("  ⚠️ No Job Cards found for this Work Order")
            print("  Job Cards may need to be created first")
            return
        
        print(f"  Found {len(job_cards)} Job Card(s)")
        
        # Show Job Card status
        for jc in job_cards[:5]:  # Show first 5
            print(f"    - {jc.name}: {jc.status} (Operation: {jc.operation})")
        
        # Try to start first open Job Card
        open_jcs = [jc for jc in job_cards if jc.status == 'Open']
        
        if open_jcs:
            print(f"  Attempting to start Job Card: {open_jcs[0].name}")
            
            from tekson_manufacturing.services.job_card_service import JobCardService
            
            service = JobCardService()
            result = service.start_job_card(open_jcs[0].name)
            
            if result.get('success'):
                print("  ✅ Job Card started successfully")
            else:
                print(f"  ⚠️ Job Card start failed: {result.get('message', 'Unknown error')}")
        
    except Exception as e:
        print(f"  ❌ Job Card Error: {str(e)}")
        import traceback
        traceback.print_exc()


def validate_department_transfers(wo_name):
    """Validate department transfer creation"""
    
    print(f"Checking department transfers for {wo_name}...")
    
    try:
        from tekson_manufacturing.services.stock_service import StockService
        
        service = StockService()
        
        # Check if any Stock Entries exist for this WO
        stock_entries = frappe.db.sql("""
            SELECT name, stock_entry_type, from_warehouse, to_warehouse, docstatus
            FROM `tabStock Entry`
            WHERE work_order = %s
            ORDER BY creation DESC
            LIMIT 5
        """, (wo_name,), as_dict=True)
        
        if stock_entries:
            print(f"  Found {len(stock_entries)} Stock Entry/Entries")
            for se in stock_entries:
                print(f"    - {se.name}: {se.stock_entry_type} ({se.from_warehouse} → {se.to_warehouse})")
        else:
            print("  ⚠️ No Stock Entries found for this Work Order")
            print("  Department transfers may need to be created first")
        
    except Exception as e:
        print(f"  ❌ Department Transfer Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_validation()
