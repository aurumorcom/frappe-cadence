import unittest

from frappe_cadence.integrations.listmonk.schemas.list import (
	ListCreateRequest,
	ListResponse,
	ListUpdateRequest,
)


class TestListSchemas(unittest.TestCase):
	def test_list_create_request(self) -> None:
		req = ListCreateRequest(name="Cold Outreach", tags=["sales", "2025"])
		self.assertEqual(req.name, "Cold Outreach")
		self.assertEqual(req.type, "public")
		self.assertEqual(req.optin, "single")

	def test_list_update_request(self) -> None:
		req = ListUpdateRequest(name="Updated Name")
		self.assertEqual(req.model_dump(exclude_unset=True), {"name": "Updated Name"})

	def test_list_response(self) -> None:
		resp = ListResponse(id=1, name="List 1", type="public", optin="single")
		self.assertEqual(resp.id, 1)
