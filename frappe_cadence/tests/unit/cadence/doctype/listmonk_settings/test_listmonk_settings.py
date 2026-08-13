import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings import ListmonkSettings


class TestListmonkSettingsUnit(unittest.TestCase):
	def test_validate_strips_url(self) -> None:
		doc = ListmonkSettings.__new__(ListmonkSettings)
		doc.base_url = "http://localhost:9000/"
		doc.validate()
		self.assertEqual(doc.base_url, "http://localhost:9000")

	@patch("frappe.enqueue")
	@patch("frappe.has_permission")
	def test_bootstrap_listmonk(self, mock_has_perm: MagicMock, mock_enqueue: MagicMock) -> None:
		mock_has_perm.return_value = True
		doc = ListmonkSettings.__new__(ListmonkSettings)
		res = doc.bootstrap_listmonk()
		self.assertEqual(res["status"], "success")
		mock_enqueue.assert_called_once()
