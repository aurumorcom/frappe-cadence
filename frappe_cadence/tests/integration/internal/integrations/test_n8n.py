import json
import frappe
from unittest.mock import patch, MagicMock
from frappe.tests import IntegrationTestCase
from frappe_cadence._template import handle_callback
from frappe_cadence.integrations.n8n import (
    get_test_request_url,
    optimize,
    optimize_callback,
    trigger_execution,
    trigger_test_execution
)

class TestN8NIntegration(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    def tearDown(self):
        frappe.db.rollback()

    def test_get_test_request_url(self):
        prod_url = "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d"
        expected_test_url = "https://n8n.capybaara.com/webhook-test/ce63ee3b-90f5-41cb-9538-1418302eac7d"
        self.assertEqual(get_test_request_url(prod_url), expected_test_url)

        custom_url = "https://example.com/custom-endpoint"
        self.assertEqual(get_test_request_url(custom_url), custom_url)
        self.assertEqual(get_test_request_url(""), "")

    def test_optimize_no_schedule_fails_gracefully(self):
        template = frappe.get_doc({
            "doctype": "SMS Template",
            "title": "N8N Test No Schedule SMS",
            "provider": "n8n",
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        res = optimize("SMS Template", template.name)
        self.assertEqual(res.get("status"), "failed")
        self.assertIn("No Cadence step found", res.get("error"))

    def test_optimize_no_active_mcc_fails_gracefully(self):
        template = frappe.get_doc({
            "doctype": "Email Template",
            "name": "N8N Test No MCC Template",
            "__newname": "N8N Test No MCC Template",
            "title": "N8N Test No MCC Template",
            "subject": "Test Subject",
            "provider": "n8n",
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        cadence = frappe.get_doc({
            "doctype": "Cadence",
            "cadence_name": "N8N Test Cadence No MCC",
            "cadence_code": "CAD-TEST-NOMCC-001",
            "cadence_schedules": [
                {
                    "reference_doctype": "Email Template",
                    "reference_name": template.name,
                    "send_after_days": 1
                }
            ]
        }).insert(ignore_permissions=True)

        # Create an MCC in Provisioning status
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "lead_name": "N8N Lead Provisioning",
            "first_name": "N8N",
            "email_id": "n8n_prov_lead@example.com"
        }).insert(ignore_permissions=True)

        mcc = frappe.get_doc({
            "doctype": "Multi Channel Cadence",
            "cadence_name": cadence.name,
            "cadence_for": "CRM Lead",
            "recipient": lead.name,
            "status": "Provisioning"
        }).insert(ignore_permissions=True)

        res = optimize("Email Template", template.name)
        self.assertEqual(res.get("status"), "failed")
        self.assertIn("No active Multi Channel Cadence", res.get("error"))

    @patch("frappe.utils.redis_wrapper.RedisWrapper.xadd")
    @patch("frappe.publish_realtime")
    @patch("frappe_cadence.cadence.doctype.history.history.get_history")
    @patch("frappe_cadence.integrations.n8n.requests.post")
    def test_optimize_success_and_callback(self, mock_post, mock_get_history, mock_publish, mock_xadd):
        mock_get_history.return_value = []

        template = frappe.get_doc({
            "doctype": "Email Template",
            "name": "N8N Test Optimize Real Payload Email",
            "__newname": "N8N Test Optimize Real Payload Email",
            "title": "N8N Test Optimize Real Payload Email",
            "subject": "Real Subject",
            "provider": "n8n",
            "enabled": 1,
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        cadence = frappe.get_doc({
            "doctype": "Cadence",
            "cadence_name": "N8N Test Cadence Active",
            "cadence_code": "CAD-TEST-ACTIVE-001",
            "cadence_schedules": [
                {
                    "reference_doctype": "Email Template",
                    "reference_name": template.name,
                    "send_after_days": 1
                }
            ]
        }).insert(ignore_permissions=True)

        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "lead_name": "N8N Lead Active",
            "first_name": "N8N Active",
            "email_id": "n8n_active_lead@example.com"
        }).insert(ignore_permissions=True)

        mcc = frappe.get_doc({
            "doctype": "Multi Channel Cadence",
            "cadence_name": cadence.name,
            "cadence_for": "CRM Lead",
            "recipient": lead.name,
            "status": "Scheduled"
        }).insert(ignore_permissions=True)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = optimize("Email Template", template.name)
        self.assertEqual(res.get("status"), "success")

        template.reload()
        self.assertEqual(template.status, "Optimizing")

        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        # Should call test_request_url
        self.assertEqual(called_url, "https://n8n.capybaara.com/webhook-test/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        # Verify Communication draft was created
        schedule_name = cadence.cadence_schedules[0].name
        comm = frappe.get_doc("Communication", {
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": mcc.name,
            "cadence_schedule": schedule_name
        })
        self.assertTrue(comm.name)

        # Test callback resets template status
        callback_payload = {
            "type": "response.completed",
            "metadata": {
                "name": comm.name
            },
            "data": [{
                "content": [{
                    "text": '{"subject": "Generated Subject", "content": "Generated Content"}'
                }]
            }]
        }

        with patch("frappe.request", MagicMock(json=callback_payload)):
            cb_res = handle_callback()
            self.assertEqual(cb_res.get("status"), "success")

        comm.reload()
        self.assertEqual(comm.subject, "Generated Subject")
        self.assertEqual(comm.content, "Generated Content")

        template.reload()
        self.assertEqual(template.status, "Enabled")

    @patch("frappe.utils.redis_wrapper.RedisWrapper.xadd")
    @patch("frappe.publish_realtime")
    @patch("frappe_cadence.cadence.doctype.history.history.get_history")
    @patch("frappe_cadence.integrations.n8n.requests.post")
    def test_n8n_optimize_reverts_status_on_failure(self, mock_post, mock_get_history, mock_publish, mock_xadd):
        mock_get_history.return_value = []

        template = frappe.get_doc({
            "doctype": "Email Template",
            "name": "N8N Test Optimize Failure Revert Email",
            "__newname": "N8N Test Optimize Failure Revert Email",
            "title": "N8N Test Optimize Failure Revert Email",
            "subject": "Failure Revert Subject",
            "provider": "n8n",
            "enabled": 1,
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/invalid-url")

        cadence = frappe.get_doc({
            "doctype": "Cadence",
            "cadence_name": "N8N Test Cadence Fail",
            "cadence_code": "CAD-TEST-FAIL-001",
            "cadence_schedules": [
                {
                    "reference_doctype": "Email Template",
                    "reference_name": template.name,
                    "send_after_days": 1
                }
            ]
        }).insert(ignore_permissions=True)

        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "lead_name": "N8N Lead Fail",
            "first_name": "N8N Fail",
            "email_id": "n8n_fail_lead@example.com"
        }).insert(ignore_permissions=True)

        mcc = frappe.get_doc({
            "doctype": "Multi Channel Cadence",
            "cadence_name": cadence.name,
            "cadence_for": "CRM Lead",
            "recipient": lead.name,
            "status": "Scheduled"
        }).insert(ignore_permissions=True)

        mock_post.side_effect = Exception("Connection timed out")

        res = optimize("Email Template", template.name)
        self.assertEqual(res.get("status"), "failed")

        template.reload()
        self.assertEqual(template.status, "Enabled")

