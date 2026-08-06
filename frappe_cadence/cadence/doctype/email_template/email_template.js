frappe.ui.form.on("Email Template", {
	refresh: function(frm) {
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
});
