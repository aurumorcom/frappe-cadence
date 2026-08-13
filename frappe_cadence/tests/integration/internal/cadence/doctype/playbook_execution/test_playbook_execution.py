from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPlaybookExecutionInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "PE Doc Lead",
				"email": "pe_doc_lead@example.com",
			}
		).insert(ignore_permissions=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "PE Doc Cadence",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	@patch("frappe.enqueue")
	def test_pe_status_update_enqueues(self, mock_enqueue: MagicMock) -> None:
		frappe.get_doc(
			{
				"doctype": "Playbook Execution",
				"playbook": self.cadence.reference_playbook or self.cadence.name,
				"multi_channel_cadence": self.mcc.name,
				"status": "success",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(
			frappe.db.get_value("Multi Channel Cadence", self.mcc.name, "status"), "Provisioning"
		)
		mock_enqueue.assert_called_once()
