import frappe


def on_update(doc, method=None):
	"""
	On Communication update, if referenced to Multi Channel Cadence,
	log or update relevant tracking metrics if needed.
	"""
	try:
		reference_doctype = getattr(doc, "reference_doctype", None)
		reference_name = getattr(doc, "reference_name", None)

		if reference_doctype != "Multi Channel Cadence" or not reference_name:
			return

		mcc_name = reference_name
		if not frappe.db.exists("Multi Channel Cadence", mcc_name):
			return

		mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
		if mcc.status == "Scheduled":
			mcc.db_set("status", "In Progress")
	except Exception as e:
		frappe.log_error(title="Failed to update MCC status on communication update", message=str(e))
