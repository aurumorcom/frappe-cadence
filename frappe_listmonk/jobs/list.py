import frappe

from frappe_listmonk.client import ListmonkClient, ensure_listmonk_authorized


def sync_all_lists() -> None:
	ensure_listmonk_authorized()
	lists = frappe.get_all("List", filters={"enabled": 1}, fields=["name"])
	for l in lists:
		frappe.enqueue(
			"frappe_listmonk.jobs.list.upsert_list",
			queue="medium",
			list_name=l.name,
		)


def upsert_list(list_name: str) -> None:
	ensure_listmonk_authorized()
	if not frappe.db.exists("List", list_name):
		return

	doc = frappe.get_doc("List", list_name)
	if not doc.enabled:
		return

	payload = {
		"name": doc.list_name or doc.name,
		"crm_id": doc.name,
		"type": "private",
		"optin": "single",
	}

	client = ListmonkClient()
	if doc.listmonk_id:
		res = client.update_list(doc.listmonk_id, payload)
	else:
		# Check if already exists on Listmonk
		existing = client.find_list_by_name(doc.list_name or doc.name)
		if existing and "id" in existing:
			doc.db_set("listmonk_id", existing["id"], update_modified=False)
			res = client.update_list(existing["id"], payload)
		else:
			res = client.create_list(payload)

	if hasattr(res, "id") and res.id:
		doc.db_set("listmonk_id", res.id, update_modified=False)


def delete_list(list_name: str, listmonk_id: int | None = None) -> None:
	ensure_listmonk_authorized()
	if not listmonk_id:
		return
	client = ListmonkClient()
	client.delete_list(listmonk_id)


def evaluate_doc_for_list(reference_doctype: str, reference_name: str) -> None:
	# Trigger subscriber upsert which collects active lists and syncs to Listmonk
	frappe.enqueue(
		"frappe_listmonk.jobs.subscriber.upsert_subscriber",
		queue="high",
		reference_doctype=reference_doctype,
		reference_name=reference_name,
	)
