from typing import Optional

import frappe
from frappe.model.document import Document


class PlaybookExecution(Document):
	def on_update(self) -> None:
		on_update(self)


def on_update(doc, method: str | None = None) -> None:
	mcc_name = (
		getattr(doc, "multi_channel_cadence", None)
		or (doc.get("multi_channel_cadence") if hasattr(doc, "get") else None)
		or getattr(doc, "reference_name", None)
		or (doc.get("reference_name") if hasattr(doc, "get") else None)
	)
	if not mcc_name or not frappe.db.exists("Multi Channel Cadence", mcc_name):
		return

	mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)

	status_val = getattr(doc, "status", "") or (doc.get("status") if hasattr(doc, "get") else "") or ""
	status = str(status_val).lower()
	if status in ["running"]:
		mcc.db_set("status", "Enriching")
	elif status in ["completed", "success"]:
		mcc.db_set("status", "Provisioning")
		frappe.enqueue(
			"frappe_cadence.jobs.multi_channel_cadence.add_subscriber_to_sequence",
			queue="high",
			mcc_name=mcc.name,
		)
	elif status in ["failed", "error", "canceled"]:
		mcc.db_set("status", "Failed")
