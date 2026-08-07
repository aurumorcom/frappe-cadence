import json
import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe_cadence._template import (
    WebhookResponse,
    extract_output_text,
    extract_agent_name,
    get_raw_payload,
    update_annotation_output
)

class TestTemplate(unittest.TestCase):
    def test_payload_started_event(self):
        raw = {
            "success": True,
            "type": "agent.started",
            "id": "wm-job-101",
            "webhookId": "wh-001",
            "data": []
        }
        payload = WebhookResponse(raw)
        self.assertTrue(payload.is_started)
        self.assertFalse(payload.is_completed)
        self.assertFalse(payload.is_failed)
        self.assertEqual(payload.id, "wm-job-101")
        self.assertEqual(payload.webhook_id, "wh-001")

    def test_payload_completed_event_with_success_true(self):
        raw = {
            "success": True,
            "type": "email_template.complete",
            "id": "wm-job-102",
            "webhookId": "wh-002",
            "data": [{"content": [{"text": "Hello world"}]}]
        }
        payload = WebhookResponse(raw)
        self.assertFalse(payload.is_started)
        self.assertTrue(payload.is_completed)
        self.assertFalse(payload.is_failed)

    def test_payload_completed_event_with_completed_string(self):
        raw = {
            "success": True,
            "type": "completed",
            "data": [{"text": "Sample"}]
        }
        payload = WebhookResponse(raw)
        self.assertFalse(payload.is_started)
        self.assertTrue(payload.is_completed)
        self.assertFalse(payload.is_failed)

    def test_payload_failed_event_with_error_string(self):
        raw = {
            "success": False,
            "type": "email_template.failed",
            "error": "Execution Timeout",
            "data": []
        }
        payload = WebhookResponse(raw)
        self.assertFalse(payload.is_started)
        self.assertFalse(payload.is_completed)
        self.assertTrue(payload.is_failed)
        self.assertEqual(payload.error, "Execution Timeout")

    def test_payload_failure_by_success_false_even_without_type(self):
        raw = {
            "success": False,
            "error": "Generic error"
        }
        payload = WebhookResponse(raw)
        self.assertFalse(payload.is_started)
        self.assertFalse(payload.is_completed)
        self.assertTrue(payload.is_failed)

    def test_payload_stringified_metadata_and_data(self):
        raw = {
            "success": True,
            "type": "completed",
            "metadata": json.dumps({"name": "COMM-001", "doctype": "Communication"}),
            "data": json.dumps([{"content": [{"text": "Parsed Output"}]}])
        }
        payload = WebhookResponse(raw)
        self.assertEqual(payload.metadata.get("name"), "COMM-001")
        self.assertEqual(payload.metadata.get("doctype"), "Communication")
        self.assertIsInstance(payload.data, list)
        self.assertEqual(extract_output_text(payload.data), "Parsed Output")

    def test_extract_output_text_nested_content(self):
        # Case 1: Array of dicts with content array
        data1 = [{"content": [{"text": "Text 1"}]}]
        self.assertEqual(extract_output_text(data1), "Text 1")

        # Case 2: Dict with content array
        data2 = {"content": [{"text": "Text 2"}]}
        self.assertEqual(extract_output_text(data2), "Text 2")

        # Case 3: Dict with direct text
        data3 = {"text": "Text 3"}
        self.assertEqual(extract_output_text(data3), "Text 3")

        # Case 4: Dict with output field
        data4 = {"output": "Text 4"}
        self.assertEqual(extract_output_text(data4), "Text 4")

        # Case 5: Stringified JSON
        data5 = json.dumps({"content": [{"text": "Text 5"}]})
        self.assertEqual(extract_output_text(data5), "Text 5")

        # Case 6: Direct raw text string
        data6 = "Raw string text"
        self.assertEqual(extract_output_text(data6), "Raw string text")

        # Case 7: Text field is a dict (n8n/LLM object output)
        dict_text = {"subject": "Sub 7", "content": "Content 7"}
        data7 = [{"content": [{"type": "text", "text": dict_text}]}]
        self.assertEqual(extract_output_text(data7), dict_text)

        # Case 8: Stringified JSON inside text field
        json_str_text = json.dumps({"subject": "Sub 8", "content": "Content 8"})
        data8 = [{"content": [{"type": "text", "text": json_str_text}]}]
        self.assertEqual(extract_output_text(data8), {"subject": "Sub 8", "content": "Content 8"})

    def test_extract_agent_name(self):
        # Case 1: List with agent_name
        data1 = [{"agent_name": "agent-sift-001"}]
        self.assertEqual(extract_agent_name(data1), "agent-sift-001")

        # Case 2: Dict with agent_name
        data2 = {"agent_name": "agent-sift-002"}
        self.assertEqual(extract_agent_name(data2), "agent-sift-002")

        # Case 3: List with sift_id
        data3 = [{"sift_id": "agent-sift-003"}]
        self.assertEqual(extract_agent_name(data3), "agent-sift-003")

        # Case 4: Stringified JSON
        data4 = json.dumps({"agent_name": "agent-sift-004"})
        self.assertEqual(extract_agent_name(data4), "agent-sift-004")

    def test_get_raw_payload_with_kwargs(self):
        kwargs = {"success": True, "metadata": {"name": "COMM-100"}}
        self.assertEqual(get_raw_payload(kwargs), kwargs)

    def test_get_raw_payload_with_form_dict_fallback_when_non_json_request(self):
        mock_req = MagicMock()
        mock_req.get_json.return_value = None  # Non-JSON content type (form-data)
        with patch.object(frappe, "request", mock_req), patch.object(frappe, "form_dict", {"metadata": "COMM-200"}):
            payload = get_raw_payload()
            self.assertEqual(payload, {"metadata": "COMM-200"})

    def test_update_annotation_output_with_dict(self):
        mock_db = MagicMock()
        with patch.object(frappe, "db", mock_db):
            output_dict = {"subject": "Ann Sub", "body": "Ann Body"}
            res = update_annotation_output("Email Template Annotation", "ANN-001", output_dict)
            self.assertTrue(res)
            mock_db.set_value.assert_any_call("Email Template Annotation", "ANN-001", "subject", "Ann Sub")
            mock_db.set_value.assert_any_call("Email Template Annotation", "ANN-001", "body", "Ann Body")
