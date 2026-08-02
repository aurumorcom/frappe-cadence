import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock
from frappe_cadence.cadence.doctype.cadence_provider.cadence_provider import report_event

class TestCadenceProviderIntegration(IntegrationTestCase):
    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        existing_cadence = frappe.db.exists("Cadence", {"cadence_name": "Test Cadence"})
        if not existing_cadence:
            cadence = frappe.get_doc({
                "doctype": "Cadence",
                "cadence_name": "Test Cadence",
            }).insert(ignore_permissions=True, ignore_if_duplicate=True)
            self.cadence_name = cadence.name
        else:
            self.cadence_name = existing_cadence
            
        existing_lead = frappe.db.exists("CRM Lead", {"lead_name": "Test Lead"})
        if not existing_lead:
            lead = frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Test",
                "lead_name": "Test Lead"
            }).insert(ignore_permissions=True, ignore_if_duplicate=True)
            self.lead_name = lead.name
        else:
            self.lead_name = existing_lead
            
        mcc = frappe.get_all("Multi Channel Cadence", filters={"cadence_name": self.cadence_name, "recipient": self.lead_name})
        if not mcc:
            mcc_doc = frappe.get_doc({
                "doctype": "Multi Channel Cadence",
                "cadence_name": self.cadence_name,
                "cadence_for": "CRM Lead",
                "recipient": self.lead_name,
                "status": "In Progress",
                "start_date": frappe.utils.nowdate()
            }).insert(ignore_permissions=True)
            self.mcc_name = mcc_doc.name
        else:
            self.mcc_name = mcc[0].name

    def tearDown(self):
        frappe.db.rollback()
        super().tearDown()

    def test_report_event_replied(self):
        # Emulate webhook
        report_event(
            event_type="message_replied",
            context={"mcc_name": self.mcc_name},
            data={"id": "evt_123"}
        )
        
        # Verify MCC state
        mcc_status = frappe.db.get_value("Multi Channel Cadence", self.mcc_name, "status")
        self.assertEqual(mcc_status, "Completed")
        
        # Verify History creation
        history = frappe.get_all("History", filters={
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": self.mcc_name
        }, fields=["markdown"])
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0].markdown, "Replied")

    @patch("frappe_cadence.cadence.doctype.cadence_provider.cadence_provider.emit_event")
    @patch("frappe.utils.now")
    @patch("frappe.db.set_value")
    @patch("frappe.get_doc")
    def test_report_event_replied_mocked(self, mock_get_doc, mock_set_value, mock_now, mock_emit):
        mock_doc = MagicMock()
        mock_get_doc.return_value = mock_doc
        
        report_event("message_replied", {"mcc_name": "MCC-001"})
        
        mock_set_value.assert_called_once_with("Multi Channel Cadence", "MCC-001", "status", "Completed")
        mock_doc.insert.assert_called_once()

    @patch("frappe_cadence.cadence.doctype.cadence_provider.cadence_provider.emit_event")
    @patch("frappe.utils.now")
    @patch("frappe.db.set_value")
    @patch("frappe.get_doc")
    def test_report_event_bounced_mocked(self, mock_get_doc, mock_set_value, mock_now, mock_emit):
        mock_doc = MagicMock()
        mock_get_doc.return_value = mock_doc
        
        report_event("bounce", {"mcc_name": "MCC-001"})
        
        mock_set_value.assert_called_once_with("Multi Channel Cadence", "MCC-001", "status", "Error")
        mock_doc.insert.assert_called_once()

    @patch("frappe_cadence.cadence.doctype.cadence_provider.cadence_provider.emit_event")
    def test_provider_report_event_terminal_handling(self, mock_emit):
        comm = frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Test Communication Subject",
            "delivery_status": "Scheduled"
        }).insert(ignore_permissions=True)

        report_event(
            "message_replied",
            {"mcc_name": self.mcc_name, "communication_name": comm.name}
        )

        mcc_status = frappe.db.get_value("Multi Channel Cadence", self.mcc_name, "status")
        comm_status = frappe.db.get_value("Communication", comm.name, "status")
        self.assertEqual(mcc_status, "Completed")
        self.assertEqual(comm_status, "Replied")
        self.assertTrue(mock_emit.called)

    def test_provider_report_event_bounce(self):
        comm = frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Test Communication Subject",
            "delivery_status": "Scheduled"
        }).insert(ignore_permissions=True)

        report_event(
            "bounce",
            {"mcc_name": self.mcc_name, "communication_name": comm.name}
        )

        mcc_status = frappe.db.get_value("Multi Channel Cadence", self.mcc_name, "status")
        comm_delivery = frappe.db.get_value("Communication", comm.name, "delivery_status")
        self.assertEqual(mcc_status, "Error")
        self.assertEqual(comm_delivery, "Failed")

    @patch("frappe.utils.now")
    @patch("frappe.db.set_value")
    @patch("frappe.get_doc")
    def test_report_event_sent_opened_mocked(self, mock_get_doc, mock_set_value, mock_now):
        mock_doc = MagicMock()
        mock_get_doc.return_value = mock_doc
        
        report_event("message_sent", {"communication_name": "COMM-001", "mcc_name": "MCC-001"})
        
        mock_set_value.assert_called_once_with("Communication", "COMM-001", "delivery_status", "Sent")
        mock_doc.insert.assert_called_once()
        
        mock_set_value.reset_mock()
        mock_doc.insert.reset_mock()
        
        report_event("message_opened", {"communication_name": "COMM-001", "mcc_name": "MCC-001"})
        
        mock_set_value.assert_called_once_with("Communication", "COMM-001", "read_status", "Read")
        mock_doc.insert.assert_called_once()
