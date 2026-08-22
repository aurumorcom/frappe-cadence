import json
from typing import Any, Optional, Union

import frappe

from frappe_cadence.integrations.listmonk.client import (
	ListmonkClient,
	ensure_listmonk_authorized,
)
from frappe_cadence.integrations.listmonk.schemas.list import (
	ListCreateRequest,
	ListUpdateRequest,
)


def upsert_campaign(cadence_name: str) -> int | None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("Cadence", cadence_name):
		return None

	cadence = frappe.get_doc("Cadence", cadence_name)
	client = ListmonkClient()

	listmonk_id = cadence.get("listmonk_id")
	if listmonk_id:
		req = ListUpdateRequest(
			name=cadence.cadence_name or cadence.name,
		)
		client.update_list(int(listmonk_id), req)
	else:
		create_req = ListCreateRequest(
			name=cadence.cadence_name or cadence.name,
			type="public",
			optin="single",
		)
		resp = client.create_list(create_req)
		listmonk_id = resp.id
		cadence.db_set("listmonk_id", listmonk_id)

	if listmonk_id:
		status_str = "active" if cadence.enabled else "paused"
		client.update_list_status(int(listmonk_id), status_str)

	return listmonk_id


def update_campaign_status(cadence_name_or_id: str | int, status: str) -> None:
	ensure_listmonk_authorized()
	client = ListmonkClient()
	if isinstance(cadence_name_or_id, int) or (
		isinstance(cadence_name_or_id, str) and cadence_name_or_id.isdigit()
	):
		client.update_list_status(int(cadence_name_or_id), status)
	else:
		listmonk_id = frappe.db.get_value("Cadence", str(cadence_name_or_id), "listmonk_id")
		if listmonk_id:
			client.update_list_status(int(listmonk_id), status)


def delete_campaign(listmonk_id: int) -> None:
	ensure_listmonk_authorized()
	client = ListmonkClient()
	client.delete_list(int(listmonk_id))


def evaluate_leads_for_cadence(cadence_name: str) -> None:
	if not frappe.db.exists("Cadence", cadence_name):
		return

	cadence = frappe.get_doc("Cadence", cadence_name)
	if not cadence.assign_condition_json or not cadence.enabled:
		return

	enrolled_leads = frappe.get_all(
		"Multi Channel Cadence",
		filters={"cadence_name": cadence_name},
		pluck="recipient",
	)

	try:
		filters = json.loads(cadence.assign_condition_json)
		if not isinstance(filters, list):
			return

		if enrolled_leads:
			filters.append(["name", "not in", enrolled_leads])

		matching_leads = frappe.get_all("CRM Lead", filters=filters, pluck="name")
		if not matching_leads:
			return

		chunk_size = 100
		for i in range(0, len(matching_leads), chunk_size):
			chunk = matching_leads[i : i + chunk_size]
			frappe.enqueue(
				"frappe_cadence.jobs.cadence.add_lead_batch_to_cadence",
				queue="medium",
				cadence_name=cadence_name,
				lead_names=chunk,
				as_child=True,
			)
	except Exception as exc:
		frappe.logger("cadence").error(f"Error evaluating leads for cadence {cadence_name}: {exc}")


def evaluate_cadences_for_lead(lead_name: str) -> None:
	cadences = frappe.get_all(
		"Cadence",
		filters={"enabled": 1},
		fields=["name", "assign_condition_json"],
	)

	for cadence in cadences:
		if cadence.get("assign_condition_json"):
			frappe.enqueue(
				"frappe_cadence.jobs.cadence.add_lead_batch_to_cadence",
				queue="high",
				cadence_name=cadence["name"],
				lead_names=[lead_name],
				as_child=True,
			)


def add_lead_batch_to_cadence(cadence_name: str, lead_names: list[str]) -> list[str]:
	if not frappe.db.exists("Cadence", cadence_name):
		return []

	cadence = frappe.get_doc("Cadence", cadence_name)
	created_mccs = []

	for lead_name in lead_names:
		if frappe.db.exists("Multi Channel Cadence", {"cadence_name": cadence_name, "recipient": lead_name}):
			continue

		try:
			sender = determine_sender(cadence)
			mcc = frappe.get_doc(
				{
					"doctype": "Multi Channel Cadence",
					"cadence_name": cadence_name,
					"cadence_for": "CRM Lead",
					"recipient": lead_name,
					"sender": sender,
					"status": "Draft",
				}
			).insert(ignore_permissions=True)
			created_mccs.append(mcc.name)
		except Exception as exc:
			frappe.logger("cadence").error(f"Failed to add lead {lead_name} to cadence {cadence_name}: {exc}")

	return created_mccs


def determine_sender(cadence: Any) -> str:
	if not getattr(cadence, "users", None):
		return getattr(cadence, "owner", None) or frappe.session.user

	user_ids = [u.user for u in cadence.users if getattr(u, "user", None)]
	if not user_ids:
		return getattr(cadence, "owner", None) or frappe.session.user

	rule = getattr(cadence, "rule", None)
	if rule == "Round Robin":
		last_user = getattr(cadence, "last_user", None)
		if not last_user or last_user not in user_ids:
			sender = user_ids[0]
		else:
			idx = user_ids.index(last_user)
			next_idx = (idx + 1) % len(user_ids)
			sender = user_ids[next_idx]

		cadence.db_set("last_user", sender)
		return sender

	elif rule == "Load Balancing":
		counts = frappe.db.sql(
			"""
			SELECT sender, COUNT(name) as cnt
			FROM `tabMulti Channel Cadence`
			WHERE sender IN %s AND docstatus != 2
			GROUP BY sender
			""",
			(tuple(user_ids),),
			as_dict=True,
		)

		user_counts = {u: 0 for u in user_ids}
		for c in counts:
			user_counts[c["sender"]] = c["cnt"]

		sender = min(user_counts, key=user_counts.get)
		return sender

	return getattr(cadence, "owner", None) or frappe.session.user
