from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.jobs.cadence import add_lead_batch_to_cadence


class TestCadenceInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "Test Cadence Enrollment",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Enroll Lead",
				"email": "enroll_lead@example.com",
			}
		).insert(ignore_permissions=True)

	def test_add_lead_batch_to_cadence_db(self) -> None:
		frappe.db.delete(
			"Multi Channel Cadence", {"cadence_name": self.cadence.name, "recipient": self.lead.name}
		)
		mcc_names = add_lead_batch_to_cadence(self.cadence.name, [self.lead.name])
		self.assertTrue(len(mcc_names) > 0)
		mcc = frappe.get_doc("Multi Channel Cadence", mcc_names[0])
		self.assertEqual(mcc.recipient, self.lead.name)
		self.assertEqual(mcc.cadence_name, self.cadence.name)
		self.assertEqual(mcc.status, "Draft")
