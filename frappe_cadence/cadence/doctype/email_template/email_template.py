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

def on_update(doc, method=None):
    doc_before_save = doc.get_doc_before_save()
    if doc_before_save and doc_before_save.status != doc.status:
        from frappe_controller.utils.controller import emit_event
        event_key = f"{doc.doctype.lower().replace(' ', '_')}_enabled"
        emit_event(
            key=event_key,
            argument={
                "doctype": doc.doctype,
                "name": doc.name,
                "enabled": 1 if doc.status == "Enabled" else 0
            }
        )
