from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.subscriber import (
	delete_subscriber,
	sync_all_crm_leads,
	upsert_subscriber,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse


class TestSubscriberInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Integration Lead",
				"email": "int_lead@example.com",
			}
		).insert(ignore_permissions=True)

	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ListmonkClient")
	def test_upsert_subscriber_db_update(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		client_inst.create_subscriber.return_value = SubscriberResponse(
			id=999,
			email="int_lead@example.com",
			name="Integration Lead",
			status="enabled",
		)
		mock_client_cls.return_value = client_inst

		sub_id = upsert_subscriber(self.lead.name)
		self.assertEqual(sub_id, 999)
		self.assertEqual(int(frappe.db.get_value("CRM Lead", self.lead.name, "listmonk_id")), 999)
