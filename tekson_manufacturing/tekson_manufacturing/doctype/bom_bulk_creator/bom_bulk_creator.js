// Copyright (c) 2026, OSDuo Tech LLP. All rights reserved.
// Developer & Maintainer: OSDuo Tech LLP <developer@osduotech.com>
//
// BOM Bulk Creator - Phase 1
// Creates multi-level BOM hierarchies as Draft.
// Does NOT submit BOMs. Does NOT link child bom_no (user updates manually).

frappe.provide("tekson_manufacturing.bom_bulk_creator");

frappe.ui.form.on("BOM Bulk Creator", {
	setup(frm) {
		frm.trigger("set_queries");
	},

	refresh(frm) {
		frm.trigger("add_custom_buttons");
		frm.trigger("set_child_list_view");
	},

	set_queries(frm) {
		frm.set_query("item_code", "items", function () {
			return {
				query: "erpnext.controllers.queries.item_query",
			};
		});
		frm.set_query("fg_item", "items", function () {
			return {
				query: "erpnext.controllers.queries.item_query",
			};
		});
	},

	set_child_list_view(frm) {
		if (!frm.fields_dict.items || !frm.fields_dict.items.grid) return;
		let grid = frm.fields_dict.items.grid;
		grid.set_column_in_list_view("item_code", 2);
		grid.set_column_in_list_view("fg_item", 2);
		grid.set_column_in_list_view("source_warehouse", 1);
		grid.set_column_in_list_view("target_fg_warehouse", 1);
		grid.set_column_in_list_view("qty", 1);
		grid.set_column_in_list_view("stock_uom", 1);
		grid.set_column_in_list_view("routing", 1.5);
		grid.set_column_in_list_view("operation", 1.5);
		grid.refresh();
	},

	add_custom_buttons(frm) {
		frm.clear_custom_buttons();

		if (frm.is_new()) {
			return;
		}

		if (frm.doc.status !== "Completed" && frm.doc.status !== "Failed") {
			frm.add_custom_button(__("Create Draft BOMs"), () => {
				frm.trigger("create_draft_boms");
			}, __("Tools"));
		}
	},

	create_draft_boms(frm) {
		frm.call({
			method: "enqueue_create_boms",
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Creating BOMs..."),
		}).then(() => {
			frm.reload_doc();
		});
	},
});

frappe.ui.form.on("BOM Bulk Creator Item", {
	routing(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.routing) {
			frappe.call({
				method: "tekson_manufacturing.tekson_manufacturing.doctype.bom_bulk_creator.bom_bulk_creator.get_routing_operations",
				args: { routing_name: row.routing },
				callback(r) {
					if (r.message && r.message.length === 1) {
						frappe.model.set_value(cdt, cdn, "operation", r.message[0].operation);
					} else {
						frappe.model.set_value(cdt, cdn, "operation", "");
					}
				},
			});
		} else {
			frappe.model.set_value(cdt, cdn, "operation", "");
		}
	},
});
