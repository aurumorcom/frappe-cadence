from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_listmonk.jobs.subscriber import _evaluate_ast_condition, upsert_subscriber


class TestSubscriberJobUnit(FrappeTestCase):
	def test_ast_condition_evaluator(self) -> None:
		doc_dict = {"status": "Qualified", "annual_revenue": 500000}
		self.assertTrue(_evaluate_ast_condition("doc.status == 'Qualified'", doc_dict))
		self.assertTrue(_evaluate_ast_condition("doc.annual_revenue > 100000", doc_dict))
		self.assertFalse(_evaluate_ast_condition("doc.status == 'Unqualified'", doc_dict))

	@patch("frappe_listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_listmonk.client.ListmonkClient.update_subscriber")
	def test_upsert_subscriber_ast_list_enrollment(self, mock_update_sub, mock_auth) -> None:
		# Create AST List
		list_doc = frappe.get_doc(
			{
				"doctype": "List",
				"list_name": "High Revenue Leads",
				"reference_doctype": "CRM Lead",
				"enabled": 1,
				"filter_condition": "doc.annual_revenue > 250000",
			}
		).insert(ignore_permissions=True)
		list_doc.db_set("listmonk_id", 303, update_modified=False)

		# Create Lead matching condition
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "HighRev",
				"email": "highrev@example.com",
				"annual_revenue": 500000,
			}
		).insert(ignore_permissions=True)

		upsert_subscriber("CRM Lead", lead.name)

		mock_update_sub.assert_called_once()
		payload = mock_update_sub.call_args[0][1]
		self.assertIn(303, payload["lists"])

		frappe.delete_doc("CRM Lead", lead.name, force=True)
		frappe.delete_doc("List", list_doc.name, force=True)
