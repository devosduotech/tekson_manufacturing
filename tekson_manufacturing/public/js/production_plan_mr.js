/**
 * Production Plan — Generate Material Requests button
 */
frappe.ui.form.on('Production Plan', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Generate Material Requests'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Generate Material Requests'),
                    fields: [
                        {fieldname: 'planned_date', fieldtype: 'Date', label: __('Planned Start Date'), 
                         default: frappe.datetime.get_today(), reqd: 1},
                    ],
                    primary_action_label: __('Generate'),
                    primary_action: function(values) {
                        d.hide();
                        frappe.call({
                            method: 'tekson_manufacturing.planning.material_planning_service.generate_daily_material_requests',
                            args: { production_plan: frm.doc.name, planned_date: values.planned_date },
                            freeze: true,
                            freeze_message: __('Generating Material Requests...'),
                            callback: function(r) {
                                let res = r.message;
                                if (res && res.created_mrs && res.created_mrs.length > 0) {
                                    let names = res.created_mrs.join(', ');
                                    let details = (res.details || []).map(d => '<br>' + d.name + ' — ' + d.department_wip + ' (' + d.items + ' items)').join('');
                                    frappe.msgprint({
                                        title: __('✅ Generated'),
                                        message: __('<b>{0}</b> MR(s) for <b>{1}</b>: {2}', [res.created_mrs.length, res.planned_date, details]),
                                        indicator: 'green'
                                    });
                                } else {
                                    let msg = (res && res.message) || __('All materials already in WIP for {0}').format(values.planned_date);
                                    frappe.msgprint({title: __('No MRs'), message: msg, indicator: 'blue'});
                                }
                            }
                        });
                    }
                });
                d.show();
            });
        }
    }
});
