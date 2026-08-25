from typing import Any

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get() -> dict[str, Any]:
	payload = frappe.request.get_json() or {}

	cs_dict = payload.get("campaign_subscriber") or {}
	sub_dict = payload.get("subscriber") or {}

	campaign_id = cs_dict.get("campaign_id") or payload.get("campaign_id")
	subscriber_id = cs_dict.get("subscriber_id") or sub_dict.get("id")
	crm_id = sub_dict.get("crm_id") or payload.get("crm_id")

	if not crm_id:
		# Fallback: find Lead or Organization by email
		sub_email = sub_dict.get("email")
		if sub_email:
			crm_id = frappe.db.get_value("CRM Lead", {"email": sub_email}, "name") or frappe.db.get_value(
				"CRM Organization", {"email": sub_email}, "name"
			)

	if not campaign_id or not subscriber_id or not crm_id:
		frappe.logger("listmonk").error(
			f"Deep Research endpoint received incomplete payload: campaign_id={campaign_id}, subscriber_id={subscriber_id}, crm_id={crm_id}"
		)
		return {"status": "error", "message": _("Incomplete payload parameters.")}

	frappe.enqueue(
		"frappe_listmonk.jobs.subscriber.process_deep_research_request",
		queue="high",
		subscriber_id=int(subscriber_id),
		campaign_id=int(campaign_id),
		crm_id=str(crm_id),
		enqueue_after_commit=True,
	)

	return {"status": "queued", "message": _("Deep research request enqueued successfully.")}
