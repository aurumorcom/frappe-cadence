import unittest

from frappe_listmonk.schemas.subscriber import SubscriberCreateRequest, SubscriberResponse


class TestSubscriberSchemas(unittest.TestCase):
	def test_subscriber_request_schema(self) -> None:
		req = SubscriberCreateRequest(
			email="jane@example.com",
			name="Jane Doe",
			crm_id="LEAD-00001",
			status="enabled",
			lists=[1, 2],
			attribs={"company": "Acme Corp"},
		)
		dump = req.model_dump()
		self.assertEqual(dump["crm_id"], "LEAD-00001")
		self.assertEqual(dump["attribs"]["company"], "Acme Corp")

	def test_subscriber_response_schema(self) -> None:
		res = SubscriberResponse(
			id=100,
			uuid="ea06b2e7-4b08-4697-bcfc-2a5c6dde8f1c",
			email="jane@example.com",
			name="Jane Doe",
			phone="+14155552671",
			crm_id="LEAD-00001",
			status="enabled",
			attribs={"company": "Acme Corp"},
		)
		self.assertEqual(res.id, 100)
		self.assertEqual(res.phone, "+14155552671")
