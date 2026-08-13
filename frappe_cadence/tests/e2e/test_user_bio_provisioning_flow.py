from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.integrations.listmonk import ensure_user_bio_provisioned


class TestUserBioProvisioningE2E(FrappeTestCase):
	def setUp(self) -> None:
		self.user = "e2e_rep@example.com"
		if not frappe.db.exists("User", self.user):
			frappe.get_doc({
				"doctype": "User",
				"email": self.user,
				"first_name": "E2E",
				"last_name": "Rep",
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe.wait_for")
	def test_missing_bio_defers_and_creation_resumes(self, mock_wait_for) -> None:
		frappe.db.delete("User Bio", {"reference_user": self.user})

		mock_wait_for.side_effect = Exception("Job Deferred")
		with self.assertRaises(Exception):
			ensure_user_bio_provisioned(self.user, "E2E Cadence")

		mock_wait_for.assert_called_once()

		bio = frappe.get_doc({
			"doctype": "User Bio",
			"reference_user": self.user,
			"reference_cadence": "E2E Cadence",
			"enabled": 1,
			"content": "# Sales Bio Markdown",
		}).insert(ignore_permissions=True, ignore_links=True)

		mock_wait_for.reset_mock()
		res = ensure_user_bio_provisioned(self.user, "E2E Cadence")
		self.assertEqual(res, "# Sales Bio Markdown")
