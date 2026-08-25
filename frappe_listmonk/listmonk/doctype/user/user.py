import frappe


def on_update(doc, method: str | None = None) -> None:
	if not doc.name:
		return
	frappe.enqueue(
		"frappe_listmonk.jobs.user.update_user",
		queue="medium",
		user_name=doc.name,
		enqueue_after_commit=True,
	)
