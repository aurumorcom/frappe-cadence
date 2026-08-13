import unittest

from frappe_cadence.integrations.listmonk.schemas.webhook import (
	WebhookCreateRequest,
	WebhookEventPayload,
	WebhookResponse,
	WebhookUpdateRequest,
)


class TestWebhookSchemas(unittest.TestCase):
	def test_webhook_create_request(self) -> None:
		req = WebhookCreateRequest(
			name="Main Webhook",
			url="https://example.com/webhook",
			events=["campaign.started"],
		)
		self.assertEqual(req.name, "Main Webhook")
		self.assertEqual(req.url, "https://example.com/webhook")
		self.assertTrue(req.enabled)

	def test_webhook_update_request(self) -> None:
		req = WebhookUpdateRequest(enabled=False)
		self.assertEqual(req.model_dump(exclude_unset=True), {"enabled": False})

	def test_webhook_response(self) -> None:
		resp = WebhookResponse(
			id=99,
			name="Main Webhook",
			url="https://example.com/webhook",
		)
		self.assertEqual(resp.id, 99)

	def test_webhook_event_payload(self) -> None:
		payload = WebhookEventPayload(
			event="campaign.sent",
			data={"campaign_id": 1, "subscriber_id": 42},
		)
		self.assertEqual(payload.event, "campaign.sent")
		self.assertEqual(payload.data["subscriber_id"], 42)
