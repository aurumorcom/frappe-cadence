import unittest

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeepResearchRule(FrappeTestCase):
	def test_ast_rule_matching(self) -> None:
		from frappe_listmonk.jobs.subscriber import _evaluate_ast_condition

		doc_dict = {"designation": "CTO", "company": "Acme Corp"}
		condition_pass = "doc.designation in ['CTO', 'VP Engineering']"
		condition_fail = "doc.designation == 'Manager'"

		self.assertTrue(_evaluate_ast_condition(condition_pass, doc_dict))
		self.assertFalse(_evaluate_ast_condition(condition_fail, doc_dict))
