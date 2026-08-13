import unittest

from frappe_cadence.integrations.listmonk.schemas.campaign import (
	CampaignCreateRequest,
	CampaignResponse,
	TransactionalEmailRequest,
)


class TestCampaignSchemas(unittest.TestCase):
	def test_campaign_create_request(self) -> None:
		req = CampaignCreateRequest(
			name="Campaign Alpha",
			subject="Special Offer",
			lists=[1, 2],
			body="<p>Hello world</p>",
		)
		self.assertEqual(req.name, "Campaign Alpha")
		self.assertEqual(req.type, "regular")
		self.assertEqual(req.content_type, "richtext")

	def test_campaign_response(self) -> None:
		resp = CampaignResponse(id=10, name="Campaign Alpha", status="draft")
		self.assertEqual(resp.id, 10)

	def test_transactional_email_request(self) -> None:
		req = TransactionalEmailRequest(
			subscriber_email="user@test.local",
			template_id=3,
			data={"name": "Alice"},
		)
		self.assertEqual(req.subscriber_email, "user@test.local")
		self.assertEqual(req.template_id, 3)
