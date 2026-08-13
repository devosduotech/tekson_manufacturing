/**
 * Tekson Manufacturing - Job Card List View
 * Configures list view columns and status indicators.
 * Simplified for stability - uses Frappe's native List View Settings
 */

frappe.listview_settings['Job Card'] = {
    onload: function(listview) {
        // Hide name column
        listview.hide_name_column = true;
        
        // Add fields to display (explicitly include 'status')
        listview.settings.add_fields = [
            "status",
            "operation",
            "production_item", 
            "for_quantity",
            "custom_plant_floor",
            "work_order"
        ];
        
        // Status color coding - matches ERPNext Job Card status values
        listview.settings.get_indicator = function(doc) {
            const colors = {
                "Open": "blue",
                "Work In Progress": "green",
                "Partially Transferred": "lightblue",
                "Material Transferred": "cyan",
                "On Hold": "orange",
                "Submitted": "green",
                "Cancelled": "red",
                "Completed": "darkgrey"
            };
            const status = doc.status || "Open";
            return [__(status), colors[status] || "gray", ""];
        };
    }
};
