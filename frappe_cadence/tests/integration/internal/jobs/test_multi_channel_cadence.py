from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.jobs.multi_channel_cadence import stop_mcc


class TestMultiChannelCadenceInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "MCC Int Lead",
				"email": "mcc_int_lead@example.com",
			}
		).insert(ignore_permissions=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "MCC Int Cadence",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
				"status": "Scheduled",
			}
		).insert(ignore_permissions=True)

	def test_stop_mcc_db(self) -> None:
		stop_mcc(self.mcc.name, reason="Replied")
		self.assertEqual(frappe.db.get_value("Multi Channel Cadence", self.mcc.name, "status"), "Replied")
