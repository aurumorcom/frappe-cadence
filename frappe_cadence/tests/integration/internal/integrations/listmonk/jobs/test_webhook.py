from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.webhook import process_webhook_payload


class TestWebhookInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "WH Lead",
				"email": "wh_lead@example.com",
			}
		).insert(ignore_permissions=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "WH Cadence",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
				"status": "Scheduled",
				"listmonk_subscriber_id": 8888,
				"listmonk_campaign_id": 7777,
			}
		).insert(ignore_permissions=True)

	def test_process_webhook_payload_updates_db(self) -> None:
		payload = {
			"event": "campaign.step_executed",
			"data": {
				"subscriber_id": 8888,
				"campaign_id": 7777,
				"status": "step_executed",
				"email": "wh_lead@example.com",
			},
		}

		res = process_webhook_payload(payload)
		self.assertEqual(res["status"], "ok")
		self.assertEqual(frappe.db.get_value("Multi Channel Cadence", self.mcc.name, "status"), "In Progress")
