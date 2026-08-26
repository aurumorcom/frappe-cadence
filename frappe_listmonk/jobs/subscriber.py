import ast
import json
from typing import Any, Optional

import frappe
from frappe import _

from frappe_listmonk.client import ListmonkClient, ensure_listmonk_authorized


def _evaluate_ast_condition(condition_str: str, doc_dict: dict[str, Any]) -> bool:
	if not condition_str or not condition_str.strip():
		return True
	try:
		# Expose doc and frappe utilities in safe environment
		eval_globals = {
			"doc": frappe._dict(doc_dict),
			"today": frappe.utils.today,
			"now": frappe.utils.now,
			"cint": frappe.utils.cint,
			"flt": frappe.utils.flt,
		}
		return bool(frappe.safe_eval(condition_str, eval_globals))
	except Exception as exc:
		frappe.logger("listmonk").warning(f"AST condition evaluation error: {exc}")
		return False


def sync_all_subscribers() -> None:
	ensure_listmonk_authorized()
	# Sync Leads
	leads = frappe.get_all("CRM Lead", fields=["name"])
	for lead in leads:
		frappe.enqueue(
			"frappe_listmonk.jobs.subscriber.upsert_subscriber",
			queue="long",
			reference_doctype="CRM Lead",
			reference_name=lead.name,
		)

	# Sync Organizations
	orgs = frappe.get_all("CRM Organization", fields=["name"])
	for org in orgs:
		frappe.enqueue(
			"frappe_listmonk.jobs.subscriber.upsert_subscriber",
			queue="long",
			reference_doctype="CRM Organization",
			reference_name=org.name,
		)


def upsert_subscriber(reference_doctype: str, reference_name: str) -> None:
	ensure_listmonk_authorized()
	if not frappe.db.exists(reference_doctype, reference_name):
		return

	doc = frappe.get_doc(reference_doctype, reference_name)
	doc_dict = doc.as_dict()

	email = doc_dict.get("email") or doc_dict.get("email_id") or doc_dict.get("primary_email")
	if not email:
		return

	name = doc_dict.get("lead_name") or doc_dict.get("organization_name") or doc_dict.get("name") or email
	phone = doc_dict.get("phone") or doc_dict.get("mobile_no") or doc_dict.get("phone_number")

	# Gather Listmonk list IDs via AST filter condition evaluation and manual child table
	list_ids: list[int] = []

	enabled_lists = frappe.get_all(
		"List",
		filters={"enabled": 1, "reference_doctype": reference_doctype},
		fields=["name", "listmonk_id", "filter_condition"],
	)
	for l_doc in enabled_lists:
		lm_id = l_doc.get("listmonk_id")
		if not lm_id:
			continue
		cond = l_doc.get("filter_condition")
		if cond and cond.strip():
			if _evaluate_ast_condition(cond, doc_dict):
				if int(lm_id) not in list_ids:
					list_ids.append(int(lm_id))

	child_table_field = "crm_lead_list" if reference_doctype == "CRM Lead" else "crm_organization_list"
	lists_child = doc_dict.get(child_table_field) or []

	for row in lists_child:
		list_name = row.get("list")
		if list_name and frappe.db.exists("List", list_name):
			list_doc = frappe.get_doc("List", list_name)
			if list_doc.enabled and list_doc.listmonk_id:
				if int(list_doc.listmonk_id) not in list_ids:
					list_ids.append(int(list_doc.listmonk_id))

	# Query latest Deep Research for this entity if available
	deep_research_data = None
	deep_research_name = frappe.db.get_value(
		"Deep Research",
		{"reference_doctype": reference_doctype, "reference_doc": reference_name},
		"name",
		order_by="creation desc",
	)
	if deep_research_name:
		dr_doc = frappe.get_doc("Deep Research", deep_research_name)
		deep_research_data = dr_doc.as_dict()

	# Construct flat attribs (entity fields + deep_research object, NO user object)
	clean_entity_dict = {
		k: (v.isoformat() if hasattr(v, "isoformat") else v)
		for k, v in doc_dict.items()
		if not isinstance(v, (list, dict)) and k not in ["password", "api_secret"]
	}
	attribs = {**clean_entity_dict}
	if deep_research_data:
		attribs["deep_research"] = deep_research_data

	payload = {
		"email": str(email),
		"name": str(name),
		"phone": str(phone) if phone else None,
		"crm_id": str(reference_name),
		"status": "enabled",
		"lists": list_ids,
		"attribs": attribs,
	}

	client = ListmonkClient()
	listmonk_id = doc_dict.get("listmonk_id")
	if listmonk_id:
		res = client.update_subscriber(int(listmonk_id), payload, method="PATCH")
	else:
		res = client.create_subscriber(payload)

	if hasattr(res, "id") and res.id:
		frappe.db.set_value(reference_doctype, reference_name, "listmonk_id", res.id, update_modified=False)


def delete_subscriber(listmonk_id: int) -> None:
	ensure_listmonk_authorized()
	client = ListmonkClient()
	client.delete_subscriber(listmonk_id)


def process_deep_research_request(subscriber_id: int, campaign_id: int, crm_id: str) -> None:
	ensure_listmonk_authorized()

	reference_doctype = "CRM Lead"
	if frappe.db.exists("CRM Organization", crm_id):
		reference_doctype = "CRM Organization"
	elif not frappe.db.exists("CRM Lead", crm_id):
		frappe.logger("listmonk").error(f"Target crm_id '{crm_id}' not found in CRM Lead or CRM Organization")
		return

	target_doc = frappe.get_doc(reference_doctype, crm_id)
	doc_dict = target_doc.as_dict()

	rules = frappe.get_all(
		"Deep Research Rule",
		filters={"reference_doctype": reference_doctype},
		fields=["name", "filter_condition", "reference_playbook", "enabled", "priority"],
		order_by="priority asc",
	)

	matched_rule = None
	for rule in rules:
		condition = rule.get("filter_condition")
		if _evaluate_ast_condition(condition, doc_dict):
			matched_rule = rule
			break

	if not matched_rule:
		frappe.logger("listmonk").warning(f"No matching Deep Research Rule for {reference_doctype} {crm_id}")
		return

	# Handle disabled rule deferral
	if not matched_rule.get("enabled"):
		if getattr(frappe.flags, "current_job_id", None):
			frappe.wait_for(
				"on_update",
				filters={"doctype": "Deep Research Rule", "name": matched_rule.name, "enabled": 1},
			)
		else:
			frappe.wait_for(
				event_key=f"Deep Research Rule:on_update:{matched_rule.name}",
				condition="argument.get('enabled') == 1",
			)

	# Trigger Playbook Execution
	playbook_name = matched_rule.reference_playbook
	if not playbook_name or not frappe.db.exists("Playbook", playbook_name):
		frappe.logger("listmonk").error(
			f"Playbook '{playbook_name}' referenced by Rule '{matched_rule.name}' does not exist"
		)
		return

	execution = frappe.get_doc(
		{
			"doctype": "Playbook Execution",
			"playbook": playbook_name,
			"reference_doctype": reference_doctype,
			"reference_name": crm_id,
			"status": "running",
			"execution_data": json.dumps(
				{
					"subscriber_id": subscriber_id,
					"campaign_id": campaign_id,
					"rule_name": matched_rule.name,
				}
			),
		}
	)
	execution.insert(ignore_permissions=True)


def update_subscriber_campaign_subscriber(playbook_execution_name: str) -> None:
	ensure_listmonk_authorized()
	if not frappe.db.exists("Playbook Execution", playbook_execution_name):
		return

	execution = frappe.get_doc("Playbook Execution", playbook_execution_name)
	crm_id = execution.reference_name
	if not crm_id:
		return

	reference_doctype = execution.reference_doctype or (
		"CRM Organization" if frappe.db.exists("CRM Organization", crm_id) else "CRM Lead"
	)

	exec_data = {}
	if execution.execution_data:
		try:
			exec_data = (
				json.loads(execution.execution_data)
				if isinstance(execution.execution_data, str)
				else execution.execution_data
			)
		except Exception:
			pass

	subscriber_id = exec_data.get("subscriber_id")
	campaign_id = exec_data.get("campaign_id")
	rule_name = exec_data.get("rule_name")

	if not subscriber_id or not campaign_id:
		frappe.logger("listmonk").error(
			f"Missing subscriber_id or campaign_id in Playbook Execution {playbook_execution_name}"
		)
		return

	# Save/update Deep Research document
	output_content = str(getattr(execution, "output_data", "") or getattr(execution, "content", "") or "")
	research_doc = frappe.get_doc(
		{
			"doctype": "Deep Research",
			"reference_doctype": reference_doctype,
			"reference_doc": crm_id,
			"rule": rule_name,
			"summary": output_content,
		}
	)
	research_doc.insert(ignore_permissions=True)

	# Fetch latest Deep Research record matching BOTH crm_id and specific Rule
	latest_research = frappe.get_doc(
		"Deep Research",
		frappe.db.get_value(
			"Deep Research",
			{"reference_doctype": reference_doctype, "reference_doc": crm_id, "rule": rule_name},
			"name",
			order_by="creation desc",
		),
	)

	# Fetch entity doc for flat attribs construction
	target_doc = frappe.get_doc(reference_doctype, crm_id)
	doc_dict = target_doc.as_dict()
	clean_entity_dict = {
		k: (v.isoformat() if hasattr(v, "isoformat") else v)
		for k, v in doc_dict.items()
		if not isinstance(v, (list, dict)) and k not in ["password", "api_secret"]
	}
	attribs = {**clean_entity_dict, "deep_research": latest_research.as_dict()}

	client = ListmonkClient()
	# Call 1: Update subscriber attributes via PATCH /api/subscribers/:subscriber_id
	client.update_subscriber(int(subscriber_id), {"crm_id": crm_id, "attribs": attribs}, method="PATCH")

	# Call 2: Signal sequence completion via POST /api/campaigns/:campaign_id/subscribers/:subscriber_id
	client.update_campaign_subscriber(int(campaign_id), int(subscriber_id), status="scheduled")
