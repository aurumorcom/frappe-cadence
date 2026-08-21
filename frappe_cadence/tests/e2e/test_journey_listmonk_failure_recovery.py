from unittest.mock import MagicMock, patch

import frappe
import requests
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.subscriber import upsert_subscriber


class TestJourneyListmonkFailureRecovery(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Failure Lead",
				"email": "failure_lead@example.com",
				"email_id": "failure_lead@example.com",
			}
		).insert(ignore_permissions=True)

	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.client.requests.request")
	def test_e2e_transient_error_bubbles_for_retry(self, mock_req: MagicMock, mock_auth: MagicMock) -> None:
		# Simulate HTTP 500 transient failure from Listmonk
		mock_resp = MagicMock()
		mock_resp.status_code = 500
		mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
		mock_req.return_value = mock_resp

		with self.assertRaises(requests.exceptions.HTTPError):
			upsert_subscriber(self.lead.name)

		# Verify lead listmonk_id is NOT corrupted or set
		listmonk_id = frappe.db.get_value("CRM Lead", self.lead.name, "listmonk_id")
		self.assertTrue(listmonk_id is None or listmonk_id == 0 or listmonk_id == "")
