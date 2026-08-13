from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.integrations.listmonk import (
	create_contact,
	create_sequence,
	delete_contact,
	delete_sequence,
	ensure_listmonk_authorized,
	ensure_user_bio_provisioned,
	update_contact,
	update_sequence,
)


class TestListmonkIntegrationUnit(FrappeTestCase):
	@patch("frappe.wait_for")
	@patch("frappe.get_doc")
	def test_ensure_listmonk_authorized_defers_when_unauthorized(self, mock_get_doc, mock_wait_for) -> None:
		settings_mock = MagicMock()
		settings_mock.enabled = 0
		settings_mock.status = "Disabled"
		mock_get_doc.return_value = settings_mock

		ensure_listmonk_authorized()

		mock_wait_for.assert_called_once_with(
			"listmonk_authorized",
			condition="argument.get('enabled') == 1 and argument.get('status') == 'Authorized'",
		)

	@patch("frappe.wait_for")
	@patch("frappe.get_all", return_value=[])
	def test_ensure_user_bio_provisioned_defers_when_missing(self, mock_get_all, mock_wait_for) -> None:
		mock_wait_for.side_effect = Exception("Job deferred")

		with self.assertRaises(Exception):
			ensure_user_bio_provisioned("sales_rep@example.com", "CAD-001")

		mock_wait_for.assert_called_once()

	@patch("frappe_cadence.integrations.listmonk._make_request")
	def test_client_methods(self, mock_request) -> None:
		mock_request.return_value = {"id": 10}

		res = create_contact({"email": "test@example.com"})
		mock_request.assert_called_with("POST", "/api/contacts", payload={"email": "test@example.com"})
		self.assertEqual(res, {"id": 10})

		update_contact(10, {"name": "New Name"})
		mock_request.assert_called_with("PUT", "/api/contacts/10", payload={"name": "New Name"})

		delete_contact(10)
		mock_request.assert_called_with("DELETE", "/api/contacts/10")

		create_sequence({"name": "Seq 1"})
		mock_request.assert_called_with(
			"POST", "/api/lists", payload={"type": "public", "optin": "single", "name": "Seq 1"}
		)

		update_sequence(5, {"name": "Seq Updated"})
		mock_request.assert_called_with("PUT", "/api/sequences/5", payload={"name": "Seq Updated"})

		delete_sequence(5)
		mock_request.assert_called_with("DELETE", "/api/sequences/5")
