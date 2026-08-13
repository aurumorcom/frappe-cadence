from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.contact import (
	delete_contact,
	sync_all_crm_leads,
	upsert_contact,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse


class TestContactInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Integration Lead",
				"email": "int_lead@example.com",
			}
		).insert(ignore_permissions=True)

	@patch("frappe_cadence.integrations.listmonk.jobs.contact.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.contact.ListmonkClient")
	def test_upsert_contact_db_update(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		client_inst.create_subscriber.return_value = SubscriberResponse(
			id=999,
			email="int_lead@example.com",
			name="Integration Lead",
			status="enabled",
		)
		mock_client_cls.return_value = client_inst

		sub_id = upsert_contact(self.lead.name)
		self.assertEqual(sub_id, 999)
		self.assertEqual(int(frappe.db.get_value("CRM Lead", self.lead.name, "listmonk_id")), 999)
