import unittest
from unittest.mock import MagicMock, patch

import frappe

from frappe_cadence.cadence.doctype.user_bio.user_bio import UserBio, get_user_bio


class TestUserBioUnit(unittest.TestCase):
	def test_user_bio_permission_check(self) -> None:
		bio = UserBio({"reference_user": "user@test.local"})
		with patch("frappe.session", frappe._dict(user="user@test.local")):
			with patch("frappe.get_roles", return_value=["System Manager"]):
				self.assertTrue(bio.has_permission("read"))

	@patch("frappe.get_all")
	def test_get_user_bio_precedence(self, mock_get_all: MagicMock) -> None:
		mock_get_all.return_value = [{"content": "Cadence Bio"}]
		res = get_user_bio("user@test.local", reference_cadence="CAD-01")
		self.assertEqual(res, "Cadence Bio")
