frappe.ui.form.on("Material Request Item", {
    custom_rm_loss_pct(frm, cdt, cdn) {
        calculate_rm_loss_qty(frm, cdt, cdn);
    },
    qty(frm, cdt, cdn) {
        calculate_rm_loss_qty(frm, cdt, cdn);
    }
});

function calculate_rm_loss_qty(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row) return;

    const loss_pct = flt(row.custom_rm_loss_pct || 0) / 100;
    const base_qty = flt(row.qty || 0) / (1 + loss_pct);
    const loss_qty = base_qty * loss_pct;

    frappe.model.set_value(cdt, cdn, "custom_rm_loss_qty", loss_qty);
}