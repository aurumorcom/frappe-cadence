from typing import Any

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk import (
	create_campaign,
	create_list,
	create_subscriber,
	create_webhook,
	delete_campaign,
	delete_list,
	delete_subscriber,
	delete_webhook,
	ensure_listmonk_authorized,
	get_webhooks,
	modify_subscriber_lists,
	update_campaign,
	update_campaign_status,
	update_subscriber,
	update_webhook,
)
from frappe_cadence.tests.integration.external.conftest import (
	cadence_vcr,
	get_test_listmonk_config,
	is_listmonk_live,
)


class TestListmonkIntegrations(FrappeTestCase):
	def setUp(self) -> None:
		if not is_listmonk_live():
			self.skipTest(
				"LISTMONK service is not live or test configuration environment variables not provided"
			)

		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.base_url
		settings.username = cfg.get("username", "crm")
		settings.access_token = self.token
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	@cadence_vcr.use_cassette("integrations_authorized.yaml")
	def test_01_ensure_listmonk_authorized(self) -> None:
		ensure_listmonk_authorized()

	@cadence_vcr.use_cassette("integrations_subscribers_crud.yaml")
	def test_02_subscribers_crud_lifecycle(self) -> None:
		# Create
		subscriber_payload = {
			"email": "external_test_subscriber@example.com",
			"name": "External Test Subscriber",
			"status": "enabled",
			"attribs": {"company": "Acme Corp"},
		}
		res_create = create_subscriber(subscriber_payload)
		self.assertTrue(isinstance(res_create, dict))
		subscriber_id = res_create.get("id")
		self.assertIsNotNone(subscriber_id)

		# Update
		update_payload = {
			"email": "external_test_subscriber_updated@example.com",
			"name": "Updated Subscriber Name",
			"status": "enabled",
			"attribs": {"company": "Acme Corp Updated"},
		}
		res_update = update_subscriber(int(subscriber_id), update_payload)
		self.assertTrue(isinstance(res_update, dict))

		# Delete
		res_delete = delete_subscriber(int(subscriber_id))
		self.assertTrue(res_delete)

	@cadence_vcr.use_cassette("integrations_campaigns_crud.yaml")
	def test_03_campaigns_crud_lifecycle(self) -> None:
		# Create
		campaign_payload = {
			"name": "External Test Campaign",
			"description": "Created during external integration testing",
			"type": "sequence",
		}
		res_create = create_campaign(campaign_payload)
		self.assertTrue(isinstance(res_create, dict))
		campaign_id = res_create.get("id")
		self.assertIsNotNone(campaign_id)

		# Update
		campaign_update = {
			"name": "Renamed External Test Campaign",
			"description": "Updated campaign description",
		}
		res_update = update_campaign(int(campaign_id), campaign_update)
		self.assertTrue(isinstance(res_update, dict))

		# Status update
		res_status = update_campaign_status(int(campaign_id), "active")
		self.assertTrue(isinstance(res_status, dict))

		# Delete
		res_delete = delete_campaign(int(campaign_id))
		self.assertTrue(res_delete)

	@cadence_vcr.use_cassette("integrations_webhooks_crud.yaml")
	def test_04_webhooks_crud_lifecycle(self) -> None:
		# Create Webhook
		webhook_payload = {
			"name": "External Integration Webhook Test",
			"url": "http://localhost:8000/api/method/frappe_cadence.listmonk.webhook",
			"secret": "test_secret_key_12345",
			"events": ["subscriber.created"],
			"enabled": True,
		}
		res_create = create_webhook(webhook_payload)
		self.assertTrue(isinstance(res_create, dict))
		webhook_id = res_create.get("id")
		self.assertIsNotNone(webhook_id)

		# Get Webhooks
		webhooks = get_webhooks()
		self.assertTrue(isinstance(webhooks, list))

		# Update Webhook
		webhook_update = {
			"name": "Updated Webhook Name",
			"url": "http://localhost:8000/api/method/frappe_cadence.listmonk.webhook",
			"secret": "test_secret_key_12345",
			"events": ["subscriber.created", "subscriber.updated"],
			"enabled": True,
		}
		res_update = update_webhook(int(webhook_id), webhook_update)
		self.assertTrue(isinstance(res_update, dict))

		# Delete Webhook
		res_delete = delete_webhook(int(webhook_id))
		self.assertTrue(res_delete)

	@cadence_vcr.use_cassette("integrations_modify_subscriber_lists.yaml")
	def test_05_modify_subscriber_campaigns(self) -> None:
		# Setup subscriber, list, and campaign
		unique_email = f"campaign_test_{frappe.generate_hash(length=6)}@example.com"
		c = create_subscriber({"email": unique_email, "name": "Campaign Sub", "status": "enabled"})
		l = create_list({"name": "Enrollment Test List"})
		cid, lid = c.get("id"), l.get("id")
		s = create_campaign({"name": "Enrollment Test Campaign", "lists": [int(lid)], "type": "sequence"})
		sid = s.get("id")

		try:
			# Add to list
			res_add = modify_subscriber_lists("add", [int(cid)], [int(lid)], status="confirmed")
			self.assertTrue(res_add)

			# Remove from list
			res_remove = modify_subscriber_lists("remove", [int(cid)], [int(lid)])
			self.assertTrue(res_remove)
		finally:
			delete_subscriber(int(cid))
			delete_campaign(int(sid))
			delete_list(int(lid))
