# Tekson MES — Known Limitations

**Version:** v15.0.1
**Date:** August 2026

---

## Phase 1 Scope

The following manufacturing scenarios are **not covered** in Phase 1. They are either handled by standard ERPNext or deferred to future phases.

---

## Not in Phase 1

### Rework Operations

Work Orders with rework requirements must be handled manually. There is no automatic rework routing or rework Job Card generation.

**Workaround:** Create a new Work Order for the rework quantity.

---

### Scrap Management

Scrap quantities are tracked through ERPNext's standard BOM scrap percentage. There is no per-operation scrap tracking or scrap analysis dashboard in the MES layer.

**Workaround:** Use ERPNext's standard BOM Item scrap percentage field.

---

### Partial Production

If only a portion of the planned quantity is produced, the Planner must manually revise the Work Order quantity. The system does not automatically split or close partially completed WOs.

**Workaround:** Planner reduces WO quantity before completing the last JC.

---

### Subcontracting

Subcontracted operations and supplier Job Card tracking are not implemented. These require manual Work Orders.

**Planned:** Phase 2.

---

### Work Order Cancellation

Cancelling a Work Order requires the standard ERPNext process: cancel Stock Entries first, then cancel the WO and its Job Cards. The MES does not add a one-click cancellation.

---

### Auto Inter-Department Transfer

When a child Work Order completes in one department and the parent's first operation is in a different department, materials are NOT automatically transferred between department WIPs. This is a manual store transfer.

**Workaround:** Stores person transfers finished sub-assembly from child WIP to parent WIP.

---

### Opening Stock

The system does not include opening stock scripts. Initial inventory must be created manually via Stock Entry (Material Receipt).

---

## ERPNext Standard Behavior

### UI Refresh Delay

After submitting the last Job Card, the Work Order status may take a few seconds to update to "Completed". This is normal — the auto-complete runs via a background worker. A page refresh shows the updated status.

### Manual SE from "Finish" Button

If using the Work Order "Finish" button to create a Manufacture Stock Entry manually, the source warehouses use ERPNext defaults (WO's WIP warehouse), not per-operation department WIPs. This is ERPNext's standard behavior.

**Recommendation:** Let the auto-complete handle SE creation. Only use manual "Finish" as a fallback.

### Job Card "Can Start" Checkbox

The `Can Start Operation` checkbox shows readiness status but does not enforce blocking on its own. The actual enforcement is server-side — when the operator clicks "Start", the system validates dependencies, materials, and child WO completion.

---

## BOM Requirements

### Mandatory BOM Configuration

Phase 1 requires specific BOM fields:

| Field | Required |
|-------|----------|
| BOM Item `Operation` | ✅ Must be set |
| BOM Item `Source Warehouse` | ✅ Must be set |
| BOM Operation `Workstation Type` | ✅ Must be set |
| BOM `Target FG Warehouse` | Recommended |

Without these, some features may not work correctly.

---

## Performance Considerations

### Large Production Plans

Production Plans with 70+ Work Orders may take 30-60 seconds to release. This is normal — each WO is individually created and configured.

### Work Order with 10+ Job Cards

WOs with many Job Cards may show slower readiness refresh times. Performance targets:
- 40 JCs: < 2 seconds
- 100 JCs: < 5 seconds

---

## Version Compatibility

- **Developed for:** ERPNext V15 (15.x.x)
- **Compatible with:** ERPNext V16 (96% — minor UI adjustments may be needed)
- **Not tested on:** ERPNext V14

---

## Support

For issues not covered here, contact the implementation team with:
- Work Order number
- Job Card number
- Error message (screenshot if possible)
- Steps to reproduce
