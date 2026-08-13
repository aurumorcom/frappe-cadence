import hmac
import hashlib
import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.listmonk import webhook
from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config


class TestListmonkWebhook(FrappeTestCase):
	def setUp(self) -> None:
		cfg = get_test_listmonk_config()
		self.secret = cfg["webhook_secret"]
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = cfg["base_url"]
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

		self.cadence = frappe.get_doc({
			"doctype": "Cadence",
			"cadence_name": "Webhook Test Cadence",
			"enabled": 1,
			"listmonk_id": 999,
		}).insert(ignore_permissions=True, ignore_links=True)

		self.lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "Webhook",
			"lead_name": "Webhook Lead Test",
			"email_id": "webhook_test@example.com",
			"listmonk_id": 888,
		}).insert(ignore_permissions=True, ignore_links=True)

		self.mcc = frappe.get_doc({
			"doctype": "Multi Channel Cadence",
			"cadence_name": self.cadence.name,
			"recipient": self.lead.name,
			"status": "Scheduled",
			"listmonk_contact_id": 888,
			"listmonk_sequence_id": 999,
		}).insert(ignore_permissions=True, ignore_links=True)

	def test_webhook_hmac_signature_and_mcc_status_update(self) -> None:
		payload_dict = {
			"event": "replied",
			"contact_id": 888,
			"sequence_id": 999,
			"email": "webhook_test@example.com",
			"sender_email": "sales@company.com",
			"message": "Interested in learning more!",
		}
		body_bytes = json.dumps(payload_dict).encode("utf-8")
		sig = hmac.new(self.secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

		frappe.local.request = frappe._dict({
			"get_data": lambda: body_bytes,
			"headers": {"Listmonk-Signature": sig},
		})
		frappe.local.form_dict = frappe._dict(payload_dict)

		res = webhook()
		self.assertTrue(isinstance(res, dict))
		self.assertEqual(res.get("status"), "ok")

		self.mcc.reload()
		self.assertEqual(self.mcc.status, "Replied")
