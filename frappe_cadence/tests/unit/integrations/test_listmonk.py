from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk import (
	create_campaign,
	create_list,
	create_subscriber,
	delete_campaign,
	delete_list,
	delete_subscriber,
	ensure_listmonk_authorized,
	ensure_user_bio_provisioned,
	get_campaign,
	get_list,
	modify_subscriber_campaigns,
	modify_subscriber_lists,
	update_campaign,
	update_campaign_status,
	update_list,
	update_subscriber,
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
			event_key="Listmonk Settings:on_update:Listmonk Settings",
			condition="argument.get('enabled') == 1 and argument.get('status') == 'Authorized'",
		)

	@patch("frappe.wait_for")
	@patch("frappe.get_all", return_value=[])
	def test_ensure_user_bio_provisioned_defers_when_missing(self, mock_get_all, mock_wait_for) -> None:
		mock_wait_for.side_effect = Exception("Job deferred")

		with self.assertRaises(Exception):
			ensure_user_bio_provisioned("sales_rep@example.com", "CAD-001")

		mock_wait_for.assert_called_once()

	@patch("frappe_cadence.integrations.listmonk.client.ListmonkClient._request")
	def test_client_methods(self, mock_request) -> None:
		mock_request.return_value = {
			"id": 10,
			"email": "test@example.com",
			"name": "Test",
			"status": "enabled",
			"type": "public",
			"optin": "single",
			"lists": [],
			"attribs": {},
		}

		res = create_subscriber({"email": "test@example.com"})
		mock_request.assert_called_with("POST", "/api/subscribers", payload={"email": "test@example.com"})
		self.assertEqual(
			res,
			{
				"id": 10,
				"email": "test@example.com",
				"name": "Test",
				"status": "enabled",
				"lists": [],
				"attribs": {},
			},
		)

		update_subscriber(10, {"name": "New Name"})
		mock_request.assert_called_with("PUT", "/api/subscribers/10", payload={"name": "New Name"})

		delete_subscriber(10)
		mock_request.assert_called_with("DELETE", "/api/subscribers/10")

		create_list({"name": "List 1"})
		mock_request.assert_called_with(
			"POST",
			"/api/lists",
			payload={"type": "public", "optin": "single", "name": "List 1"},
		)

		update_list(10, {"name": "List Updated"})
		mock_request.assert_called_with(
			"PUT",
			"/api/lists/10",
			payload={"type": "public", "optin": "single", "name": "List Updated"},
		)

		delete_list(10)
		mock_request.assert_called_with("DELETE", "/api/lists/10")

		get_list(10)
		mock_request.assert_called_with("GET", "/api/lists/10")

		create_campaign({"name": "Seq 1", "lists": [10]})
		mock_request.assert_called_with(
			"POST",
			"/api/campaigns",
			payload={
				"type": "sequence",
				"status": "running",
				"description": "",
				"lists": [10],
				"content_type": "richtext",
				"subject": "Seq 1",
				"body": "",
				"name": "Seq 1",
			},
		)

		update_campaign(5, {"name": "Seq Updated", "lists": [10]})
		mock_request.assert_called_with(
			"PUT",
			"/api/campaigns/5",
			payload={
				"type": "sequence",
				"status": "running",
				"description": "",
				"lists": [10],
				"name": "Seq Updated",
			},
		)

		update_campaign_status(5, "paused")
		mock_request.assert_called_with("PUT", "/api/campaigns/5/status", payload={"status": "paused"})

		delete_campaign(5)
		mock_request.assert_called_with("DELETE", "/api/campaigns/5")

		get_campaign(5)
		mock_request.assert_called_with("GET", "/api/campaigns/5")

		modify_subscriber_lists(action="add", subscriber_ids=[1, 2], list_ids=[10], status="confirmed")
		mock_request.assert_called_with(
			"PUT",
			"/api/subscribers/lists",
			payload={"action": "add", "ids": [1, 2], "target_list_ids": [10], "status": "confirmed"},
		)

		modify_subscriber_campaigns(action="remove", subscriber_ids=[1, 2], list_ids=[10])
		mock_request.assert_called_with(
			"PUT",
			"/api/subscribers/lists",
			payload={"action": "remove", "ids": [1, 2], "target_list_ids": [10], "status": "confirmed"},
		)
