from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrmLeadInternalIntegration(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_lead_update_enqueues_jobs(self, mock_enqueue: MagicMock) -> None:
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "CRM Lead Doc",
				"email": "crm_lead_doc@example.com",
			}
		).insert(ignore_permissions=True)

		self.assertTrue(mock_enqueue.called)
