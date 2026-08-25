import frappe


def on_update(doc, method: str | None = None) -> None:
	if not doc.name:
		return
	frappe.enqueue(
		"frappe_listmonk.jobs.list.evaluate_doc_for_list",
		queue="high",
		reference_doctype="CRM Lead",
		reference_name=doc.name,
		enqueue_after_commit=True,
	)
	frappe.enqueue(
		"frappe_listmonk.jobs.subscriber.upsert_subscriber",
		queue="high",
		reference_doctype="CRM Lead",
		reference_name=doc.name,
		enqueue_after_commit=True,
	)


def on_trash(doc, method: str | None = None) -> None:
	listmonk_id = doc.get("listmonk_id")
	if listmonk_id:
		frappe.enqueue(
			"frappe_listmonk.jobs.subscriber.delete_subscriber",
			queue="high",
			listmonk_id=int(listmonk_id),
			enqueue_after_commit=True,
		)
