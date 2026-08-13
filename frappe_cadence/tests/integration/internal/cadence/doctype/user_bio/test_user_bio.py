import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio


class TestUserBioInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.user_email = "bio_int_user@example.com"
		if not frappe.db.exists("User", self.user_email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": self.user_email,
					"first_name": "BioInt",
					"last_name": "User",
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists("Cadence", "CAD-INT-1"):
			frappe.get_doc(
				{
					"doctype": "Cadence",
					"cadence_code": "CAD-INT-1",
					"cadence_name": "CAD-INT-1",
					"enabled": 1,
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists(
			"User Bio", {"reference_user": self.user_email, "reference_cadence": "CAD-INT-1"}
		):
			self.user_bio = frappe.get_doc(
				{
					"doctype": "User Bio",
					"reference_user": self.user_email,
					"reference_cadence": "CAD-INT-1",
					"is_default": 1,
					"enabled": 1,
					"content": "Int user bio text",
				}
			).insert(ignore_permissions=True)

	def test_get_user_bio_from_db(self) -> None:
		bio = get_user_bio(self.user_email, reference_cadence="CAD-INT-1")
		self.assertEqual(bio, "Int user bio text")
