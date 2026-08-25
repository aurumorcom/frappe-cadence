import frappe

from frappe_listmonk.client import ListmonkClient, ensure_listmonk_authorized


def setup_webhook() -> None:
	ensure_listmonk_authorized()
	settings = frappe.get_doc("Listmonk Settings")
	if not settings.enabled:
		return

	client = ListmonkClient()
	site_url = frappe.utils.get_url()
	webhook_url = f"{site_url.rstrip('/')}/api/method/frappe_listmonk.jobs.webhook.handle_webhook"

	existing_webhooks = client.get_webhooks()
	target_webhook = None
	for wh in existing_webhooks:
		if isinstance(wh, dict) and wh.get("url") == webhook_url:
			target_webhook = wh
			break

	payload = {
		"name": "Frappe CRM Telemetry Webhook",
		"url": webhook_url,
		"events": ["campaign.status", "subscriber.unsubscribe", "subscriber.bounce"],
		"enabled": True,
		"secret": settings.get_webhook_secret() or "",
	}

	if target_webhook and "id" in target_webhook:
		client.update_webhook(target_webhook["id"], payload)
	else:
		client.create_webhook(payload)


@frappe.whitelist(allow_guest=True)
def handle_webhook() -> dict[str, str]:
	# Handle Listmonk telemetry callbacks
	payload = frappe.request.get_json() or {}
	frappe.logger("listmonk").info(f"Received Listmonk webhook payload: {payload}")
	return {"status": "ok"}
