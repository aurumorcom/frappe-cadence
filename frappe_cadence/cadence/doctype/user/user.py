import frappe


def on_update(doc, method: str | None = None) -> None:
	frappe.enqueue(
		"frappe_cadence.integrations.listmonk.jobs.user.get_users",
		queue="medium",
	)
