from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeepResearchFlow(FrappeTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.db.sql(
			"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Listmonk Settings', 'Deep Research', 'Deep Research Rule', 'List', 'CRM Lead List', 'CRM Organization List')"
		)
		frappe.db.commit()
		frappe.clear_cache()

	def setUp(self) -> None:
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.status = "Authorized"
		settings.base_url = "http://localhost:9000"
		settings.access_token = "test_token"
		settings.save(ignore_permissions=True)
		frappe.db.set_single_value("Listmonk Settings", "status", "Authorized")

	@patch("frappe_listmonk.client.ListmonkClient.update_campaign_subscriber")
	@patch("frappe_listmonk.client.ListmonkClient.update_subscriber")
	def test_e2e_deep_research_dispatch_and_callback(self, mock_update_sub, mock_update_cs) -> None:
		from frappe_listmonk.deep_research import get as deep_research_get
		from frappe_listmonk.jobs.subscriber import (
			process_deep_research_request,
			update_subscriber_campaign_subscriber,
		)

		# 1. Setup Rule
		rule = frappe.get_doc(
			{
				"doctype": "Deep Research Rule",
				"rule_name": "Executive Deep Research Rule",
				"reference_doctype": "CRM Lead",
				"filter_condition": "doc.first_name == 'Alice'",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		# 2. Setup Lead
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Alice",
				"last_name": "VP",
				"email": "alice.vp@example.com",
			}
		).insert(ignore_permissions=True)

		# 3. Simulate Listmonk POST request to whitelisted endpoint
		payload = {
			"campaign_subscriber": {
				"campaign_id": 42,
				"subscriber_id": 100,
				"email_id": 5,
				"from_address": "sales@example.com",
				"status": "waiting",
				"current_step": 0,
			},
			"subscriber": {
				"id": 100,
				"email": "alice.vp@example.com",
				"name": "Alice VP",
				"crm_id": lead.name,
			},
			"campaign_id": 42,
		}

		frappe.request = frappe._dict({"get_json": lambda: payload})
		res = deep_research_get()
		self.assertEqual(res["status"], "queued")

		# 4. Process deep research request
		process_deep_research_request(100, 42, lead.name)

		# Verify Playbook Execution created
		execution_name = frappe.db.get_value("Playbook Execution", {"reference_name": lead.name}, "name")
		self.assertIsNotNone(execution_name)

		execution = frappe.get_doc("Playbook Execution", execution_name)
		execution.status = "success"
		execution.output_data = "AI Analysis: Highly qualified prospect"
		execution.save(ignore_permissions=True)

		# 5. Trigger completion callback
		update_subscriber_campaign_subscriber(execution.name)

		# Assert Two-Step Callback Execution
		mock_update_sub.assert_called()
		mock_update_cs.assert_called_with(42, 100, status="scheduled")

		# Assert Deep Research record created
		dr_name = frappe.db.get_value(
			"Deep Research", {"reference_doc": lead.name, "rule": rule.name}, "name"
		)
		self.assertIsNotNone(dr_name)

		# Cleanup
		frappe.delete_doc("Deep Research", dr_name, force=True)
		frappe.delete_doc("Playbook Execution", execution.name, force=True)
		frappe.delete_doc("CRM Lead", lead.name, force=True)
		frappe.delete_doc("Deep Research Rule", rule.name, force=True)
