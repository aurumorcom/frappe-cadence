import unittest

from frappe_listmonk.schemas.user import UserResponse


class TestUserSchemas(unittest.TestCase):
	def test_user_response(self) -> None:
		res = UserResponse(
			id=12,
			email="sales@example.com",
			name="Sales User",
			crm_id="user@example.com",
		)
		self.assertEqual(res.id, 12)
		self.assertEqual(res.crm_id, "user@example.com")
