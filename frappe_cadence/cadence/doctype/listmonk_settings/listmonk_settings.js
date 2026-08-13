frappe.ui.form.on('Listmonk Settings', {
	refresh(frm) {
		if (frm.doc.enabled && frm.doc.status === 'Authorized') {
			frm.add_custom_button(__('Bootstrap'), function() {
				frappe.confirm(
					__('Are you sure you want to sync all CRM Leads to Listmonk?'),
					function() {
						frm.call({
							method: 'bootstrap_listmonk',
							doc: frm.doc,
							callback: function(r) {
								if (r.message && r.message.status === 'success') {
									frappe.msgprint(r.message.message);
								}
							}
						});
					}
				);
			});
		}
	}
});
