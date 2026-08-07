import frappe

def before_save(doc, method=None):
	if doc.has_value_changed("enabled"):
		doc.status = "Enabled" if doc.enabled else "Disabled"
	elif doc.has_value_changed("status"):
		if doc.status == "Disabled":
			doc.enabled = 0
		elif doc.status == "Enabled":
			doc.enabled = 1
	elif doc.status not in ["Optimizing", "Predicting"]:
		doc.status = "Enabled" if doc.enabled else "Disabled"

