import unittest
from unittest.mock import MagicMock

from frappe_cadence.cadence.doctype.context.context import Context


class TestContextUnit(unittest.TestCase):
	def test_context_instantiation(self) -> None:
		doc = Context.__new__(Context)
		doc.reference_doctype = "CRM Lead"
		doc.reference_doc = "LEAD-001"
		doc.content = "Lead context information"
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.content, "Lead context information")
