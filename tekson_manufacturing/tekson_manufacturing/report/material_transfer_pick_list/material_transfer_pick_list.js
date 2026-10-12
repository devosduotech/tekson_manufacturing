frappe.query_reports["Material Transfer Pick List"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: "2026-01-01",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: "2026-12-31",
			reqd: 1,
		},
	],
};
