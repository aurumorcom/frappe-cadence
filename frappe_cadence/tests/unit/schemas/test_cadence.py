import unittest

from frappe_cadence.schemas.cadence import (
	LeadEvaluationRequest,
	LeadEvaluationResponse,
)


class TestCadenceSchemas(unittest.TestCase):
	def test_lead_evaluation_request(self) -> None:
		req = LeadEvaluationRequest(
			lead_name="LEAD-001",
			lead_status="Lead",
			industry="Tech",
			country="US",
		)
		self.assertEqual(req.lead_name, "LEAD-001")
		self.assertEqual(req.industry, "Tech")

	def test_lead_evaluation_response(self) -> None:
		resp = LeadEvaluationResponse(
			lead_name="LEAD-001",
			eligible_cadences=["CAD-1", "CAD-2"],
		)
		self.assertEqual(len(resp.eligible_cadences), 2)
