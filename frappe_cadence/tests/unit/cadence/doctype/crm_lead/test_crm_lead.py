from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.crm_lead.crm_lead import (
	delete_contact,
	on_trash,
	on_update,
	upsert_contact,
)


class TestCRMLeadUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_crm_lead_on_update_enqueues_jobs(self, mock_enqueue) -> None:
		doc = frappe._dict({"name": "LEAD-0001"})
		on_update(doc)
		self.assertEqual(mock_enqueue.call_count, 2)

	@patch("frappe.enqueue")
	def test_crm_lead_on_trash_enqueues_delete_contact(self, mock_enqueue) -> None:
		doc = frappe._dict({"name": "LEAD-0001", "listmonk_id": 101})
		on_trash(doc)
		mock_enqueue.assert_called_once_with(
			"frappe_cadence.cadence.doctype.crm_lead.crm_lead.delete_contact",
			queue="high",
			listmonk_id=101,
		)

	@patch("frappe.enqueue")
	def test_crm_lead_on_trash_skips_when_no_listmonk_id(self, mock_enqueue) -> None:
		doc = frappe._dict({"name": "LEAD-0001", "listmonk_id": None})
		on_trash(doc)
		mock_enqueue.assert_not_called()

	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.create_contact")
	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.ensure_listmonk_authorized")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_upsert_contact_creates_contact_when_no_listmonk_id(
		self, mock_exists, mock_get_doc, mock_ensure_auth, mock_create
	) -> None:
		lead_doc = MagicMock()
		lead_doc.name = "LEAD-0001"
		lead_doc.get.side_effect = lambda k: None if k == "listmonk_id" else "test@example.com"
		lead_doc.as_dict.return_value = {"name": "LEAD-0001"}
		mock_get_doc.return_value = lead_doc
		mock_create.return_value = {"id": 101}

		upsert_contact("LEAD-0001")

		mock_ensure_auth.assert_called_once()
		mock_create.assert_called_once()
		lead_doc.db_set.assert_called_once_with("listmonk_id", 101)

	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.update_contact")
	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.ensure_listmonk_authorized")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_upsert_contact_updates_contact_when_listmonk_id_exists(
		self, mock_exists, mock_get_doc, mock_ensure_auth, mock_update
	) -> None:
		lead_doc = MagicMock()
		lead_doc.name = "LEAD-0001"
		lead_doc.get.side_effect = lambda k: 101 if k == "listmonk_id" else "test@example.com"
		lead_doc.as_dict.return_value = {"name": "LEAD-0001"}
		mock_get_doc.return_value = lead_doc

		upsert_contact("LEAD-0001")

		mock_ensure_auth.assert_called_once()
		mock_update.assert_called_once()

	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.api_delete_contact")
	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.ensure_listmonk_authorized")
	def test_delete_contact(self, mock_ensure_auth, mock_api_delete) -> None:
		delete_contact(101)
		mock_ensure_auth.assert_called_once()
		mock_api_delete.assert_called_once_with(101)
