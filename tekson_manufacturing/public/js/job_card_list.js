/**
 * Tekson Manufacturing - Job Card List View
 * Configures list view columns and status indicators.
 */

frappe.router.on("change", () => {
    if (frappe.get_route()[0] !== "List" || frappe.get_route()[1] !== "Job Card") {
        return;
    }

    let attempts = 0;
    const timer = setInterval(() => {
        if (!window.cur_list || !cur_list.columns) {
            if (++attempts > 25) { clearInterval(timer); return; }  // Stop after 5 seconds
            return;
        }
        clearInterval(timer);

        cur_list.settings.hide_name_column = true;
        cur_list.settings.add_fields = [
            "operation", "production_item", "for_quantity", "sequence_id", "custom_start_status"
        ];

        cur_list.settings.get_indicator = function (doc) {
            const colors = {
                "Ready to Start": "green", "Material Available": "green",
                "Awaiting": "gray", "Awaiting Previous Operation": "orange",
                "Awaiting Material": "red", "In Progress": "blue", "Completed": "darkgrey"
            };
            return [__(doc.custom_start_status || ""), colors[doc.custom_start_status] || "gray", ""];
        };

        cur_list.setup_columns();
        cur_list.columns = cur_list.columns.filter(col => col.type !== "Status");
        cur_list.columns = cur_list.columns.filter(col => {
            if (col.type !== "Field") return true;
            return col.df.fieldname !== "name";
        });

        cur_list.render_header(true);
        cur_list.refresh(true);
    }, 200);
});
