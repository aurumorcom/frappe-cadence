from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCadenceInternalIntegration(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_cadence_lifecycle(self, mock_enqueue: MagicMock) -> None:
		cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "Test Cadence Doc",
				"assign_condition": "doc.first_name == 'Lead'",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(cadence.assign_condition_json, '[["first_name", "=", "Lead"]]')
		self.assertTrue(mock_enqueue.called)
