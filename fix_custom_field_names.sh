#!/bin/bash
# Fix Custom Field Names in Code to Match Database
# Run this on your VM

cd ~/frappe-bench/apps/tekson_manufacturing

echo "=== Fixing Custom Field Names ==="
echo ""

# Update job_card_utils.py
echo "Updating job_card_utils.py..."
sed -i 's/custom_item_code/custom_operation_item_code/g' tekson_manufacturing/utils/job_card_utils.py
sed -i 's/custom_actual_production_item/custom_actual_production_qty/g' tekson_manufacturing/utils/job_card_utils.py

# Update job_card_service.py  
echo "Updating job_card_service.py..."
sed -i 's/custom_item_code/custom_operation_item_code/g' tekson_manufacturing/services/job_card_service.py
sed -i 's/custom_actual_production_item/custom_actual_production_qty/g' tekson_manufacturing/services/job_card_service.py

echo ""
echo "=== Files Updated ==="
echo ""

# Show what changed
git diff --stat

echo ""
echo "=== Committing Changes ==="
echo ""

git add tekson_manufacturing/utils/job_card_utils.py
git add tekson_manufacturing/services/job_card_service.py

git commit -m "fix: Update custom field names to match database

- custom_item_code → custom_operation_item_code
- custom_actual_production_item → custom_actual_production_qty
- Matches existing custom fields in Job Card doctype"

echo ""
echo "=== Pushing to GitHub ==="
echo ""

git pull origin develop --rebase
git push origin develop

echo ""
echo "=== Complete! ==="
echo ""
echo "Next steps:"
echo "1. bench --site teksons.dev clear-cache"
echo "2. bench restart"
echo "3. Test custom fields in console"
