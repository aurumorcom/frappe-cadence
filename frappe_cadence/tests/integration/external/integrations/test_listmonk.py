from typing import Any
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.integrations.listmonk import (
	create_contact,
	create_sequence,
	create_webhook,
	delete_contact,
	delete_sequence,
	delete_webhook,
	ensure_listmonk_authorized,
	get_webhooks,
	modify_contact_sequences,
	update_contact,
	update_sequence,
	update_sequence_status,
	update_webhook,
)


from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config


class TestListmonkIntegrations(FrappeTestCase):
	def setUp(self) -> None:
		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.base_url
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	def test_01_ensure_listmonk_authorized(self) -> None:
		ensure_listmonk_authorized()

	def test_02_contacts_crud_lifecycle(self) -> None:
		# Create
		contact_payload = {
			"email": "external_test_subscriber@example.com",
			"name": "External Test Subscriber",
			"status": "enabled",
			"attribs": {"company": "Acme Corp"},
		}
		res_create = create_contact(contact_payload)
		self.assertTrue(isinstance(res_create, dict))
		contact_id = res_create.get("id")
		self.assertIsNotNone(contact_id)

		# Update
		update_payload = {
			"email": "external_test_subscriber_updated@example.com",
			"name": "Updated Subscriber Name",
			"status": "enabled",
			"attribs": {"company": "Acme Corp Updated"},
		}
		res_update = update_contact(int(contact_id), update_payload)
		self.assertTrue(isinstance(res_update, dict))

		# Delete
		res_delete = delete_contact(int(contact_id))
		self.assertTrue(res_delete)

	def test_03_sequences_crud_lifecycle(self) -> None:
		# Create
		seq_payload = {
			"name": "External Test Sequence",
			"description": "Created during external integration testing",
		}
		res_create = create_sequence(seq_payload)
		self.assertTrue(isinstance(res_create, dict))
		seq_id = res_create.get("id")
		self.assertIsNotNone(seq_id)

		# Update
		seq_update = {
			"name": "Renamed External Test Sequence",
			"description": "Updated sequence description",
		}
		res_update = update_sequence(int(seq_id), seq_update)
		self.assertTrue(isinstance(res_update, dict))

		# Status update
		res_status = update_sequence_status(int(seq_id), "active")
		self.assertTrue(isinstance(res_status, dict))

		# Delete
		res_delete = delete_sequence(int(seq_id))
		self.assertTrue(res_delete)

	def test_04_webhooks_crud_lifecycle(self) -> None:
		# Create Webhook
		webhook_payload = {
			"name": "External Integration Webhook Test",
			"url": "http://localhost:8000/api/method/frappe_cadence.listmonk.webhook",
			"secret": "test_secret_key_12345",
			"events": ["contact.created"],
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
			"events": ["contact.created", "contact.updated"],
			"enabled": True,
		}
		res_update = update_webhook(int(webhook_id), webhook_update)
		self.assertTrue(isinstance(res_update, dict))

		# Delete Webhook
		res_delete = delete_webhook(int(webhook_id))
		self.assertTrue(res_delete)

	def test_05_modify_contact_sequences(self) -> None:
		# Setup contact and sequence
		unique_email = f"seq_test_{frappe.generate_hash(length=6)}@example.com"
		c = create_contact({"email": unique_email, "name": "Seq Sub", "status": "enabled"})
		s = create_sequence({"name": "Enrollment Test Sequence"})
		cid, sid = c.get("id"), s.get("id")

		try:
			# Add to sequence
			res_add = modify_contact_sequences("add", [int(cid)], [int(sid)], status="confirmed")
			self.assertTrue(res_add)

			# Remove from sequence
			res_remove = modify_contact_sequences("remove", [int(cid)], [int(sid)])
			self.assertTrue(res_remove)
		finally:
			delete_contact(int(cid))
			delete_sequence(int(sid))
