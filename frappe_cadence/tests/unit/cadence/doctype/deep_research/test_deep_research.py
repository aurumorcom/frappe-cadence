import unittest
from unittest.mock import MagicMock

from frappe_cadence.cadence.doctype.deep_research.deep_research import DeepResearch


class TestDeepResearchUnit(unittest.TestCase):
	def test_deep_research_instantiation(self) -> None:
		doc = DeepResearch.__new__(DeepResearch)
		doc.reference_doctype = "CRM Lead"
		doc.reference_doc = "LEAD-001"
		doc.content = "Lead research information"
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.content, "Lead research information")
