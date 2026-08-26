import unittest

from frappe_listmonk.schemas.list import ListCreateRequest, ListResponse


class TestListSchemas(unittest.TestCase):
	def test_list_create_request(self) -> None:
		req = ListCreateRequest(
			name="Outreach List",
			crm_id="LIST-00001",
		)
		dump = req.model_dump()
		self.assertEqual(dump["crm_id"], "LIST-00001")
		self.assertEqual(dump["type"], "private")
		self.assertEqual(dump["optin"], "single")
