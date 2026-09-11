// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
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
		frm.trigger("set_root_item");
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

	set_root_item(frm) {
		if (frm.is_new() && frm.doc.items?.length) {
			frappe.model.set_value(frm.doc.items[0].doctype, frm.doc.items[0].name, "is_root", 1);
		}
	},

	add_custom_buttons(frm) {
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
		}).then(() => {
			frm.reload_doc();
		});
	},
});

frappe.ui.form.on("BOM Bulk Creator Item", {
	item_code(frm, cdt, cdn) {
		let item = frappe.get_doc(cdt, cdn);
		if (item.item_code && item.is_root) {
			frappe.model.set_value(cdt, cdn, "fg_item", item.item_code);
		}
	},
});
