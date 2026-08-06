frappe.ui.form.on("Email Template", {
	refresh: function(frm) {
		toggle_fields(frm);
		const is_n8n_provider = frm.doc.provider === "n8n";
		const is_dspy_provider = frm.doc.provider === "DSPy";

		if (is_n8n_provider || is_dspy_provider) {
			frm.add_custom_button(__("Optimize"), function() {
				const method = is_n8n_provider
					? "frappe_cadence.integrations.n8n.optimize"
					: "frappe_cadence.integrations.sift.optimize";
				frappe.call({
					method: method,
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
				const method = is_n8n_provider
					? "frappe_cadence.integrations.n8n.predict"
					: "frappe_cadence.integrations.sift.predict";
				frappe.call({
					method: method,
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
	frm.set_df_property("subject", "read_only", 0);
	frm.set_df_property("use_html", "read_only", 0);
	frm.set_df_property("response", "read_only", 0);
	frm.set_df_property("status", "read_only", 1);
	frm.set_df_property("status", "hidden", 1);

	if (frm.doc.status) {
		const indicator_map = {
			"Enabled": "green",
			"Disabled": "red",
			"Optimizing": "orange",
			"Predicting": "blue"
		};
		frm.page.set_indicator(frm.doc.status, indicator_map[frm.doc.status] || "grey");
	}
}
