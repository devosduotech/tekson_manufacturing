frappe.pages['test-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({parent: wrapper, title: 'Test Dashboard', single_column: true});
    page.body.html('<div style="padding:20px"><h2>Test Page Loaded Successfully!</h2><p>If you see this, permissions work.</p></div>');
};
