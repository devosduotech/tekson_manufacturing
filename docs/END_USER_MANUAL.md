# Tekson Manufacturing — User Guide

**Version:** 1.0 (Draft)  
**Date:** September 2026  
**Product:** Tekson Manufacturing Execution System (MES)  
**Platform:** ERPNext v15  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Bill of Materials (BOM) Management](#3-bill-of-materials-bom-management)
4. [Work Order & Production Execution](#4-work-order--production-execution)
5. [Material Planning & Transfers](#5-material-planning--transfers)
6. [Job Card Operations](#6-job-card-operations)
7. [Dashboards & Reports](#7-dashboards--reports)
8. [Troubleshooting](#8-troubleshooting)
9. [Glossary](#9-glossary)

---

## 1. Introduction

### What is Tekson Manufacturing?

Tekson Manufacturing is an add-on module for ERPNext that enhances your production workflow with:

- **Automated Job Card Readiness** — System automatically checks if materials are available and previous operations are complete before allowing you to start a job
- **Material Planning** — One-click Material Request generation grouped by department
- **BOM Bulk Creator** — Create complex multi-level Bills of Materials in minutes instead of hours
- **Production Dashboards** — Real-time visibility into production status, exceptions, and department workload

### Who is this guide for?

| Role | What you'll use |
|------|----------------|
| **Production Manager** | Dashboards, Material Planning, BOM Bulk Creator |
| **Store Operator** | Material Transfer Pick List, Material Requests |
| **Shop Floor Supervisor** | Job Card status, starting/completing operations |
| **System Administrator** | Configuration, Workstation setup |

---

## 2. Getting Started

### Logging In

1. Open your browser and go to your ERPNext URL (e.g., `https://your-site.com`)
2. Enter your username and password
3. You'll see the ERPNext home page

### Key Navigation

| What you need | Where to find it |
|---------------|-----------------|
| BOM Bulk Creator | Search bar → "BOM Bulk Creator" |
| Material Planning | Search bar → "Material Planning" or `/app/material-planning` |
| Work Orders | Manufacturing → Work Order |
| Job Cards | Manufacturing → Job Card |
| Material Requests | Stock → Material Request |
| MES Dashboard | `/mes/dashboard` |

### Understanding the Status Flow

Every Job Card goes through this status flow:

```
Awaiting Material / Awaiting Previous Operation
              ↓
        Ready to Start
              ↓
       Work In Progress
              ↓
         Completed
```

You **cannot** start a Job Card until the system shows **"Ready to Start"**.

---

## 3. Bill of Materials (BOM) Management

### 3.1 Creating a Multi-Level BOM (BOM Bulk Creator)

When you have a finished good that requires multiple sub-assemblies (each with their own BOM), use the **BOM Bulk Creator** to create all BOMs at once.

**Step 1: Create a New BOM Bulk Creator**

1. Search for "BOM Bulk Creator" in the search bar
2. Click **New**
3. Fill in the header:
   - **Item Code**: The finished good item (e.g., "R215 Combi Cooler")
   - **Qty**: Quantity to produce (default: 1)
   - **Company**: Your company name
   - **Target FG Warehouse**: Where finished goods will be stored

**Step 2: Add Items**

Switch to the **Sub Assemblies & Raw Materials** tab. Add each item as a row:

| Field | Description | Example |
|-------|-------------|---------|
| Item Code | The material or sub-assembly item | Aluminium Coil 0.2*110 |
| FG Item | Which parent item this belongs to (leave blank for root FG) | R215 Combi Cooler |
| Parent Row No | The row number of the parent item (leave blank for root) | — |
| Qty | Quantity needed per unit | 5.736 |
| Stock UOM | Unit of measure | Kg |
| Routing | Which routing this item follows | R215 Routing |
| Operation | Which operation in the routing | Core Assembly |
| Source Warehouse | Where to pick the material from | Raw Material Stores - TPL |

**Step 3: Build the Hierarchy**

To create sub-assemblies, add the sub-assembly item as a row with:
- **FG Item** = the parent item's item code
- **Parent Row No** = the row number of the parent

Example hierarchy:
```
Row 1: R215 Combi Cooler (root — no FG Item or Parent Row No)
Row 2: R215 OC → FG Item = R215 Combi Cooler, Parent Row No = 1
Row 3: Aluminium Coil 0.3*110 → FG Item = R215 OC, Parent Row No = 2
Row 4: R215 RAD → FG Item = R215 Combi Cooler, Parent Row No = 1
Row 5: Aluminium Coil 0.2*110 → FG Item = R215 RAD, Parent Row No = 4
```

**Step 4: Create Draft BOMs**

1. Click **Tools → Create Draft BOMs**
2. The system validates the hierarchy (checks for cycles, missing fields)
3. BOMs are created as **Draft** documents (bottom-up: sub-assemblies first, root last)
4. Status changes to **Completed** when all BOMs are created

**Step 5: Review and Submit**

1. Go to BOM list and find your newly created Draft BOMs
2. Open each Draft BOM and review the items
3. **Important:** Child BOM links (`bom_no` field) are left blank intentionally. You must manually link them:
   - Open the parent BOM
   - In the Items table, find the sub-assembly row
   - Set the `BOM No` field to the child BOM you created
4. Add any operations, quality templates, or cost details
5. **Submit** each BOM (sub-assembly BOMs first, then root BOM)

> **Note:** All BOMs are created as Draft. You must review and submit them before they can be used in Work Orders.

### 3.2 BOM Tree View

The **BOM Tree** tab shows your hierarchy visually. Use it to verify the parent-child relationships before creating BOMs.

---

## 4. Work Order & Production Execution

### 4.1 Creating a Work Order

**From Production Plan (Recommended):**

1. Go to Production Plan → Open a submitted plan
2. Click **Create → Work Order**
3. Work Orders are created with warehouses auto-set:
   - **FG Warehouse** = from BOM's target FG warehouse
   - **WIP Warehouse** = from first operation's workstation plant floor
   - **Source Warehouse** = Raw Material Stores

**Manual Creation:**

1. Go to Work Order → New
2. Select the Item Code (finished good)
3. Select the BOM
4. Set quantities and dates
5. Warehouses auto-populate based on the BOM and workstation configuration

### 4.2 Submitting a Work Order (Production Release)

When you **submit** a Work Order, the system:

1. Validates your permissions
2. Evaluates all Job Cards in the Work Order
3. Sets each Job Card's status:
   - **"Ready to Start"** — if materials are in WIP and no previous operation dependency
   - **"Awaiting Material"** — if materials are not yet in the WIP warehouse
   - **"Awaiting Previous Operation"** — if a previous operation must complete first

> **Important:** Submitting a Work Order is the "Production Release" step. Job Cards become visible to shop floor operators after this.

### 4.3 Work Order Statuses

| Status | Meaning |
|--------|---------|
| Draft | Work Order created but not yet released |
| Open | Released — production can begin |
| In Process | At least one Job Card is in progress |
| Completed | All Job Cards completed, finished goods produced |
| Cancelled | Work Order cancelled |

---

## 5. Material Planning & Transfers

### 5.1 Generating Material Requests

The Material Planning page creates Material Requests grouped by department WIP warehouse.

**Step 1: Open Material Planning**

- Search for "Material Planning" or go to `/app/material-planning`

**Step 2: Select Parameters**

- **Production Plan**: Choose the Production Plan to generate MRs for
- **Planned Start Date**: The date you want materials available (defaults to today)

**Step 3: Generate**

Click **Generate Material Requests**. The system:

1. Finds all incomplete Work Orders starting on that date
2. Calculates raw material requirements (skipping sub-assemblies with their own Work Orders)
3. Checks what's already in each department's WIP warehouse
4. Creates Material Requests only for items with actual shortages
5. Groups items by target WIP warehouse (department)

**Step 4: Review Results**

You'll see a summary of created MRs:
- Each MR is grouped by department WIP warehouse
- Quantities are rounded up to whole numbers
- Each MR is linked to the Production Plan

### 5.2 Material Transfer Pick List

The Pick List report shows what materials need to be transferred and where.

**Step 1: Open the Report**

- Go to Work Order list → Click **Pick List** in the toolbar
- Or search for "Material Transfer Pick List"

**Step 2: Set Date Range**

- **From Date** and **To Date**: Filter by planned start date

**Step 3: Review the Report**

| Column | Meaning |
|--------|---------|
| Work Order | Which WO needs the material |
| Item Code | Material item |
| Required | Total quantity needed |
| Available | Quantity available at source warehouse |
| To Transfer | Quantity to transfer (Required − Already in WIP) |
| To (WIP) | Target WIP warehouse (department) |

### 5.3 Creating a Material Transfer

1. From the Pick List, note the items and quantities
2. Go to Stock Entry → New
3. Set Purpose = **Material Transfer** or **Material Transfer for Manufacture**
4. Add items with:
   - **From Warehouse**: Raw Material Stores - TPL (or BOF Stores)
   - **To Warehouse**: The WIP warehouse from the Pick List
5. Submit the Stock Entry

**What happens after Material Transfer:**

- The system automatically detects the material transfer
- Job Cards in the affected Work Orders are re-evaluated
- If materials are now available, Job Card status changes from "Awaiting Material" to **"Ready to Start"**

### 5.4 How Material Availability Works

The system checks material availability **per Job Card operation**:

- Each BOM item can be assigned to a specific operation
- Only materials for that operation need to be in WIP before the Job Card can start
- Materials are checked against the **Bin** (actual stock) in the target WIP warehouse

---

## 6. Job Card Operations

### 6.1 Understanding Job Card Status

| Status | What it means | What to do |
|--------|--------------|------------|
| **Awaiting Material** | Materials not yet in WIP warehouse | Ask stores to transfer materials |
| **Awaiting Previous Operation** | Previous operation must complete first | Wait for prior Job Card to complete |
| **Ready to Start** | All conditions met — can begin work | Start the operation |
| **Work In Progress** | Operation is running | Complete when done |
| **Completed** | Operation finished | System auto-refreshes next Job Card |

### 6.2 Starting a Job Card

1. Open the Job Card
2. Verify the status shows **"Ready to Start"**
3. Click **Start** or set status to "Work In Progress"

**If the system blocks you**, it will show one of these messages:

| Error | Cause | Solution |
|-------|-------|----------|
| "Materials not available" | WIP warehouse doesn't have enough stock | Contact stores for material transfer |
| "Previous operation not complete" | Dependency not met | Wait for previous Job Card to complete |
| "Job Card not linked to Work Order" | Configuration issue | Contact administrator |

### 6.3 Completing a Job Card

1. Set the status to **"Completed"**
2. Enter the completed quantity
3. Submit

**What happens automatically:**

- System evaluates the **next** Job Card(s) in the sequence
- If the next Job Cards' materials are available and dependencies met, their status changes to "Ready to Start"
- If this was the **last** Job Card in the Work Order, the system automatically:
  - Creates a Manufacture Stock Entry
  - Moves finished goods to the FG warehouse
  - Marks the Work Order as "Completed"

### 6.4 Parallel Operations

If multiple Job Cards share the same sequence number (parallel operations), they can run simultaneously. The system evaluates each one independently.

### 6.5 Job Card Custom Fields

| Field | Description |
|-------|-------------|
| Start Status | Current readiness status (shown to operators) |
| Can Start Operation | ✅ if all conditions met |
| Material Available | ✅ if materials are in WIP |
| Dependency Check | ✅ if previous operation is complete |
| Plant Floor | Which department/plant floor this JC belongs to |
| Operation Item | Which item this operation produces |
| Blocked By | What is preventing this JC from starting |

---

## 7. Dashboards & Reports

> **Note:** Dashboards and reports are planned features and are not yet available. The section below describes what will be built.

### 7.1 MES Dashboard (Planned)

**URL:** `/mes/dashboard` *(not yet implemented)*

The dashboard will show:

- **Production Status** — Count of Work Orders and Job Cards by status
- **Active Alerts** — Negative stock, stale Job Cards, material shortages
- **Recent Activity** — Recently completed Job Cards and Stock Entries
- **Department-wise Production** — Work Orders by department/WIP warehouse

### 7.2 Material Transfer Pick List (Planned)

**URL:** `/app/query-report/Material%20Transfer%20Pick%20List` *(not yet implemented)*

Will show materials to transfer for submitted Work Orders within a date range. Use this to plan daily material transfers.

### 7.3 Planner Intelligence (Planned)

Backend APIs are ready but no frontend page exists yet. Planned features:

| Feature | What it will show |
|---------|------------------|
| Planner KPIs | On-time %, readiness %, WO counts |
| Production Calendar | Upcoming WOs grouped by date |
| Exceptions | Overdue WOs, blocked JCs, material shortages |
| Department Workload | WO count and quantity per department |
| Stores KPIs | MR count, items short per department |

---

## 8. Troubleshooting

### Common Issues

**"Cannot start Job Card"**

1. Check the **Start Status** field on the Job Card
2. If "Awaiting Material" — check if materials are in the WIP warehouse
3. If "Awaiting Previous Operation" — check if the previous Job Card is completed
4. If "Ready to Start" but still blocked — contact system administrator

**Material Request has wrong quantities**

- The system only requests materials with actual shortages (required − WIP stock > 0)
- If WIP warehouse already has stock, it won't be re-requested
- Quantities are rounded up to whole numbers

**BOM Bulk Creator fails**

- Check that all items have valid Item Codes
- Ensure Parent Row No is set for all non-root items
- Verify no circular references in the hierarchy
- Check the status field — if "Failed", review the Error Log

**Work Order warehouses are wrong**

- Warehouses auto-populate from BOM and Workstation configuration
- FG Warehouse comes from BOM's target FG warehouse
- WIP Warehouse comes from the first operation's workstation plant floor
- Source Warehouse defaults to "Raw Material Stores"

### Getting Help

- Check the **Error Log** in ERPNext for detailed error messages
- Contact your system administrator
- Refer to the internal testing guide for debug commands

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **BOM** | Bill of Materials — list of items needed to produce a finished good |
| **BOM Bulk Creator** | Tool to create multi-level BOM hierarchies in one step |
| **Work Order (WO)** | Instruction to produce a quantity of a finished good |
| **Job Card (JC)** | Individual operation within a Work Order |
| **Material Request (MR)** | Request to transfer materials from stores to production |
| **Stock Entry (SE)** | Document recording material movement between warehouses |
| **WIP Warehouse** | Work In Progress warehouse — where materials wait for production |
| **FG Warehouse** | Finished Goods warehouse — where completed products are stored |
| **Source Warehouse** | Where raw materials are stored (Raw Material Stores, BOF Stores) |
| **Plant Floor** | Physical production area (e.g., Weld, CNC, RA, RP) |
| **Routing** | Sequence of operations to produce an item |
| **Operation** | A single production step (e.g., Cutting, Welding, Assembly) |
| **Dependency** | Requirement that a previous operation must complete before the next can start |
| **Readiness** | System check of whether a Job Card can start (materials + dependencies) |
| **Production Plan** | Master plan scheduling which items to produce and when |
| **Bin** | Actual stock quantity of an item in a specific warehouse |
| **Pick List** | Report showing what materials to transfer and where |

---

## Appendix A: Warehouse Structure

```
Raw Material Stores - TPL     ← Source warehouse for raw materials
BOF Stores - TPL              ← Source for BOF items
WIP-Ralu Weld - TPL           ← Welding department WIP
WIP-Ralu In - TPL             ← Core assembly department WIP
WIP-CNC - TPL                 ← CNC department WIP
WIP-RA - TPL                  ← RA department WIP
WIP-RP - TPL                  ← RP (Folding) department WIP
WIP-W - TPL                   ← W (Shearing) department WIP
Finish Goods Stores - TPL     ← Completed products
Scrap Stores - TPL            ← Scrap materials
```

## Appendix B: Status Flow Diagrams

### Work Order Flow
```
Draft → Open → In Process → Completed
                  ↑              ↑
          (JC starts)    (Last JC completes)
```

### Job Card Flow
```
[Awaiting Material] ──┐
                      ├──→ Ready to Start → Work In Progress → Completed
[Awaiting Prev Op] ──┘
```

### Material Flow
```
Raw Material Stores → (Material Transfer) → WIP Warehouse → (Production) → FG Warehouse
```

---

*Document Version: 1.0 (Draft)*  
*Last Updated: September 2026*  
*Prepared by: OSDuo Tech LLP*
