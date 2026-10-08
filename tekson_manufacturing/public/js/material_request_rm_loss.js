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
    const qty = flt(row.qty || 0);
    
    // qty already includes loss: qty = base_qty * (1 + loss_pct)
    // loss_qty = base_qty * loss_pct = qty * (loss_pct / (1 + loss_pct))
    const loss_qty = loss_pct > 0 ? qty * (loss_pct / (1 + loss_pct)) : 0;

    frappe.model.set_value(cdt, cdn, "custom_rm_loss_qty", loss_qty);
}