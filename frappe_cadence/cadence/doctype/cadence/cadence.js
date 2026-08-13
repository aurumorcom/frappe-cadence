frappe.ui.form.on("Cadence", {
	refresh: function (frm) {
		if (frm.is_new()) {
			frm.toggle_display("cadence_code", false);
			frm.toggle_reqd("cadence_code", 0);
			frm.toggle_display("naming_series", true);
		} else {
			frm.toggle_display("naming_series", false);
			frm.add_custom_button(
				__("View Leads"),
				function () {
					frappe.route_options = { utm_source: "Cadence", utm_campaign: frm.doc.name };
					frappe.set_route("List", "CRM Lead");
				},
				"fa fa-list",
				true
			);

			if (frm.doc.listmonk_id) {
				frm.add_custom_button(
					__("Cadence Builder"),
					function () {
						frappe.db.get_doc("Listmonk Settings").then(function (settings) {
							var baseUrl = (settings.base_url || "").replace(/\/+$/, "");
							if (baseUrl) {
								window.open(baseUrl + "/admin/sequences/" + frm.doc.listmonk_id, "_blank");
							} else {
								frappe.msgprint(__("Listmonk Base URL is not configured in Listmonk Settings."));
							}
						});
					},
					null,
					true
				);
			}
		}
	},
});
