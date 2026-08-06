import frappe
from unittest.mock import patch, MagicMock
from frappe.tests import IntegrationTestCase
from frappe_cadence.integrations.n8n import (
    get_test_request_url,
    optimize,
    optimize_callback,
    predict,
    predict_callback
)

class TestN8NIntegration(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    def test_get_test_request_url(self):
        prod_url = "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d"
        expected_test_url = "https://n8n.capybaara.com/webhook-test/ce63ee3b-90f5-41cb-9538-1418302eac7d"
        self.assertEqual(get_test_request_url(prod_url), expected_test_url)

        custom_url = "https://example.com/custom-endpoint"
        self.assertEqual(get_test_request_url(custom_url), custom_url)
        self.assertEqual(get_test_request_url(""), "")

    @patch("frappe.utils.redis_wrapper.RedisWrapper.xadd")
    @patch("frappe.publish_realtime")
    @patch("frappe_cadence.integrations.n8n.requests.post")
    def test_optimize_success(self, mock_post, mock_publish, mock_xadd):
        template = frappe.get_doc({
            "doctype": "SMS Template",
            "name": "N8N Test Optimize SMS",
            "title": "N8N Test Optimize SMS",
            "provider": "n8n",
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")
        template.reload()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = optimize("SMS Template", template.name)
        self.assertEqual(res.get("status"), "success")

        template.reload()
        self.assertEqual(template.status, "Optimizing")

        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, "https://n8n.capybaara.com/webhook-test/ce63ee3b-90f5-41cb-9538-1418302eac7d")

    @patch("frappe.utils.redis_wrapper.RedisWrapper.xadd")
    @patch("frappe.publish_realtime")
    @patch("frappe_cadence.integrations.n8n.requests.post")
    def test_optimize_graceful_failure(self, mock_post, mock_publish, mock_xadd):
        template = frappe.get_doc({
            "doctype": "SMS Template",
            "name": "N8N Test Fail SMS",
            "title": "N8N Test Fail SMS",
            "provider": "n8n",
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")
        template.reload()

        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("n8n test workflow not listening")

        res = optimize("SMS Template", template.name)
        self.assertEqual(res.get("status"), "failed")
        self.assertIn("not listening", res.get("error"))

        template.reload()
        self.assertEqual(template.status, "Enabled")

    @patch("frappe.utils.redis_wrapper.RedisWrapper.xadd")
    @patch("frappe.publish_realtime")
    @patch("frappe_cadence.cadence.doctype.history.history.get_history")
    @patch("frappe_cadence.integrations.n8n.requests.post")
    def test_predict_and_callback(self, mock_post, mock_get_history, mock_publish, mock_xadd):
        mock_get_history.return_value = []

        template = frappe.get_doc({
            "doctype": "Email Template",
            "name": "N8N Test Predict Email",
            "title": "N8N Test Predict Email",
            "subject": "N8N Test Subject",
            "provider": "n8n",
            "status": "Enabled"
        }).insert(ignore_permissions=True)
        template.db_set("request_url", "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "lead_name": "N8N Lead Email",
            "first_name": "N8N",
            "email_id": "n8n_lead_email@example.com"
        }).insert(ignore_permissions=True)

        annotation = frappe.get_doc({
            "doctype": "Email Template Annotation",
            "parent": template.name,
            "parentfield": "annotations",
            "parenttype": "Email Template",
            "reference_doctype": "CRM Lead",
            "reference_name": lead.name,
            "sender": "Administrator"
        }).insert(ignore_permissions=True)

        template.reload()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = predict("Email Template", template.name)
        self.assertEqual(res.get("status"), "success")

        template.reload()
        self.assertEqual(template.status, "Predicting")

        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, "https://n8n.capybaara.com/webhook/ce63ee3b-90f5-41cb-9538-1418302eac7d")

        # Test predict_callback
        callback_payload = {
            "type": "response.completed",
            "metadata": {
                "name": annotation.name,
                "doctype": annotation.doctype
            },
            "data": [{
                "content": [{
                    "text": '{"subject": "N8N Predicted Subject", "body": "N8N Predicted Body"}'
                }]
            }]
        }

        cb_res = predict_callback(**callback_payload)
        self.assertEqual(cb_res.get("status"), "success")

        annotation.reload()
        self.assertEqual(annotation.subject, "N8N Predicted Subject")
        self.assertEqual(annotation.body, "N8N Predicted Body")
