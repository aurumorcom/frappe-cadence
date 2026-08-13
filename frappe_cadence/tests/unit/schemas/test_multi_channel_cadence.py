import unittest

from frappe_cadence.schemas.multi_channel_cadence import (
	MCCStatusUpdateRequest,
)


class TestMultiChannelCadenceSchemas(unittest.TestCase):
	def test_mcc_status_update_request(self) -> None:
		req = MCCStatusUpdateRequest(
			mcc_name="MCC-001",
			status="In Progress",
			reason="Sequence started",
		)
		self.assertEqual(req.mcc_name, "MCC-001")
		self.assertEqual(req.status, "In Progress")
		self.assertEqual(req.reason, "Sequence started")
