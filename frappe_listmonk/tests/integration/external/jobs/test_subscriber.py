import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSubscriberJobExternal(FrappeTestCase):
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
	def test_two_step_callback_protocol(self, mock_update_sub, mock_update_cs) -> None:
		from frappe_listmonk.jobs.subscriber import update_subscriber_campaign_subscriber

		# Setup Rule
		rule = frappe.get_doc(
			{
				"doctype": "Deep Research Rule",
				"rule_name": "CTO Research Rule",
				"reference_doctype": "CRM Lead",
				"filter_condition": "doc.first_name == 'Jane'",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		# Setup Lead
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Jane",
				"last_name": "Doe",
				"email": "cto.jane@example.com",
			}
		).insert(ignore_permissions=True)

		# Setup Playbook Execution
		execution = frappe.get_doc(
			{
				"doctype": "Playbook Execution",
				"playbook": rule.reference_playbook,
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
				"status": "success",
				"execution_data": json.dumps(
					{
						"subscriber_id": 100,
						"campaign_id": 42,
						"rule_name": rule.name,
					}
				),
			}
		).insert(ignore_permissions=True)

		update_subscriber_campaign_subscriber(execution.name)

		# Assert Call 1: PATCH /api/subscribers/100
		mock_update_sub.assert_called_once()
		sub_id, payload = mock_update_sub.call_args[0][0], mock_update_sub.call_args[0][1]
		self.assertEqual(sub_id, 100)
		self.assertEqual(payload["crm_id"], lead.name)
		self.assertIn("deep_research", payload["attribs"])
		self.assertEqual(payload["attribs"]["first_name"], "Jane")

		# Assert Call 2: POST /api/campaigns/42/subscribers/100 status = scheduled
		mock_update_cs.assert_called_once_with(42, 100, status="scheduled")

		# Cleanup
		frappe.delete_doc("Playbook Execution", execution.name, force=True)
		frappe.delete_doc("CRM Lead", lead.name, force=True)
		frappe.delete_doc("Deep Research Rule", rule.name, force=True)
