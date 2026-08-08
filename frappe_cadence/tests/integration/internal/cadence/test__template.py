from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock
import frappe
from frappe_cadence._template import handle_callback

class TestTemplateIntegration(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for ps_name, fieldname, prop, val, ptype in [
            ("Email Template-subject-reqd", "subject", "reqd", "0", "Check"),
            ("Email Template-subject-mandatory_depends_on", "subject", "mandatory_depends_on", "eval:!doc.provider || doc.provider == 'Frappe'", "Data"),
            ("Email Template-response-reqd", "response", "reqd", "0", "Check"),
            ("Email Template-response-mandatory_depends_on", "response", "mandatory_depends_on", "eval:(!doc.provider || doc.provider == 'Frappe') && !doc.use_html", "Data"),
        ]:
            if not frappe.db.exists("Property Setter", ps_name):
                frappe.get_doc({
                    "doctype": "Property Setter",
                    "doc_type": "Email Template",
                    "doctype_or_field": "DocField",
                    "field_name": fieldname,
                    "property": prop,
                    "property_type": ptype,
                    "value": val,
                    "module": "Cadence"
                }).insert(ignore_permissions=True)
            else:
                frappe.db.set_value("Property Setter", ps_name, "value", val)
        frappe.clear_cache(doctype="Email Template")

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    def test_callback_emits_event(self, mock_get_doc, mock_emit_event):
        # Mock payload with WebhookResponse schema, 5-part email schema, and Markdown
        frappe.local.request = frappe._dict(json={
            "success": True,
            "type": "response.completed",
            "id": "wm-job-001",
            "webhookId": "wh-001",
            "metadata": {
                "name": "COMM-001"
            },
            "data": [
                {
                    "content": [
                        {
                            "text": "{\"subject\": \"Hello\", \"salutation\": \"Dear **John**,\", \"body\": \"Welcome to *our* service.\", \"call_to_action\": \"Click [here](https://example.com).\", \"sign_off\": \"Best,\\n**Team**\"}"
                        }
                    ]
                }
            ]
        })
        
        mock_comm = MagicMock()
        mock_comm.communication_medium = "Email"
        mock_comm.name = "COMM-001"
        mock_comm.doctype = "Communication"
        mock_comm.cadence_schedule = None
        mock_comm.as_dict.return_value = {
            "name": "COMM-001",
            "doctype": "Communication",
            "subject": "Hello",
            "delivery_status": "Scheduled"
        }
        mock_get_doc.return_value = mock_comm
        
        result = handle_callback()
        
        self.assertEqual(result.get("name"), "COMM-001")
        self.assertEqual(result.get("doctype"), "Communication")
        self.assertEqual(mock_comm.subject, "Hello")
        self.assertIn('<p>Dear <strong>John</strong>,</p>', mock_comm.content)
        self.assertIn("<em>our</em>", mock_comm.content)
        self.assertIn('href="https://example.com"', mock_comm.content)
        mock_comm.save.assert_called_once_with(ignore_permissions=True)
        
        mock_emit_event.assert_called_once_with("callback", {"communication_id": "COMM-001"})

    def test_callback_missing_communication_id(self):
        frappe.local.request = frappe._dict(json={
            "success": True,
            "metadata": {},
            "data": [{"content": [{"text": "{}"}]}]
        })
        result = handle_callback()
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("message"), "Missing communication_id in metadata")

    def test_callback_missing_output_text(self):
        frappe.local.request = frappe._dict(json={
            "success": True,
            "metadata": {"name": "COMM-001"},
            "data": [{"content": [{}]}]
        })
        result = handle_callback()
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("message"), "Missing output text")

    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    @patch("frappe.db.exists", return_value=True)
    def test_callback_invalid_json_fallback_to_content(self, mock_exists, mock_get_doc, mock_emit_event):
        frappe.local.request = frappe._dict(json={
            "success": True,
            "type": "response.completed",
            "metadata": {"name": "COMM-001"},
            "data": [{"content": [{"text": "{ invalid json }"}]}]
        })
        mock_comm = MagicMock()
        mock_comm.communication_medium = "Email"
        mock_comm.cadence_schedule = None
        mock_comm.as_dict.return_value = {"name": "COMM-001", "content": "<p>{ invalid json }</p>"}
        mock_get_doc.return_value = mock_comm

        result = handle_callback()
        self.assertEqual(result.get("name"), "COMM-001")
        self.assertIn("{ invalid json }", mock_comm.content)

    def test_sift_id_in_email_template(self):
        doc = frappe.get_doc({
            "doctype": "Email Template",
            "name": "_Test Email Template",
            "subject": "_Test Email Subject",
            "response": "Hello from Email",
            "sift_id": "sift_email_123"
        }).insert(ignore_permissions=True)
        
        reloaded_doc = frappe.get_doc("Email Template", doc.name)
        self.assertEqual(reloaded_doc.sift_id, "sift_email_123")
        
        meta = frappe.get_meta("Email Template")
        field = meta.get_field("sift_id")
        self.assertIsNotNone(field)

    @patch("frappe_controller.utils.controller.emit_event")
    def test_emit_event_on_template_enable(self, mock_emit):
        if not frappe.db.exists("Email Template", "Test Event Emit Template"):
            doc = frappe.get_doc({
                "doctype": "Email Template",
                "name": "Test Event Emit Template",
                "subject": "Test",
                "response": "Test Content",
                "status": "Disabled"
            }).insert(ignore_permissions=True)
        else:
            doc = frappe.get_doc("Email Template", "Test Event Emit Template")
            doc.status = "Disabled"
            doc.save(ignore_permissions=True)
            
        mock_emit.reset_mock()
        
        # Change status to Enabled
        doc.status = "Enabled"
        doc.save(ignore_permissions=True)
        
        # Standard frappe_controller doc event should be emitted; dirty custom event should NOT be emitted
        emitted_keys = [call[1].get("key") if "key" in call[1] else call[0][0] for call in mock_emit.call_args_list if call[0] or call[1]]
        self.assertIn("doc:Email Template:on_update", emitted_keys)
        self.assertNotIn("email_template_enabled", emitted_keys)

    @patch("frappe.log_error")
    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    @patch("frappe.db.exists", return_value=True)
    def test_sift_callback_failure_recovery(self, mock_exists, mock_get_doc, mock_emit, mock_log_error):
        frappe.local.request = frappe._dict(json={
            "success": False,
            "type": "response.failed",
            "metadata": {"name": "COMM-001"},
            "error": "Sift Generation Failed"
        })
        mock_comm = MagicMock()
        mock_comm.cadence_schedule = None
        mock_comm.as_dict.return_value = {
            "name": "COMM-001",
            "doctype": "Communication",
            "delivery_status": "Failed"
        }
        mock_get_doc.return_value = mock_comm

        result = handle_callback()

        self.assertEqual(result.get("status"), "failed")
        mock_comm.save.assert_not_called()
        mock_emit.assert_called_once_with("callback", {"communication_id": "COMM-001", "error": "Sift Generation Failed"})

    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    def test_callback_with_dict_text_payload(self, mock_get_doc, mock_emit_event):
        frappe.local.request = frappe._dict(json={
            "success": True,
            "type": "response.completed",
            "metadata": {"name": "COMM-002"},
            "data": [
                {
                    "content": [
                        {
                            "type": "text",
                            "text": {
                                "subject": "Dict Subject",
                                "content": "Dict Content Body"
                            }
                        }
                    ]
                }
            ]
        })
        mock_comm = MagicMock()
        mock_comm.communication_medium = "Email"
        mock_comm.name = "COMM-002"
        mock_comm.doctype = "Communication"
        mock_comm.cadence_schedule = None
        mock_comm.as_dict.return_value = {"name": "COMM-002", "subject": "Dict Subject"}
        mock_get_doc.return_value = mock_comm

        result = handle_callback()
        self.assertEqual(result.get("name"), "COMM-002")
        self.assertEqual(mock_comm.subject, "Dict Subject")
        self.assertIn("Dict Content Body", mock_comm.content)

    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    def test_callback_with_form_data_payload(self, mock_get_doc, mock_emit_event):
        import json
        frappe.local.request = MagicMock()
        frappe.local.request.get_json.return_value = None  # Form data request (non-JSON header)
        frappe.local.form_dict = frappe._dict({
            "success": "true",
            "metadata": json.dumps({"name": "COMM-003"}),
            "data": json.dumps([{"content": [{"text": {"subject": "Form Sub", "content": "Form Body"}}]}]),
            "webhookId": "wh-form-1"
        })
        mock_comm = MagicMock()
        mock_comm.communication_medium = "Email"
        mock_comm.name = "COMM-003"
        mock_comm.doctype = "Communication"
        mock_comm.cadence_schedule = None
        mock_comm.as_dict.return_value = {"name": "COMM-003", "subject": "Form Sub"}
        mock_get_doc.return_value = mock_comm

        result = handle_callback()
        self.assertEqual(result.get("name"), "COMM-003")
        self.assertEqual(mock_comm.subject, "Form Sub")
        self.assertIn("Form Body", mock_comm.content)

    @patch("frappe_cadence._template.emit_event")
    @patch("frappe_cadence._template.frappe.get_doc")
    def test_callback_emits_cadence_step_completed(self, mock_get_doc, mock_emit_event):
        frappe.local.request = frappe._dict(json={
            "success": True,
            "type": "response.completed",
            "metadata": {
                "communication_id": "COMM-MCC-001"
            },
            "data": [{"content": [{"text": "{\"subject\": \"Generated Subject\", \"body\": \"Generated Content\"}"}]}]
        })

        mock_comm = MagicMock()
        mock_comm.communication_medium = "Email"
        mock_comm.name = "COMM-MCC-001"
        mock_comm.doctype = "Communication"
        mock_comm.reference_doctype = "Multi Channel Cadence"
        mock_comm.reference_name = "MCC-2026-00001"
        mock_comm.cadence_schedule = "SCHED-001"
        mock_comm.as_dict.return_value = {
            "name": "COMM-MCC-001",
            "doctype": "Communication",
            "delivery_status": "Scheduled"
        }
        mock_get_doc.return_value = mock_comm

        result = handle_callback()

        self.assertEqual(result.get("name"), "COMM-MCC-001")
        self.assertEqual(mock_comm.delivery_status, "Scheduled")
        mock_emit_event.assert_any_call("cadence_step_completed", {
            "cadence_name": "MCC-2026-00001",
            "schedule_name": "SCHED-001"
        })
        mock_emit_event.assert_any_call("callback", {"communication_id": "COMM-MCC-001"})

    def test_n8n_and_dspy_template_creation_without_subject(self):
        doc = frappe.get_doc({
            "doctype": "Email Template",
            "name": "_Test Optional n8n Template",
            "provider": "n8n",
            "request_url": "https://n8n.example.com/webhook/123",
            "status": "Disabled"
        }).insert(ignore_permissions=True)
        self.assertTrue(doc.name)
        self.assertEqual(doc.provider, "n8n")

    def test_all_templates_enabled_field_exists(self):
        for doctype in ["Email Template", "SMS Template", "WhatsApp Template", "LinkedIn Template"]:
            meta = frappe.get_meta(doctype)
            self.assertIsNotNone(meta.get_field("enabled"), f"enabled field missing on {doctype}")

    def test_email_template_enabled_status_sync(self):
        doc = frappe.get_doc({
            "doctype": "Email Template",
            "name": "Test Enabled Sync Template",
            "subject": "Test Sync",
            "response": "Content Sync",
            "enabled": 1
        }).insert(ignore_permissions=True)
        self.assertEqual(doc.status, "Enabled")

        doc.enabled = 0
        doc.save(ignore_permissions=True)
        self.assertEqual(doc.status, "Disabled")

        doc.enabled = 1
        doc.save(ignore_permissions=True)
        self.assertEqual(doc.status, "Enabled")

    def test_link_search_includes_enabled_template(self):
        doc = frappe.get_doc({
            "doctype": "Email Template",
            "name": "Test Search Link Enabled Template",
            "subject": "Test Search",
            "response": "Content Search",
            "enabled": 1
        }).insert(ignore_permissions=True)

        from frappe.desk.search import search_link
        results = search_link(
            doctype="Email Template",
            txt="Test Search Link Enabled Template",
            query=None,
            filters=None
        )
        result_names = [r[0] if isinstance(r, (list, tuple)) else r.get("value") for r in results]
        self.assertIn(doc.name, result_names)

    def test_link_search_includes_disabled_template_when_flag_set(self):
        doc = frappe.get_doc({
            "doctype": "Email Template",
            "name": "Test Search Link Disabled Template",
            "subject": "Test Search Disabled",
            "response": "Content Search Disabled",
            "enabled": 0
        }).insert(ignore_permissions=True)

        from frappe.desk.search import search_link
        # Standard search without include_disabled=1 should NOT return disabled template
        std_results = search_link(
            doctype="Email Template",
            txt="Test Search Link Disabled Template",
            query=None,
            filters=None
        )
        std_result_names = [r[0] if isinstance(r, (list, tuple)) else r.get("value") for r in std_results]
        self.assertNotIn(doc.name, std_result_names)

        # Search with include_disabled=1 MUST return disabled template
        disabled_results = search_link(
            doctype="Email Template",
            txt="Test Search Link Disabled Template",
            query=None,
            filters={"include_disabled": 1}
        )
        disabled_result_names = [r[0] if isinstance(r, (list, tuple)) else r.get("value") for r in disabled_results]
        self.assertIn(doc.name, disabled_result_names)
