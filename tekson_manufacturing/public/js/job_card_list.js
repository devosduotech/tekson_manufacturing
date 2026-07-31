// ==========================================================
// Tekson Manufacturing - Job Card List View
// ==========================================================

const ENABLE_TEKSON_JOB_CARD_VIEW = false;

if (!ENABLE_TEKSON_JOB_CARD_VIEW) {
    console.log("Tekson Job Card View Disabled");
}
else {

    console.log("Tekson Job Card Override Loaded");

    frappe.router.on("change", () => {

        if (
            frappe.get_route()[0] !== "List" ||
            frappe.get_route()[1] !== "Job Card"
        ) {
            return;
        }

        const timer = setInterval(() => {

            if (!window.cur_list || !cur_list.columns) {
                return;
            }

            clearInterval(timer);

            console.log("Applying Tekson Job Card List View");

            // -------------------------------------------------
            // Configure the CURRENT ListView
            // -------------------------------------------------

            cur_list.settings.hide_name_column = true;

            cur_list.settings.add_fields = [
                "operation",
                "production_item",
                "for_quantity",
                "sequence_id",
                "custom_start_status"
            ];

            cur_list.settings.get_indicator = function (doc) {

                const colors = {
                    "Ready to Start": "green",
                    "Material Available": "green",
                    "Awaiting": "gray",
                    "Awaiting Previous Operation": "orange",
                    "Awaiting Material": "red",
                    "In Progress": "blue",
                    "Completed": "darkgrey"
                };

                return [
                    __(doc.custom_start_status || ""),
                    colors[doc.custom_start_status] || "gray",
                    ""
                ];
            };

            // -------------------------------------------------
            // Rebuild columns
            // -------------------------------------------------

            cur_list.setup_columns();

            // Remove ERPNext Status column
            cur_list.columns = cur_list.columns.filter(col => {
                return col.type !== "Status";
            });

            // Remove ID column
            cur_list.columns = cur_list.columns.filter(col => {

                if (col.type !== "Field") {
                    return true;
                }

                return col.df.fieldname !== "name";
            });

            // Refresh header and rows
            cur_list.render_header(true);
            cur_list.refresh(true);

            frappe.show_alert({
                message: "Tekson Job Card View Applied",
                indicator: "green"
            });

        }, 200);

    });

}
