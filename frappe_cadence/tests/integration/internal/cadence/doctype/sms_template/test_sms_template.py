# Copyright (c) 2026, Aurumor and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestSMSTemplate(IntegrationTestCase):
	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def setUp(self):
		super().setUp()

	def tearDown(self):
		frappe.db.rollback()
		super().tearDown()

	"""
	Integration tests for SMSTemplate.
	Use this class for testing interactions between multiple components.
	"""

	@patch("frappe.log_error")
	@patch("frappe_cadence._template.emit_event")
	@patch("frappe_cadence._template.frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_sift_callback_failure_recovery(self, mock_exists, mock_get_doc, mock_emit, mock_log_error):
		from frappe_cadence.sms_template import callback
		from unittest.mock import MagicMock
		frappe.local.request = frappe._dict(json={
			"type": "response.failed",
			"metadata": {"name": "COMM-001"},
			"error": "Sift Generation Failed"
		})
		mock_comm = MagicMock()
		mock_get_doc.return_value = mock_comm

		result = callback()

		self.assertEqual(result.get("status"), "failed")
		mock_comm.save.assert_not_called()
		mock_emit.assert_called_once_with("callback", {"communication_id": "COMM-001", "error": "Sift Generation Failed"})

	def test_sift_id_in_sms_template(self):
		import frappe
		doc = frappe.get_doc({
			"doctype": "SMS Template",
			"title": "_Test SMS Template",
			"status": "Enabled",
			"message": "Hello from SMS",
			"sift_id": "sift_sms_123"
		}).insert(ignore_permissions=True)
		
		reloaded_doc = frappe.get_doc("SMS Template", doc.name)
		self.assertEqual(reloaded_doc.sift_id, "sift_sms_123")
		
		meta = frappe.get_meta("SMS Template")
		field = meta.get_field("sift_id")
		self.assertIsNotNone(field)
