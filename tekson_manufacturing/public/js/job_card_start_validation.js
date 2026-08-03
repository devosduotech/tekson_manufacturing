// Client Script: Job Card Start Validation
// Doctype: Job Card
// Event: Before Save

// Override the standard Start button behavior
frappe.ui.form.on('Job Card', {
    refresh: function(frm) {
        // Only show custom start button for Open Job Cards
        if (frm.doc.status === 'Open' && frm.doc.docstatus === 0) {
            // Remove standard Start button if exists
            frm.page.clear_inner_toolbar();
            
            // Add custom Start button with validation
            frm.page.add_inner_button(__('Start Job'), function() {
                start_job_with_validation(frm);
            }, 'Primary');
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
