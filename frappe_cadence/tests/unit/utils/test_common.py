import unittest
from datetime import datetime

from frappe_cadence.utils.common import calculate_delay_date, clean_html, format_signature


class TestCommonUtils(unittest.TestCase):
	def test_calculate_delay_date(self) -> None:
		base = datetime(2025, 1, 1, 12, 0, 0)
		res = calculate_delay_date(3, start_date=base)
		self.assertEqual(res.day, 4)

	def test_clean_html(self) -> None:
		raw = "<p>Hello <b>World</b></p>"
		self.assertEqual(clean_html(raw), "Hello World")
		self.assertEqual(clean_html(""), "")

	def test_format_signature(self) -> None:
		sig = format_signature("Jane Doe", role="Sales Manager", company="Acme Inc")
		self.assertEqual(sig, "<b>Jane Doe</b><br>Sales Manager<br>Acme Inc")
