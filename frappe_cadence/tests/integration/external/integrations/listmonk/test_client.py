from unittest.mock import MagicMock, patch

from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberCreateRequest


class TestListmonkClientExternal(FrappeTestCase):
	def setUp(self) -> None:
		self.client = ListmonkClient(
			base_url="https://listmonk.mock.external",
			token="mock_external_token",
		)

	@patch("requests.request")
	def test_create_subscriber_external(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": {"id": 200, "email": "ext@lead.com", "name": "Ext Lead", "status": "enabled", "lists": [], "attribs": {}}}'
		mock_resp.json.return_value = {
			"data": {
				"id": 200,
				"email": "ext@lead.com",
				"name": "Ext Lead",
				"status": "enabled",
				"lists": [],
				"attribs": {},
			}
		}
		mock_req.return_value = mock_resp

		req = SubscriberCreateRequest(email="ext@lead.com", name="Ext Lead")
		resp = self.client.create_subscriber(req)
		self.assertEqual(resp.id, 200)
		self.assertEqual(resp.email, "ext@lead.com")
