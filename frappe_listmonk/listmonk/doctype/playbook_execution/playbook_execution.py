import frappe
from frappe.model.document import Document


class PlaybookExecution(Document):
	def on_update(self) -> None:
		on_update(self)


def on_update(doc, method: str | None = None) -> None:
	status_val = getattr(doc, "status", "") or (doc.get("status") if hasattr(doc, "get") else "") or ""
	status = str(status_val).lower()

	if status in ["success", "completed"]:
		frappe.enqueue(
			"frappe_listmonk.jobs.subscriber.update_subscriber_campaign_subscriber",
			queue="high",
			playbook_execution_name=doc.name,
			enqueue_after_commit=True,
		)
