# ERPNext V15 Customization — Job Card Required Raw Materials

## Objective

Implement a customization in the existing `tekson_manufacturing` custom Frappe/ERPNext application.

The purpose is to display, inside the **Job Card**, the raw materials and quantities required for the **specific operation represented by that Job Card**.

The information is intended for the shop-floor operator.

The operator should be able to see:

- Item
- Item Name
- Required Quantity
- UOM

The information must be **read-only**.

---

# 1. Important Business Rule

Do **not** recalculate material requirements from the BOM.

ERPNext has already processed the BOM when the Work Order was created.

The Work Order's:

```text
Work Order → Required Items
```

already contains the required material information, including:

- Item
- Item Name
- Required Quantity
- Stock UOM
- Operation

The Work Order is therefore the **source of truth** for this customization.

The customization must use:

```text
Job Card
   ↓
Work Order
   ↓
Work Order.required_items
   ↓
Filter by Job Card.operation
   ↓
Display required materials
```

Do not independently calculate BOM quantity.

Do not query BOM Items to calculate quantity.

Do not duplicate ERPNext's BOM explosion/calculation logic.

---

# 2. Existing Environment

Target application:

```text
tekson_manufacturing
```

Target ERPNext/Frappe version:

```text
ERPNext V15
Frappe V15
```

The application already contains other Teksons manufacturing customizations.

Therefore:

- Do not modify ERPNext core.
- Do not modify Frappe core.
- Do not interfere with existing Teksons customizations.
- Reuse existing application conventions where possible.
- Inspect the existing application structure before creating new files.
- Follow existing naming and coding conventions.

---

# 3. Functional Requirement

Add a read-only section/table to the standard ERPNext **Job Card**.

Suggested section/table label:

```text
Required Raw Materials
```

The operator should see something similar to:

```text
Required Raw Materials

┌──────────────────────┬──────────────┬─────────┐
│ Item                 │ Required Qty │ UOM     │
├──────────────────────┼──────────────┼─────────┤
│ RM-001               │ 10           │ Nos     │
│ RM-002               │ 20           │ Nos     │
│ RM-003               │ 5            │ Kg      │
└──────────────────────┴──────────────┴─────────┘
```

The table is informational only.

The operator must not be able to:

- Add rows
- Delete rows
- Change Item
- Change Item Name
- Change Required Qty
- Change UOM

---

# 4. Data Source

The linked Work Order is available on the Job Card.

Use:

```python
job_card.work_order
```

to retrieve the Work Order.

Then use:

```python
work_order.required_items
```

as the source of the material information.

Each Work Order Required Item already contains the operation.

The filtering rule is:

```python
required_item.operation == job_card.operation
```

Only matching items should be displayed.

Example:

Work Order Required Items:

```text
Item       Required Qty    UOM    Operation
------------------------------------------------
RM-001     100             Nos    Cutting
RM-002     100             Nos    Assembly
RM-003     200             Nos    Welding
RM-004      50             Nos    Welding
RM-005     100             Nos    Painting
```

Job Card:

```text
Work Order: WO-00001
Operation: Welding
```

The Job Card must display:

```text
Item       Required Qty    UOM
--------------------------------
RM-003     200             Nos
RM-004      50             Nos
```

It must NOT display RM-001, RM-002 or RM-005.

---

# 5. Do Not Recalculate Quantity

This is critical.

The implementation must use the quantity already calculated by the Work Order.

Use:

```python
row.required_qty
```

Do not calculate:

```text
BOM Qty × Work Order Qty
```

Do not independently explode the BOM.

Do not calculate scrap, conversion factors, or other BOM/WO quantities.

ERPNext has already performed the required calculation.

The customization only reads and displays the resulting Work Order requirement.

---

# 6. Custom Child DocType

Create a child table DocType in the `tekson_manufacturing` application.

Suggested name:

```text
Job Card Required Material
```

Set:

```text
Is Child Table = Yes
```

Fields:

### 6.1 Item

```text
Fieldname: item_code
Label: Item
Type: Link
Options: Item
Read Only: Yes
```

### 6.2 Item Name

```text
Fieldname: item_name
Label: Item Name
Type: Data
Read Only: Yes
```

### 6.3 Required Quantity

```text
Fieldname: required_qty
Label: Required Qty
Type: Float
Read Only: Yes
```

### 6.4 UOM

```text
Fieldname: uom
Label: UOM
Type: Link
Options: UOM
Read Only: Yes
```

Do not add unnecessary fields at this stage.

Do not add:

- Source Warehouse
- Transferred Qty
- Consumed Qty
- Batch
- Serial No
- Location
- Available Qty
- Pending Qty

Those are outside the current requirement.

---

# 7. Add Child Table to Job Card

Extend the standard ERPNext `Job Card` DocType through the custom application.

Add a Table field:

```text
Label: Required Raw Materials
Fieldname: required_raw_materials
Field Type: Table
Options: Job Card Required Material
Read Only: Yes
```

Do not modify the standard ERPNext Job Card DocType directly.

Use the standard Frappe customization mechanism supported by the application.

Prefer application-controlled customization rather than manually editing ERPNext source files.

---

# 8. Server-Side API

Create a server-side method in the `tekson_manufacturing` application.

Suggested
