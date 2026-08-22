from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.playbook_execution.playbook_execution import on_update
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse
from frappe_cadence.jobs.multi_channel_cadence import add_subscriber_to_campaign


class TestJourneyPlaybookEnrollment(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "PB Journey Lead",
				"email": "pb_lead@example.com",
			}
		).insert(ignore_permissions=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "PB Journey Cadence",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		self.cadence.db_set("listmonk_id", 101)
		self.cadence.reload()

		self.mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	@patch("frappe_cadence.jobs.multi_channel_cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.multi_channel_cadence.ListmonkClient")
	def test_e2e_playbook_execution_to_provisioning(
		self, mock_client_cls: MagicMock, mock_auth: MagicMock
	) -> None:
		client_inst = MagicMock()
		client_inst.update_subscriber.return_value = SubscriberResponse(
			id=303,
			email="pb_lead@example.com",
			name="PB Journey Lead",
			status="enabled",
		)
		mock_client_cls.return_value = client_inst

		# Playbook execution completes
		pe = frappe.get_doc(
			{
				"doctype": "Playbook Execution",
				"playbook": self.cadence.reference_playbook or self.cadence.name,
				"multi_channel_cadence": self.mcc.name,
				"status": "success",
			}
		).insert(ignore_permissions=True)

		on_update(pe)
		self.assertEqual(
			frappe.db.get_value("Multi Channel Cadence", self.mcc.name, "status"), "Provisioning"
		)

		# Provisioning step runs
		self.lead.db_set("listmonk_id", 303)
		add_subscriber_to_campaign(self.mcc.name)
		self.assertEqual(frappe.db.get_value("Multi Channel Cadence", self.mcc.name, "status"), "Scheduled")
