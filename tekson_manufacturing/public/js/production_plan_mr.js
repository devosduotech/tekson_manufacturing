/**
 * Production Plan — Generate Material Requests button
 */
frappe.ui.form.on('Production Plan', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Generate Material Requests'), function() {
                frappe.call({
                    method: 'tekson_manufacturing.planning.material_planning_service.generate_daily_material_requests',
                    args: { production_plan: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Generating Material Requests...'),
                    callback: function(r) {
                        if (r.message && r.message.created_mrs) {
                            let mrs = r.message.created_mrs;
                            let msg = __('Created {0} Material Request(s):<br>', [mrs.length]);
                            mrs.forEach(function(mr) {
                                msg += '<br><a href="/app/material-request/' + mr + '">' + mr + '</a>';
                            });
                            frappe.msgprint({title: __('Material Requests Created'), message: msg, indicator: 'green'});
                            frm.refresh();
                        } else {
                            frappe.msgprint({title: __('No MRs Created'), message: r.message.message || __('All materials already in WIP'), indicator: 'blue'});
                        }
                    }
                });
            });
        }
    }
});
