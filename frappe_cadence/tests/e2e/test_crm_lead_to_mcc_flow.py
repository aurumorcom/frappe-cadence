from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.cadence.cadence import add_lead_batch_to_cadence
from frappe_cadence.cadence.doctype.crm_lead.crm_lead import evaluate_cadences_for_lead, upsert_contact


class TestCRMLeadToMCCFlowE2E(FrappeTestCase):
	def setUp(self) -> None:
		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "E2E Lead Trigger Cadence",
				"assign_condition": 'doc.territory == "India"',
				"enabled": 1,
				"listmonk_id": 801,
			}
		).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.create_contact", return_value={"id": 444})
	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.ensure_listmonk_authorized")
	def test_new_crm_lead_syncs_contact_and_triggers_mcc_creation(
		self, mock_ensure_auth, mock_create_contact
	) -> None:
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "E2E Trigger Lead",
				"lead_name": "E2E Trigger Lead",
				"email_id": "trigger.lead@example.com",
				"territory": "India",
			}
		).insert(ignore_permissions=True, ignore_links=True)

		upsert_contact(lead.name)
		lead.reload()
		self.assertEqual(lead.listmonk_id, 444)

		evaluate_cadences_for_lead(lead.name)
		add_lead_batch_to_cadence(self.cadence.name, [lead.name])

		mccs = frappe.get_all(
			"Multi Channel Cadence", filters={"recipient": lead.name, "cadence_name": self.cadence.name}
		)
		self.assertEqual(len(mccs), 1)
