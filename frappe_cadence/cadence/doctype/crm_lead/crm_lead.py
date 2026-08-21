import json
from typing import Optional

import frappe

from frappe_cadence.integrations.listmonk.jobs.subscriber import (
	delete_subscriber,
	upsert_subscriber,
)
from frappe_cadence.jobs.cadence import evaluate_cadences_for_lead


def on_update(doc, method: str | None = None) -> None:
	if not doc.name:
		return
	frappe.enqueue(
		"frappe_cadence.integrations.listmonk.jobs.subscriber.upsert_subscriber",
		queue="high",
		lead_name=doc.name,
	)
	frappe.enqueue(
		"frappe_cadence.jobs.cadence.evaluate_cadences_for_lead",
		queue="high",
		lead_name=doc.name,
	)


def on_trash(doc, method: str | None = None) -> None:
	listmonk_id = doc.get("listmonk_id")
	if listmonk_id:
		frappe.enqueue(
			"frappe_cadence.integrations.listmonk.jobs.subscriber.delete_subscriber",
			queue="high",
			listmonk_id=int(listmonk_id),
		)
