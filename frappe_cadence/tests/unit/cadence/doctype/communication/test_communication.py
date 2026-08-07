from unittest.mock import patch, MagicMock
from frappe.tests import UnitTestCase
import frappe
from frappe_cadence.cadence.doctype.communication.communication import on_update

class TestCommunicationEvents(UnitTestCase):
    def test_module_load(self):
        import frappe_cadence.cadence.doctype.communication.communication as comm_module
        self.assertIsNotNone(comm_module)

    def test_on_update_ignores_non_mcc_communication(self):
        comm = MagicMock()
        comm.reference_doctype = "Customer"
        comm.reference_name = "CUST-001"

        with patch("frappe.db.exists") as mock_exists:
            on_update(comm)
            mock_exists.assert_not_called()

    def test_on_update_ignores_incomplete_schedules(self):
        comm = MagicMock()
        comm.reference_doctype = "Multi Channel Cadence"
        comm.reference_name = "MCC-001"

        mock_mcc = MagicMock()
        mock_mcc.status = "Draft"
        mock_mcc.cadence_name = "CADENCE-001"

        mock_cadence = MagicMock()
        mock_cadence.cadence_schedules = [
            MagicMock(name="SCHED-1"),
            MagicMock(name="SCHED-2")
        ]
        # Override name attributes
        mock_cadence.cadence_schedules[0].name = "SCHED-1"
        mock_cadence.cadence_schedules[1].name = "SCHED-2"

        # Only 1 communication exists for 2 steps
        mock_comms = [
            MagicMock(cadence_schedule="SCHED-1", delivery_status="Scheduled")
        ]

        def get_doc_side_effect(doctype, name):
            if doctype == "Multi Channel Cadence":
                return mock_mcc
            if doctype == "Cadence":
                return mock_cadence
            return MagicMock()

        with patch("frappe.db.exists", return_value=True):
            with patch("frappe.get_doc", side_effect=get_doc_side_effect):
                with patch("frappe.get_all", return_value=mock_comms):
                    on_update(comm)
                    mock_mcc.save.assert_not_called()

    @patch("frappe_cadence.cadence.doctype.communication.communication.emit_event")
    def test_on_update_transitions_mcc_draft_to_scheduled(self, mock_emit_event):
        comm = MagicMock()
        comm.reference_doctype = "Multi Channel Cadence"
        comm.reference_name = "MCC-001"

        mock_mcc = MagicMock()
        mock_mcc.status = "Draft"
        mock_mcc.cadence_name = "CADENCE-001"

        mock_cadence = MagicMock()
        sched1, sched2 = MagicMock(), MagicMock()
        sched1.name = "SCHED-1"
        sched2.name = "SCHED-2"
        mock_cadence.cadence_schedules = [sched1, sched2]

        mock_comms = [
            MagicMock(cadence_schedule="SCHED-1", delivery_status="Scheduled"),
            MagicMock(cadence_schedule="SCHED-2", delivery_status="Scheduled")
        ]

        def get_doc_side_effect(doctype, name):
            if doctype == "Multi Channel Cadence":
                return mock_mcc
            if doctype == "Cadence":
                return mock_cadence
            return MagicMock()

        with patch("frappe.db.exists", return_value=True):
            with patch("frappe.get_doc", side_effect=get_doc_side_effect):
                with patch("frappe.get_all", return_value=mock_comms):
                    on_update(comm)

                    self.assertEqual(mock_mcc.status, "Scheduled")
                    mock_mcc.save.assert_called_once()
                    mock_emit_event.assert_called_once_with(
                        "mcc_scheduled", {"doctype": "Multi Channel Cadence", "name": "MCC-001"}
                    )

    @patch("frappe_cadence.cadence.doctype.communication.communication.emit_event")
    def test_on_update_transitions_mcc_scheduled_to_in_progress(self, mock_emit_event):
        comm = MagicMock()
        comm.reference_doctype = "Multi Channel Cadence"
        comm.reference_name = "MCC-001"

        mock_mcc = MagicMock()
        mock_mcc.status = "Scheduled"
        mock_mcc.cadence_name = "CADENCE-001"

        mock_cadence = MagicMock()
        sched1, sched2 = MagicMock(), MagicMock()
        sched1.name = "SCHED-1"
        sched2.name = "SCHED-2"
        mock_cadence.cadence_schedules = [sched1, sched2]

        mock_comms = [
            MagicMock(cadence_schedule="SCHED-1", delivery_status="Sent"),
            MagicMock(cadence_schedule="SCHED-2", delivery_status="Scheduled")
        ]

        def get_doc_side_effect(doctype, name):
            if doctype == "Multi Channel Cadence":
                return mock_mcc
            if doctype == "Cadence":
                return mock_cadence
            return MagicMock()

        with patch("frappe.db.exists", return_value=True):
            with patch("frappe.get_doc", side_effect=get_doc_side_effect):
                with patch("frappe.get_all", return_value=mock_comms):
                    on_update(comm)

                    self.assertEqual(mock_mcc.status, "In Progress")
                    mock_mcc.save.assert_called_once()
                    mock_emit_event.assert_called_once_with(
                        "mcc_in_progress", {"doctype": "Multi Channel Cadence", "name": "MCC-001"}
                    )
