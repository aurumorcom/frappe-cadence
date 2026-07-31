# Copyright (c) 2024, Roo and contributors
# For license information, please see license.txt

from unittest.mock import MagicMock, patch
import requests
import frappe
from frappe.tests import IntegrationTestCase

class TestHistory(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def tearDown(self):
		frappe.db.rollback()
		super().tearDown()

	def test_history_schema(self):
		# Create a dummy reference document or just use a generic one
		# History can be created standalone to test the schema
		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com",
			"markdown": "Test history content",
			"html": "<p>Test history content</p>",
			"screenshot": "/files/test_image.png"
		}).insert()

		# Verify that fields were saved correctly
		self.assertEqual(history_doc.url, "https://example.com")
		self.assertEqual(history_doc.markdown, "Test history content")
		self.assertEqual(history_doc.screenshot, "/files/test_image.png")

	def test_history_group_schema(self):
		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com/hist1",
			"markdown": "Content"
		}).insert()

		group_doc = frappe.get_doc({
			"doctype": "History Group",
			"url": "https://example.com",
			"history": [
				{
					"history": history_doc.name
				}
			]
		}).insert()

		self.assertEqual(group_doc.url, "https://example.com")
		self.assertTrue(group_doc.name.startswith("HIST-GRP-"))
		self.assertEqual(len(group_doc.history), 1)
		self.assertEqual(group_doc.history[0].history, history_doc.name)

	def test_get_history_integration(self):
		from frappe.utils import add_months, today
		from frappe_cadence.cadence.doctype.history.history import get_history
		
		# Create a dummy CRM Lead
		lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "Test History Lead"
		}).insert(ignore_permissions=True)
		
		# Create a History record
		hist1 = frappe.get_doc({
			"doctype": "History",
			"reference_doctype": "CRM Lead",
			"reference_name": lead.name,
			"markdown": "**Bold interaction**"
		}).insert(ignore_permissions=True)
		
		# Test fetch
		since = add_months(today(), -1)
		messages = get_history("CRM Lead", lead.name, since_date=since)
		
		# Validate that messages are constructed correctly
		self.assertTrue(len(messages) >= 1)
		
		# The output of get_history is [{"role": "user", "content": [{"type": "text", "text": "..."}]}]
		has_content = False
		for m in messages:
			for c in m["content"]:
				if c["type"] == "text" and "Bold interaction" in c["text"]:
					has_content = True
					break
		
		self.assertTrue(has_content)

	@patch("requests.get")
	def test_screenshot_url_download_on_create(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.content = b"fake_png_data"
		mock_get.return_value = mock_response

		presigned_url = "https://storage.googleapis.com/bucket/sample_screen.png?X-Amz-Expires=3600"
		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com",
			"screenshot": presigned_url
		}).insert()

		mock_get.assert_called_once_with(presigned_url, timeout=10)
		self.assertTrue(history_doc.screenshot.startswith("/files/"))
		self.assertTrue(frappe.db.exists("File", {"file_url": history_doc.screenshot, "is_private": 0}))

	@patch("requests.get")
	def test_screenshot_url_download_on_update(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.content = b"fake_updated_data"
		mock_get.return_value = mock_response

		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com"
		}).insert()

		updated_presigned_url = "https://storage.googleapis.com/bucket/updated_screen.png?X-Amz-Expires=3600"
		history_doc.screenshot = updated_presigned_url
		history_doc.save()

		mock_get.assert_called_once_with(updated_presigned_url, timeout=10)
		self.assertTrue(history_doc.screenshot.startswith("/files/"))
		self.assertTrue(frappe.db.exists("File", {"file_url": history_doc.screenshot, "is_private": 0}))

	@patch("requests.get")
	def test_filename_extraction_from_complex_presigned_url(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.content = b"complex_url_data"
		mock_get.return_value = mock_response

		complex_url = (
			"https://storage.googleapis.com/koda-asia-south1-bucket-iazx11/"
			"69916db138be40dab4c8396547cfed02_bd8c77b3c5c846189a288d2382861fad.png?"
			"X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=GOOG1EDLJCUNLBUXXQTA4QXQQHSDRMDNO7N6NDJNDRYCL62VFYKQDFK7KVHTZ"
			"%2F20260729%2Fasia-south1%2Fs3%2Faws4_request&X-Amz-Date=20260729T113037Z&X-Amz-Expires=3600"
		)

		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com",
			"screenshot": complex_url
		}).insert()

		file_doc = frappe.get_doc("File", {"file_url": history_doc.screenshot})
		self.assertTrue(file_doc.file_name.startswith("69916db138be40dab4c8396547cfed02_bd8c77b3c5c846189a288d2382861fad"))
		self.assertTrue(file_doc.file_name.endswith(".png"))
		self.assertEqual(file_doc.is_private, 0)

	@patch("requests.get")
	def test_duplicate_file_handling(self, mock_get):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_response.content = b"duplicate_data"
		mock_get.return_value = mock_response

		url_1 = "https://storage.googleapis.com/bucket/dup_image.png?token=1"
		url_2 = "https://storage.googleapis.com/bucket/dup_image.png?token=2"

		doc1 = frappe.get_doc({"doctype": "History", "screenshot": url_1}).insert()
		doc2 = frappe.get_doc({"doctype": "History", "screenshot": url_2}).insert()

		self.assertTrue(doc1.screenshot.startswith("/files/"))
		self.assertTrue(doc2.screenshot.startswith("/files/"))
		self.assertTrue(frappe.db.exists("File", {"file_url": doc1.screenshot}))
		self.assertTrue(frappe.db.exists("File", {"file_url": doc2.screenshot}))

	@patch("requests.get")
	def test_screenshot_local_path_ignored(self, mock_get):
		history_doc = frappe.get_doc({
			"doctype": "History",
			"screenshot": "/files/already_local.png"
		}).insert()

		mock_get.assert_not_called()
		self.assertEqual(history_doc.screenshot, "/files/already_local.png")

	@patch("requests.get")
	def test_screenshot_download_failure_graceful(self, mock_get):
		mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

		remote_url = "https://storage.googleapis.com/bucket/timeout_image.png"
		history_doc = frappe.get_doc({
			"doctype": "History",
			"screenshot": remote_url
		}).insert()

		# Document creation should succeed, keeping original URL
		self.assertEqual(history_doc.screenshot, remote_url)

	def test_history_and_group_hash_autoname(self):
		history_doc = frappe.get_doc({
			"doctype": "History",
			"url": "https://example.com/hash_test",
			"markdown": "Hash test markdown"
		}).insert()

		group_doc = frappe.get_doc({
			"doctype": "History Group",
			"url": "https://example.com/hash_group_test",
			"history": [{"history": history_doc.name}]
		}).insert()

		self.assertEqual(len(history_doc.name), 10)
		self.assertEqual(len(group_doc.name), 10)
		self.assertFalse(history_doc.name.startswith("HIST-"))
		self.assertFalse(group_doc.name.startswith("HIST-GRP-"))
