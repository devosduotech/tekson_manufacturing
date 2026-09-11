// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//
// BOM Bulk Creator — Phase 1
// Creates multi-level BOM hierarchies as Draft.
// Does NOT submit BOMs. Does NOT link child bom_no.

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
		if (!frm.is_new()) {
			if (frm.doc.status === "Completed" || frm.doc.docstatus === 2) {
				return;
			}

			frm.add_custom_button(__("Preview BOMs"), () => {
				frm.trigger("preview_boms");
			}, __("Tools"));

			if (frm.doc.docstatus === 1 && frm.doc.status !== "Completed") {
				frm.add_custom_button(__("Create Draft BOMs"), () => {
					frm.trigger("create_draft_boms");
				}, __("Tools"));
			}
		}
	},

	preview_boms(frm) {
		frm.call({
			method: "preview_boms",
			doc: frm.doc,
			callback(r) {
				if (r.message) {
					let preview = r.message;
					let msg = __("<b>Bulk BOM Creation Preview</b><br><br>");
					msg += __("Total BOMs to create: {0}<br>", [preview.total_boms]);
					msg += __("Existing BOMs (will skip): {0}<br><br>", [preview.existing_boms.length]);

					if (preview.bom_list && preview.bom_list.length) {
						msg += __("<b>BOM List:</b><br>");
						preview.bom_list.forEach(bom => {
							let status_text = bom.status === "will_create" ? "[Will Create]" :
								bom.status === "submitted_exists" ? "[Submitted]" : "[Draft]";
							msg += `${bom.item_code} (Level ${bom.level}) - ${bom.child_items_count} items ${status_text}<br>`;
						});
					}

					frappe.msgprint({
						title: __("Preview"),
						indicator: "green",
						message: msg,
					});
				}
			},
		});
	},

	create_draft_boms(frm) {
		frappe.confirm(
			__("This will create all BOMs as Draft. Continue?"),
			() => {
				frm.call({
					method: "enqueue_create_boms",
					doc: frm.doc,
				});
			}
		);
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
