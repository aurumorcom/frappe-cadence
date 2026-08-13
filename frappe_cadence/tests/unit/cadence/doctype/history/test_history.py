import unittest

from frappe_cadence.cadence.doctype.history.history import History


class TestHistoryUnit(unittest.TestCase):
	def test_history_instantiation(self) -> None:
		doc = History.__new__(History)
		doc.cadence_name = "CAD-001"
		doc.recipient = "LEAD-001"
		self.assertEqual(doc.cadence_name, "CAD-001")
		self.assertEqual(doc.recipient, "LEAD-001")
