// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Multi Channel Cadence", {
	setup: function(frm) {
		frm.set_query("reference_name", "cadence_schedules", function(doc, cdt, cdn) {
			return {
				filters: {
					include_disabled: 1
				}
			};
		});
	},
	email_cadence_for: function (frm) {
		frm.set_value("recipient", "");
	},
});
