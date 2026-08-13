from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.cadence.cadence import add_lead_batch_to_cadence, evaluate_leads_for_cadence


class TestCadenceCreationToMCCFlowE2E(FrappeTestCase):
	def setUp(self) -> None:
		self.lead1 = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "E2E Lead 1",
			"lead_name": "E2E Lead Batch 1",
			"territory": "United States",
		}).insert(ignore_permissions=True, ignore_links=True)

		self.lead2 = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "E2E Lead 2",
			"lead_name": "E2E Lead Batch 2",
			"territory": "United States",
		}).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe.enqueue")
	def test_cadence_evaluation_chunks_and_creates_mcc(self, mock_enqueue) -> None:
		cadence = frappe.get_doc({
			"doctype": "Cadence",
			"cadence_name": "E2E US Cadence",
			"assign_condition": 'doc.territory == "United States"',
			"enabled": 1,
		}).insert(ignore_permissions=True, ignore_links=True)

		evaluate_leads_for_cadence(cadence.name)

		self.assertTrue(mock_enqueue.called)

		mcc_names = add_lead_batch_to_cadence(cadence.name, [self.lead1.name, self.lead2.name])
		self.assertEqual(len(mcc_names), 2)

		mccs = frappe.get_all("Multi Channel Cadence", filters={"cadence_name": cadence.name}, fields=["recipient", "status"])
		recipients = [m["recipient"] for m in mccs]
		self.assertIn(self.lead1.name, recipients)
		self.assertIn(self.lead2.name, recipients)
