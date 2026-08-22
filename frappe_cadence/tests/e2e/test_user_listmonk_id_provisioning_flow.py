from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk import ensure_user_listmonk_id_provisioned
from frappe_cadence.integrations.listmonk.jobs.user import get_users
from frappe_cadence.jobs.multi_channel_cadence import add_subscriber_to_campaign


class TestUserListmonkIdProvisioningFlowE2E(FrappeTestCase):
	def setUp(self) -> None:
		self.user_email = f"e2e_sales_{frappe.generate_hash(length=6)}@example.com"
		self.user = frappe.get_doc(
			{
				"doctype": "User",
				"email": self.user_email,
				"first_name": "E2E Sales",
				"last_name": "Rep",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True, ignore_links=True)

		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "E2E Lead",
				"email": "e2e_lead@acmecorp.com",
				"email_id": "e2e_lead@acmecorp.com",
				"listmonk_id": 501,
			}
		).insert(ignore_permissions=True, ignore_links=True)

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "E2E User ID Flow Cadence",
				"enabled": 1,
				"listmonk_id": 101,
				"listmonk_list_id": 1,
			}
		).insert(ignore_permissions=True, ignore_links=True)

		self.mcc = frappe.get_doc(
			{
				"doctype": "Multi Channel Cadence",
				"cadence_name": self.cadence.name,
				"cadence_for": "CRM Lead",
				"recipient": self.lead.name,
				"sender": self.user.name,
				"status": "Provisioning",
			}
		).insert(ignore_permissions=True, ignore_links=True)

	def tearDown(self) -> None:
		frappe.db.delete("User", {"email": self.user_email})

	@patch("frappe.wait_for")
	def test_ensure_user_listmonk_id_defers_when_missing(self, mock_wait_for: MagicMock) -> None:
		# User has no listmonk_id initially
		self.assertFalse(self.user.get("listmonk_id"))

		mock_wait_for.side_effect = Exception("Job Deferred")
		frappe.flags.current_job_id = "job_test_123"
		try:
			with self.assertRaises(Exception):
				ensure_user_listmonk_id_provisioned(self.user.name)
		finally:
			frappe.flags.current_job_id = None

		mock_wait_for.assert_called_once_with(
			event_key=f"User:on_update:{self.user.name}",
			condition="argument.get('listmonk_id') is not None and argument.get('listmonk_id') > 0",
		)

	@patch("frappe_cadence.integrations.listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.user.ListmonkClient")
	def test_get_users_populates_listmonk_id(
		self, mock_client_cls: MagicMock, mock_auth: MagicMock
	) -> None:
		client_inst = MagicMock()
		client_inst.get_listmonk_users.return_value = [
			{"id": 777, "email": self.user_email, "name": "E2E Sales Rep"}
		]
		mock_client_cls.return_value = client_inst

		get_users()

		self.user.reload()
		self.assertEqual(int(self.user.listmonk_id), 777)

	@patch("frappe_cadence.jobs.multi_channel_cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.multi_channel_cadence.resolve_user_bio", return_value="Account Executive")
	@patch("frappe_cadence.jobs.multi_channel_cadence.ListmonkClient")
	def test_campaign_enrollment_uses_user_listmonk_id_and_bio(
		self,
		mock_client_cls: MagicMock,
		mock_bio: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		# Set listmonk_id on user
		self.user.db_set("listmonk_id", 777)
		self.user.reload()

		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		add_subscriber_to_campaign(self.mcc.name)

		client_inst.update_subscriber.assert_called_once()
		call_args = client_inst.update_subscriber.call_args
		payload = call_args[0][1]

		# Verify attribs.user contains user.id == 777 and user.bio == bio
		req_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload
		attribs_user = req_dict["attribs"]["user"]
		self.assertEqual(attribs_user["id"], 777)
		self.assertEqual(attribs_user["bio"], "Account Executive")
		self.assertEqual(attribs_user["name"], self.user.name)
