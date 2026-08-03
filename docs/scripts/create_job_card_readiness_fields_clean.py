# Job Card Readiness Fields - Check and Create
# Run this directly in bench console

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
    print(f"  [OK] {field.fieldname} ({field.fieldtype})")
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
        print(f"  [OK] {fieldname} - ALREADY EXISTS")
    else:
        try:
            cf = frappe.new_doc('Custom Field')
            cf.dt = 'Job Card'
            cf.update(field_data)
            cf.insert()
            created.append(fieldname)
            print(f"  [OK] {fieldname} - CREATED")
        except Exception as e:
            failed.append({'fieldname': fieldname, 'error': str(e)})
            print(f"  [FAIL] {fieldname} - FAILED: {str(e)}")

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
print('Job Card readiness fields setup complete!')
print('=' * 80)
