from unittest.mock import MagicMock, patch

from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberCreateRequest


class TestListmonkClientExternal(FrappeTestCase):
	def setUp(self) -> None:
		self.client = ListmonkClient(
			base_url="https://listmonk.capybaara.com",
			username="crm",
			token="7VPrQtx6YYJBmUjS0UmqVUnciE7AnIEj1zH2kUoUkgB0Efy8",
		)

	def test_external_auth_header_format(self) -> None:
		headers = self.client._get_headers()
		self.assertEqual(
			headers["Authorization"],
			"token crm:7VPrQtx6YYJBmUjS0UmqVUnciE7AnIEj1zH2kUoUkgB0Efy8",
		)

	@patch("requests.get")
	def test_external_test_connection(self, mock_get: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.status_code = 200
		mock_get.return_value = mock_resp

		self.assertTrue(self.client.test_connection())
		mock_get.assert_called_once_with(
			"https://listmonk.capybaara.com/api/campaigns",
			headers={
				"Authorization": "token crm:7VPrQtx6YYJBmUjS0UmqVUnciE7AnIEj1zH2kUoUkgB0Efy8",
				"Content-Type": "application/json",
			},
			timeout=10,
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
