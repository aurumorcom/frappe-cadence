import json
import unittest
from frappe_cadence._template import ParsedWebhookPayload, extract_output_text, extract_agent_name

class TestWebhookPayload(unittest.TestCase):
    def test_payload_started_event(self):
        raw = {
            "success": True,
            "type": "agent.started",
            "id": "wm-job-101",
            "webhookId": "wh-001",
            "data": []
        }
        payload = ParsedWebhookPayload(raw)
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
        payload = ParsedWebhookPayload(raw)
        self.assertFalse(payload.is_started)
        self.assertTrue(payload.is_completed)
        self.assertFalse(payload.is_failed)

    def test_payload_completed_event_with_completed_string(self):
        raw = {
            "success": True,
            "type": "completed",
            "data": [{"text": "Sample"}]
        }
        payload = ParsedWebhookPayload(raw)
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
        payload = ParsedWebhookPayload(raw)
        self.assertFalse(payload.is_started)
        self.assertFalse(payload.is_completed)
        self.assertTrue(payload.is_failed)
        self.assertEqual(payload.error, "Execution Timeout")

    def test_payload_failure_by_success_false_even_without_type(self):
        raw = {
            "success": False,
            "error": "Generic error"
        }
        payload = ParsedWebhookPayload(raw)
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
        payload = ParsedWebhookPayload(raw)
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
