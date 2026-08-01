import frappe

frappe.init(site='teksons.dev')
frappe.connect()

print("=" * 60)
print("SIMPLE VALIDATION - Data Check Only")
print("=" * 60)

# Check Work Orders
print("\n1. Work Orders (R21x)...")
wo_count = frappe.db.count('Work Order', {'production_item': ['like', '%R21%']})
print(f"   ✅ Found {wo_count} Work Orders")

# Check Job Cards
print("\n2. Job Cards...")
jc_count = frappe.db.count('Job Card')
print(f"   ✅ Found {jc_count} Job Cards")

# Check Stock Entries
print("\n3. Stock Entries...")
se_count = frappe.db.count('Stock Entry', {'docstatus': 1})
print(f"   ✅ Found {se_count} submitted Stock Entries")

# Check Warehouses
print("\n4. Warehouses...")
wh_list = frappe.get_all('Warehouse', fields=['name', 'warehouse_name'])
print(f"   ✅ Found {len(wh_list)} warehouses")
print("   Sample warehouses:")
for wh in wh_list[:5]:
    print(f"      - {wh.name}: {wh.warehouse_name}")

# Check Items
print("\n5. Items...")
item_count = frappe.db.count('Item')
print(f"   ✅ Found {item_count} items")

# Check BOMs
print("\n6. BOMs...")
bom_count = frappe.db.count('BOM', {'docstatus': 1})
print(f"   ✅ Found {bom_count} active BOMs")

print("\n" + "=" * 60)
print("✅ DATA VALIDATION COMPLETE")
print("=" * 60)
print("\nNext: Add custom fields and migrate warehouse structure")

frappe.destroy()
