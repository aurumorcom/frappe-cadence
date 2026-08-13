from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestListmonkSettingsInternalIntegration(FrappeTestCase):
	def test_settings_save(self) -> None:
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 0
		settings.save(ignore_permissions=True)
		self.assertEqual(settings.status, "Disabled")
