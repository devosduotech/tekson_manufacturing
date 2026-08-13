/**
 * Material Transfer Pick List - Work Order List View Integration
 * 
 * Adds "Pick List" button to Work Order List View for quick access.
 * TEMPORARILY DISABLED - getdoctype() error
 */

// Disabled - causing getdoctype() error in ERPNext
// var wos = frappe.listview_settings['Work Order'] || {};
// wos.onload = function(listview) {
//     listview.page.add_action_item(__('Pick List'), function() {
//         let wo = listview.get_checked_items().length === 1 ? listview.get_checked_items()[0].name : '';
//         let url = '/app/query-report/Material Transfer Pick List' + (wo ? '?work_order=' + encodeURIComponent(wo) : '');
//         window.open(url, '_blank');
//     });
// };
// frappe.listview_settings['Work Order'] = wos;
