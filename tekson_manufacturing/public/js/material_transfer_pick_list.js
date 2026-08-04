/**
 * Material Transfer Pick List - Work Order List View Integration
 * 
 * Adds "Pick List" button to Work Order List View for quick access.
 */

frappe.listview_settings['Work Order'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Pick List'), function() {
            let selected = listview.get_checked_items();
            let work_order = selected.length === 1 ? selected[0].name : '';
            
            let url = '/app/query-report/Material Transfer Pick List';
            if (work_order) {
                url += '?work_order=' + encodeURIComponent(work_order);
            }
            
            window.open(url, '_blank');
        });
    }
};
