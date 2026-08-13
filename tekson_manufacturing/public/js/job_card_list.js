/**
 * Tekson Manufacturing - Job Card List View
 * Configures list view columns and status indicators.
 * Simplified for stability - uses Frappe's native List View Settings
 */

frappe.listview_settings['Job Card'] = {
    onload: function(listview) {
        // Hide name column, show operation instead
        listview.hide_name_column = true;
        
        // Add custom fields to display
        listview.settings.add_fields = [
            "operation",
            "production_item", 
            "for_quantity",
            "custom_plant_floor",
            "work_order"
        ];
        
        // Status color coding
        listview.settings.get_indicator = function(doc) {
            const colors = {
                "Open": "blue",
                "Work In Progress": "green",
                "On Hold": "orange",
                "Completed": "darkgrey",
                "Stopped": "red"
            };
            const status = doc.status || "Open";
            return [__(status), colors[status] || "gray", ""];
        };
    }
};
