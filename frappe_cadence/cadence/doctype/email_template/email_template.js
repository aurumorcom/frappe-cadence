frappe.ui.form.on("Email Template", {
	refresh: function(frm) {
		toggle_fields(frm);
		if (frm.doc.provider === "DSPy") {
			frm.add_custom_button(__("Optimize"), function() {
				frappe.call({
					method: "frappe_cadence.integrations.sift.optimize",
					args: {
						template_doctype: frm.doc.doctype,
						template_name: frm.doc.name
					},
					callback: function(r) {
						if (!r.exc) {
							frm.reload_doc();
						}
					}
				});
			});
			frm.add_custom_button(__("Predict"), function() {
				frappe.call({
					method: "frappe_cadence.integrations.sift.predict",
					args: {
						template_doctype: frm.doc.doctype,
						template_name: frm.doc.name
					},
					callback: function(r) {
						if (!r.exc) {
							frm.reload_doc();
						}
					}
				});
			});
		}
	},
	provider: function(frm) {
		toggle_fields(frm);
	}
});

function toggle_fields(frm) {
	const is_ai = ["DSPy", "n8n"].includes(frm.doc.provider);
	frm.set_df_property("subject", "read_only", is_ai);
	frm.set_df_property("use_html", "read_only", is_ai);
	frm.set_df_property("response", "read_only", is_ai);
}
