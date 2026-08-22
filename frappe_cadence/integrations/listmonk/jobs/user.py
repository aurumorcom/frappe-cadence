from typing import Any

import frappe

from frappe_cadence.integrations.listmonk.client import (
	ListmonkClient,
	ensure_listmonk_authorized,
)


def get_users() -> dict[str, Any]:
	ensure_listmonk_authorized()

	users = frappe.get_all(
		"User",
		filters={"enabled": 1},
		fields=["name", "email", "listmonk_id"],
	)

	client = ListmonkClient()
	listmonk_users = client.get_listmonk_users()

	lm_user_map: dict[str, int] = {}
	for lm_user in listmonk_users:
		if isinstance(lm_user, dict) and lm_user.get("email") and lm_user.get("id"):
			lm_user_map[str(lm_user["email"]).lower().strip()] = int(lm_user["id"])

	updated_count = 0
	for u in users:
		email = (u.get("email") or u.get("name") or "").lower().strip()
		if not email:
			continue

		user_name = u.get("name") if isinstance(u, dict) else getattr(u, "name", None)
		lm_id = lm_user_map.get(email)
		if lm_id and u.get("listmonk_id") != lm_id and user_name:
			frappe.db.set_value("User", user_name, "listmonk_id", lm_id)
			updated_count += 1

	return {"status": "success", "updated": updated_count}
