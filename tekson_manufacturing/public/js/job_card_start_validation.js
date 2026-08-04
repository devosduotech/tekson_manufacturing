frappe.ui.form.on('Job Card', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open' && frm.doc.docstatus === 0) {
            frm.page.set_primary_action(__('Start Job'), function() {
                start_job_with_validation(frm);
            });
        }
    }
});


function start_job_with_validation(frm) {
    // Call our custom API which includes material validation
    frappe.call({
        method: 'tekson_manufacturing.api.job_card_start.start_job_card',
        args: {
            job_card_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Validating material availability...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Job Card started successfully'),
                    indicator: 'green'
                });
                
                // Reload the form to show updated status
                frm.refresh();
            }
        },
        error: function(err) {
            // Error message already shown by frappe.throw() in the API
            console.error('Job Card start failed:', err);
        }
    });
}
