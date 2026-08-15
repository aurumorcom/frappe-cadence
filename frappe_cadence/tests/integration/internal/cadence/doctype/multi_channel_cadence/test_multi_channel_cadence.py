from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMultiChannelCadenceInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "MCC Doc Cadence",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "MCC Doc Lead",
				"email": "mcc_doc_lead@example.com",
			}
		).insert(ignore_permissions=True)

	def test_mcc_creation_defaults(self) -> None:
		mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(mcc.status, "Draft")
