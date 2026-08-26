import frappe

from frappe_listmonk.client import ListmonkClient, ensure_listmonk_authorized


def sync_all_crm_users() -> None:
	ensure_listmonk_authorized()
	client = ListmonkClient()
	listmonk_users = client.get_listmonk_users()

	# Map Listmonk user IDs to active Frappe CRM Users by email match
	crm_users = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "email"])
	user_map = {u.email.lower(): u.name for u in crm_users if u.get("email")}

	for lm_user in listmonk_users:
		if not isinstance(lm_user, dict):
			continue
		email = (lm_user.get("email") or "").lower()
		lm_id = lm_user.get("id")
		if email in user_map and lm_id:
			frappe.db.set_value("User", user_map[email], "listmonk_id", lm_id, update_modified=False)


def update_user(user_name: str) -> None:
	ensure_listmonk_authorized()
	if not frappe.db.exists("User", user_name):
		return

	doc = frappe.get_doc("User", user_name)
	if not doc.enabled or not doc.email:
		return

	client = ListmonkClient()
	listmonk_users = client.get_listmonk_users()

	for lm_user in listmonk_users:
		if isinstance(lm_user, dict) and (lm_user.get("email") or "").lower() == doc.email.lower():
			lm_id = lm_user.get("id")
			if lm_id:
				doc.db_set("listmonk_id", lm_id, update_modified=False)
			break
