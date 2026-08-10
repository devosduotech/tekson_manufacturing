frappe.pages['material-planning-1'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Daily Material Planning',
		single_column: true
	});
}