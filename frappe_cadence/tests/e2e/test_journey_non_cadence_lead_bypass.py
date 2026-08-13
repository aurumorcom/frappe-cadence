from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.jobs.cadence import evaluate_leads_for_cadence


class TestJourneyNonCadenceLeadBypass(FrappeTestCase):
	def setUp(self) -> None:
		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "Enterprise Only Cadence",
				"assign_condition": "doc.first_name == 'Enterprise Lead'",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Standard Lead",
				"email": "standard_lead@example.com",
			}
		).insert(ignore_permissions=True)

	@patch("frappe.enqueue")
	def test_unmatched_lead_bypasses_enrollment(self, mock_enqueue: MagicMock) -> None:
		evaluate_leads_for_cadence(self.cadence.name)
		mock_enqueue.assert_not_called()
