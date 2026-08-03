# Console Script: Create Job Card Readiness Fields

**Purpose:** Check existing fields and create only missing ones

**Run on VM Console:**
```bash
bench --site teksons.dev console
```

**Then paste this script:**

```python
# Job Card Readiness Fields - Check and Create

from frappe import _

# Define required fields
required_fields = [
    {
        'fieldname': 'custom_material_status',
        'label': 'Material Status',
        'fieldtype': 'Select',
        'options': '\nWaiting for Material\nMaterial Available\nMaterial Short',
        'insert_after': 'job_card_item',
        'description': 'Material availability in WIP warehouse',
        'read_only': 1
    },
    {
        'fieldname': 'custom_readiness_status',
        'label': 'Readiness Status',
        'fieldtype': 'Select',
        'options': '\nReady to Start\nWaiting for Previous Operation\nBlocked\nIn Progress\nCompleted',
        'insert_after': 'custom_material_status',
        'description': 'Can operator start this operation?',
        'read_only': 1
    },
    {
        'fieldname': 'custom_material_shortage_details',
        'label': 'Material Shortage Details',
        'fieldtype': 'Text',
        'insert_after': 'custom_readiness_status',
        'description': 'Details of material shortage (if any)',
        'read_only': 1
    },
    {
        'fieldname': 'custom_dependency_last_updated',
        'label': 'Last Updated',
        'fieldtype': 'Datetime',
        'insert_after': 'custom_material_shortage_details',
        'description': 'When readiness was last evaluated',
        'read_only': 1
    },
    {
        'fieldname': 'custom_blocked_by',
        'label': 'Blocked By',
        'fieldtype': 'Data',
        'insert_after': 'custom_dependency_last_updated',
        'description': 'Specific reason if operation is blocked',
        'read_only': 1
    }
]

print('=' * 80)
print('JOB CARD READINESS FIELDS - CHECK AND CREATE')
print('=' * 80)
print()

# Get existing custom fields on Job Card
existing_fields = frappe.get_all('Custom Field',
    filters={'dt': 'Job Card'},
    fields=['fieldname', 'label', 'fieldtype'])

existing_fieldnames = {f.fieldname for f in existing_fields}

print('Existing Job Card Custom Fields:')
print('-' * 80)
for field in sorted(existing_fields, key=lambda x: x.fieldname):
    print(f"  ✓ {field.fieldname} ({field.fieldtype})")
print()

# Check and create required fields
print('Required Readiness Fields:')
print('-' * 80)

created = []
already_exists = []
failed = []

for field_data in required_fields:
    fieldname = field_data['fieldname']
    
    if fieldname in existing_fieldnames:
        already_exists.append(fieldname)
        print(f"  ✓ {fieldname} - ALREADY EXISTS")
    else:
        try:
            cf = frappe.new_doc('Custom Field')
            cf.dt = 'Job Card'
            cf.update(field_data)
            cf.insert()
            created.append(fieldname)
            print(f"  ✅ {fieldname} - CREATED")
        except Exception as e:
            failed.append({'fieldname': fieldname, 'error': str(e)})
            print(f"  ❌ {fieldname} - FAILED: {str(e)}")

frappe.db.commit()

# Summary
print()
print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'  Created: {len(created)}')
print(f'  Already Exists: {len(already_exists)}')
print(f'  Failed: {len(failed)}')
print()

if created:
    print('New Fields Created:')
    for fn in created:
        print(f'    - {fn}')
    print()

if already_exists:
    print('Fields Already Present:')
    for fn in already_exists:
        print(f'    - {fn}')
    print()

if failed:
    print('Failed to Create:')
    for item in failed:
        print(f'    - {item["fieldname"]}: {item["error"]}')
    print()

print('=' * 80)
print('✅ Job Card readiness fields setup complete!')
print('=' * 80)
```

---

## Expected Output

### Scenario 1: No Fields Exist Yet
```
================================================================================
JOB CARD READINESS FIELDS - CHECK AND CREATE
================================================================================

Existing Job Card Custom Fields:
--------------------------------------------------------------------------------
  ✓ custom_department (Data)
  ✓ custom_operation_id (Link)

Required Readiness Fields:
--------------------------------------------------------------------------------
  ✅ custom_material_status - CREATED
  ✅ custom_readiness_status - CREATED
  ✅ custom_material_shortage_details - CREATED
  ✅ custom_dependency_last_updated - CREATED
  ✅ custom_blocked_by - CREATED

================================================================================
SUMMARY
================================================================================
  Created: 5
  Already Exists: 0
  Failed: 0

New Fields Created:
    - custom_material_status
    - custom_readiness_status
    - custom_material_shortage_details
    - custom_dependency_last_updated
    - custom_blocked_by

================================================================================
✅ Job Card readiness fields setup complete!
================================================================================
```

### Scenario 2: Some Fields Already Exist
```
================================================================================
SUMMARY
================================================================================
  Created: 3
  Already Exists: 2
  Failed: 0

New Fields Created:
    - custom_material_status
    - custom_readiness_status
    - custom_material_shortage_details

Fields Already Present:
    - custom_dependency_last_updated
    - custom_blocked_by
```

---

## After Running: Verify Fields

```python
# Verify fields were created
jc_meta = frappe.get_meta('Job Card')

readiness_fields = [f for f in jc_meta.fields if f.fieldname.startswith('custom_') and 'readiness' in f.fieldname or 'material_status' in f.fieldname]

print('Job Card Readiness Fields:')
for f in readiness_fields:
    print(f'  {f.fieldname}: {f.fieldtype} - {f.label}')
```

---

## Next Step: Clear Cache

After creating fields:
```bash
bench --site teksons.dev clear-cache
```

Then verify in UI:
1. Open any Job Card
2. Check if new fields appear
3. Verify field types (Select, Text, Datetime, Data)
