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


