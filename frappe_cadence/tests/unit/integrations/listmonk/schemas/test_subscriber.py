import unittest

from frappe_cadence.integrations.listmonk.schemas.subscriber import (
	SubscriberCreateRequest,
	SubscriberListModifyRequest,
	SubscriberResponse,
	SubscriberUpdateRequest,
)


class TestSubscriberSchemas(unittest.TestCase):
	def test_subscriber_create_request(self) -> None:
		req = SubscriberCreateRequest(
			email="lead@company.com",
			name="Lead Name",
			lists=[1, 2],
			attribs={"industry": "SaaS"},
		)
		self.assertEqual(req.email, "lead@company.com")
		self.assertEqual(req.status, "enabled")
		self.assertTrue(req.preconfirm_subscriptions)

	def test_subscriber_update_request(self) -> None:
		req = SubscriberUpdateRequest(name="New Name")
		dump = req.model_dump(exclude_unset=True)
		self.assertEqual(dump, {"name": "New Name"})

	def test_subscriber_response(self) -> None:
		resp = SubscriberResponse(
			id=42,
			email="lead@company.com",
			name="Lead Name",
			status="enabled",
		)
		self.assertEqual(resp.id, 42)

	def test_subscriber_list_modify(self) -> None:
		req = SubscriberListModifyRequest(
			action="remove",
			ids=[10],
			target_list_ids=[1],
		)
		self.assertEqual(req.action, "remove")
