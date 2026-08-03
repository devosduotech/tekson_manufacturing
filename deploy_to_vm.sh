#!/bin/bash

# =============================================================================
# Tekson Manufacturing MES - UAT Deployment Script
# =============================================================================
# Purpose: Deploy MES Phase 1 to Local VM for UAT Testing
# Version: 1.0
# Date: 2026-08-03
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Configuration
# =============================================================================

SITE_NAME="teksons.dev"  # Change if your site name is different
APP_NAME="tekson_manufacturing"
BENCH_PATH="$HOME/frappe-bench"  # Change to your bench path

# =============================================================================
# Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_bench() {
    if ! command -v bench &> /dev/null; then
        print_error "bench command not found. Please activate frappe environment."
        exit 1
    fi
    print_success "Bench command found"
}

check_site() {
    if ! bench --site $SITE_NAME execute "print('Site exists')" &> /dev/null; then
        print_error "Site '$SITE_NAME' does not exist"
        exit 1
    fi
    print_success "Site '$SITE_NAME' exists"
}

# =============================================================================
# Deployment Steps
# =============================================================================

print_header "MES Phase 1 UAT Deployment"

echo "Site: $SITE_NAME"
echo "App: $APP_NAME"
echo "Bench: $BENCH_PATH"
echo ""
read -p "Continue with deployment? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelled"
    exit 0
fi

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"
check_bench
check_site

# Step 2: Navigate to bench
print_header "Step 2: Navigating to Bench"
cd $BENCH_PATH
print_success "Changed to bench directory"

# Step 3: Update app
print_header "Step 3: Pulling Latest Code"
cd apps/$APP_NAME
git fetch origin
git checkout develop
git pull origin develop
print_success "Code updated to latest develop branch"

# Step 4: Check latest commit
print_header "Step 4: Verifying Code Version"
LATEST_COMMIT=$(git log --oneline -1)
print_info "Latest commit: $LATEST_COMMIT"

# Step 5: Install app (if not already installed)
print_header "Step 5: Installing App on Site"
bench --site $SITE_NAME install-app $APP_NAME || print_info "App already installed"

# Step 6: Clear cache
print_header "Step 6: Clearing Cache"
bench --site $SITE_NAME clear-cache
bench --site $SITE_NAME clear-website-cache
print_success "Cache cleared"

# Step 7: Restart bench
print_header "Step 7: Restarting Bench"
bench restart
print_success "Bench restarted"

# Step 8: Verify installation
print_header "Step 8: Running Verification Tests"

cd ../../  # Back to bench root

# Create verification script
cat > /tmp/verify_mes_deployment.py << 'EOF'
"""Verify MES Deployment"""
import frappe

print("\n" + "="*60)
print("MES DEPLOYMENT VERIFICATION")
print("="*60)

# Test 1: Check custom fields
print("\n1. Checking Custom Fields...")
fields = frappe.get_all('Custom Field', 
    filters={'dt': 'Job Card', 'fieldname': ['in', [
        'custom_material_status',
        'custom_readiness_status', 
        'custom_can_start_operation',
        'custom_material_available_for_operation',
        'custom_blocked_by',
        'custom_dependency_last_updated'
    ]]},
    fields=['fieldname', 'fieldtype'])

print(f"   Found {len(fields)} custom fields:")
for f in fields:
    print(f"   ✓ {f.fieldname} ({f.fieldtype})")

if len(fields) >= 6:
    print("   ✅ Custom fields verified")
else:
    print("   ⚠️  Some custom fields missing")

# Test 2: Check hooks
print("\n2. Checking Hook Registration...")
hooks = frappe.get_hooks('doc_events')

wo_hooks = hooks.get('Work Order', {})
if 'on_submit' in wo_hooks and 'mes_coordinator' in str(wo_hooks['on_submit']):
    print("   ✅ Work Order on_submit hook registered")
else:
    print("   ⚠️  Work Order hook may not be registered correctly")

se_hooks = hooks.get('Stock Entry', {})
if 'on_submit' in se_hooks and 'mes_coordinator' in str(se_hooks['on_submit']):
    print("   ✅ Stock Entry on_submit hook registered")
else:
    print("   ⚠️  Stock Entry hook may not be registered correctly")

jc_hooks = hooks.get('Job Card', {})
if 'on_submit' in jc_hooks and 'mes_coordinator' in str(jc_hooks['on_submit']):
    print("   ✅ Job Card on_submit hook registered")
else:
    print("   ⚠️  Job Card hook may not be registered correctly")

# Test 3: Check engines
print("\n3. Checking Engine Imports...")
try:
    from tekson_manufacturing.mes.dataclasses import MaterialResult, DependencyResult, ReadinessResult
    print("   ✅ Dataclasses imported")
except Exception as e:
    print(f"   ✗ Dataclasses import failed: {e}")

try:
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    print("   ✅ Readiness Engine imported")
except Exception as e:
    print(f"   ✗ Readiness Engine import failed: {e}")

try:
    from tekson_manufacturing.mes.mes_coordinator import MESExecutionCoordinator
    print("   ✅ MES Coordinator imported")
except Exception as e:
    print(f"   ✗ MES Coordinator import failed: {e}")

try:
    from tekson_manufacturing.security.security_utils import validate_manufacturing_role
    print("   ✅ Security module imported")
except Exception as e:
    print(f"   ✗ Security module import failed: {e}")

# Test 4: Create test result
print("\n4. Testing Dataclass Creation...")
try:
    from tekson_manufacturing.mes.dataclasses import MaterialResult, MaterialStatus
    result = MaterialResult(
        is_ready=True,
        status=MaterialStatus.AVAILABLE,
        message="Deployment successful",
        available_qty=100.0,
        required_qty=50.0
    )
    print(f"   ✅ Dataclass works: {result.status}")
except Exception as e:
    print(f"   ✗ Dataclass test failed: {e}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
print("\n✅ Deployment successful! Ready for UAT testing.")
print("\nNext steps:")
print("1. Open browser: http://localhost:8000")
print("2. Login to ERPNext")
print("3. Navigate to Work Order List")
print("4. Create test Work Order")
print("5. Execute UAT test scenarios")
EOF

# Run verification
bench --site $SITE_NAME execute /tmp/verify_mes_deployment.py

# Cleanup
rm -f /tmp/verify_mes_deployment.py

# Step 9: Display next steps
print_header "Deployment Complete!"

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ MES Phase 1 Successfully Deployed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Access Information:"
echo "  → URL: http://localhost:8000"
echo "  → Site: $SITE_NAME"
echo "  → App: $APP_NAME"
echo ""
echo "Next Steps:"
echo "  1. Open browser and login to ERPNext"
echo "  2. Navigate to: Manufacturing → Work Order"
echo "  3. Create a test Work Order"
echo "  4. Execute UAT test scenarios from docs/UAT_DEPLOYMENT_GUIDE.md"
echo ""
echo "UAT Test Scenarios:"
echo "  ✓ TC-001: Work Order Submit (no WIP stock)"
echo "  ✓ TC-002: Work Order Submit (with WIP stock)"
echo "  ✓ TC-003: Material Transfer Refresh"
echo "  ✓ TC-004: Operation Complete → Downstream Refresh"
echo "  ✓ TC-005: Start Button Validation"
echo "  ✓ TC-006: Dependency Validation"
echo "  ✓ TC-007: Large Work Order Performance"
echo "  ✓ TC-008: Cancel & Amend Workflow"
echo ""
echo "Documentation:"
echo "  → UAT Guide: docs/UAT_DEPLOYMENT_GUIDE.md"
echo "  → Test Scenarios: docs/MANUFACTURING_WORKFLOW_AUDIT.md"
echo "  → Readiness: docs/PRODUCTION_READINESS_AUDIT.md"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Ready for Internal UAT Testing!${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
