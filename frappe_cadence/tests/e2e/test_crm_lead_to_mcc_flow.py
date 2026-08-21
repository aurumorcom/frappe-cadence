from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.cadence.cadence import add_lead_batch_to_cadence
from frappe_cadence.cadence.doctype.crm_lead.crm_lead import (
	evaluate_cadences_for_lead,
	upsert_subscriber,
)


class TestCRMLeadToMCCFlowE2E(FrappeTestCase):
	def setUp(self) -> None:
		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "E2E Lead Trigger Cadence",
				"assign_condition": 'doc.territory == "India"',
				"enabled": 1,
				"listmonk_id": 801,
			}
		).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ListmonkClient")
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	def test_new_crm_lead_syncs_subscriber_and_triggers_mcc_creation(
		self, mock_ensure_auth, mock_client_cls
	) -> None:
		from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse

		client_inst = MagicMock()
		client_inst.create_subscriber.return_value = SubscriberResponse(
			id=444, email="trigger.lead@example.com", name="E2E Trigger Lead", status="enabled"
		)
		mock_client_cls.return_value = client_inst
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "E2E Trigger Lead",
				"lead_name": "E2E Trigger Lead",
				"email_id": "trigger.lead@example.com",
				"territory": "India",
			}
		).insert(ignore_permissions=True, ignore_links=True)

		upsert_subscriber(lead.name)
		lead.reload()
		self.assertEqual(lead.listmonk_id, 444)

		evaluate_cadences_for_lead(lead.name)
		add_lead_batch_to_cadence(self.cadence.name, [lead.name])

		mccs = frappe.get_all(
			"Multi Channel Cadence", filters={"recipient": lead.name, "cadence_name": self.cadence.name}
		)
		self.assertEqual(len(mccs), 1)
