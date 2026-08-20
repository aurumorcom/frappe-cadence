from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.subscriber import upsert_subscriber
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse
from frappe_cadence.jobs.cadence import add_lead_batch_to_cadence


class TestJourneyLeadCadenceEnrollment(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "E2E Lead Alpha",
				"email": "e2e_lead_alpha@example.com",
			}
		).insert(ignore_permissions=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "E2E Inbound Cadence",
				"assign_condition": "doc.first_name == 'E2E Lead Alpha'",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ListmonkClient")
	def test_e2e_lead_to_cadence_enrollment_journey(
		self,
		mock_client_cls: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		# Step 1: Upsert subscriber to Listmonk
		client_inst = MagicMock()
		client_inst.create_subscriber.return_value = SubscriberResponse(
			id=505,
			email="e2e_lead_alpha@example.com",
			name="E2E Lead Alpha",
			status="enabled",
		)
		mock_client_cls.return_value = client_inst

		sub_id = upsert_subscriber(self.lead.name)
		self.assertEqual(sub_id, 505)
		self.assertEqual(int(frappe.db.get_value("CRM Lead", self.lead.name, "listmonk_id")), 505)

		# Step 2: Enroll into Cadence
		mccs = add_lead_batch_to_cadence(self.cadence.name, [self.lead.name])
		self.assertTrue(len(mccs) > 0)

		mcc_doc = frappe.get_doc("Multi Channel Cadence", mccs[0])
		self.assertEqual(mcc_doc.recipient, self.lead.name)
		self.assertEqual(mcc_doc.cadence_name, self.cadence.name)
		self.assertEqual(mcc_doc.status, "Draft")
