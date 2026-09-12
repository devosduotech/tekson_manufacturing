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
		frm.set_query("operation", "items", function (doc, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (!row.routing) {
				frappe.msgprint(__("Please select a Routing first"));
				return false;
			}
			return {
				query: "frappe.client.get_list",
				filters: {
					parenttype: "Routing",
					parent: row.routing,
				},
				fields: ["operation"],
			};
		});
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
				method: "frappe.client.get_list",
				args: {
					doctype: "BOM Operation",
					filters: { parenttype: "Routing", parent: row.routing },
					fields: ["operation"],
					limit_page_length: 0,
				},
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
