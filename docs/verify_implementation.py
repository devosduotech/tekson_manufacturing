"""
Quick verification script for MES implementation

Run this in Frappe console:
    bench --site teksons.dev console
    >>> exec(open('docs/verify_implementation.py').read())
"""

print("=" * 60)
print("MES IMPLEMENTATION VERIFICATION")
print("=" * 60)

# Test 1: Import dataclasses
print("\n1. Testing dataclasses import...")
try:
    from tekson_manufacturing.mes.dataclasses import (
        MaterialStatus,
        ReadinessStatus,
        MaterialResult,
        DependencyResult,
        ReadinessResult
    )
    print("   ✅ Dataclasses imported successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 2: Create MaterialResult
print("\n2. Testing MaterialResult creation...")
try:
    result = MaterialResult(
        is_ready=True,
        status=MaterialStatus.AVAILABLE,
        message="Material available",
        available_qty=100.0,
        required_qty=50.0
    )
    assert result.is_ready == True
    assert result.status == MaterialStatus.AVAILABLE
    print(f"   ✅ MaterialResult created: {result.status}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 3: Create DependencyResult
print("\n3. Testing DependencyResult creation...")
try:
    dep_result = DependencyResult(
        can_start=True,
        previous_jc_name=None,
        message="No dependencies"
    )
    assert dep_result.can_start == True
    print(f"   ✅ DependencyResult created: {dep_result.message}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 4: Create ReadinessResult
print("\n4. Testing ReadinessResult factory methods...")
try:
    ready = ReadinessResult.create_ready(MaterialStatus.AVAILABLE)
    assert ready.readiness_status == ReadinessStatus.READY
    assert ready.can_start == True
    print(f"   ✅ ReadinessResult.create_ready() works: {ready.readiness_status}")
    
    waiting = ReadinessResult.create_waiting_material("Short by 10")
    assert waiting.readiness_status == ReadinessStatus.BLOCKED
    assert waiting.can_start == False
    print(f"   ✅ ReadinessResult.create_waiting_material() works")
    
    blocked = ReadinessResult.create_waiting_previous_op("JC-10")
    assert blocked.blocked_by == "JC-10"
    print(f"   ✅ ReadinessResult.create_waiting_previous_op() works")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 5: Import Readiness Engine
print("\n5. Testing JobCardReadinessEngine import...")
try:
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    print("   ✅ JobCardReadinessEngine instantiated")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 6: Import MES Coordinator
print("\n6. Testing MESExecutionCoordinator import...")
try:
    from tekson_manufacturing.mes.mes_coordinator import MESExecutionCoordinator
    coordinator = MESExecutionCoordinator()
    print("   ✅ MESExecutionCoordinator instantiated")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 7: Verify hooks
print("\n7. Checking hooks registration...")
try:
    hooks = frappe.get_hooks('doc_events')
    
    wo_hooks = hooks.get('Work Order', {})
    if 'on_submit' in wo_hooks:
        on_submit = wo_hooks['on_submit']
        if isinstance(on_submit, list):
            has_coordinator = any('mes_coordinator' in h for h in on_submit)
        else:
            has_coordinator = 'mes_coordinator' in on_submit
        if has_coordinator:
            print("   ✅ Work Order on_submit hook registered")
        else:
            print(f"   ⚠️  Work Order on_submit exists but may not include coordinator: {on_submit}")
    else:
        print("   ⚠️  Work Order on_submit hook not found")
    
    se_hooks = hooks.get('Stock Entry', {})
    if 'on_submit' in se_hooks:
        on_submit = se_hooks['on_submit']
        if isinstance(on_submit, list):
            has_coordinator = any('mes_coordinator' in h for h in on_submit)
        else:
            has_coordinator = 'mes_coordinator' in on_submit
        if has_coordinator:
            print("   ✅ Stock Entry on_submit hook registered")
        else:
            print(f"   ⚠️  Stock Entry on_submit exists but may not include coordinator: {on_submit}")
    
    jc_hooks = hooks.get('Job Card', {})
    if 'on_submit' in jc_hooks:
        on_submit = jc_hooks['on_submit']
        if isinstance(on_submit, list):
            has_coordinator = any('mes_coordinator' in h for h in on_submit)
        else:
            has_coordinator = 'mes_coordinator' in on_submit
        if has_coordinator:
            print("   ✅ Job Card on_submit hook registered")
        else:
            print(f"   ⚠️  Job Card on_submit exists but may not include coordinator: {on_submit}")
    
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Create a test Work Order")
print("2. Submit it → Verify all Job Cards evaluated")
print("3. Create Material Transfer → Verify status updates")
print("4. Complete Operation 1 → Verify Operation 2 refreshed")
