# Copyright (c) 2024, Roo and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from frappe.utils.file_manager import save_file


class History(Document):
	def validate(self):
		self.download_screenshot_if_url()

	def download_screenshot_if_url(self):
		if not self.screenshot:
			return

		if self.screenshot.startswith("http://") or self.screenshot.startswith("https://"):
			if frappe.db.exists("File", {"file_url": self.screenshot}):
				return

			try:
				response = requests.get(self.screenshot, timeout=10)
				if response.status_code == 200:
					clean_url = self.screenshot.split("?")[0]
					clean_filename = clean_url.split("/")[-1] or f"{self.name or 'screenshot'}.png"

					file_doc = save_file(
						fname=clean_filename,
						content=response.content,
						dt=self.doctype,
						dn=self.name,
						is_private=0,
					)

					self.screenshot = file_doc.file_url
			except Exception as e:
				frappe.log_error(f"Failed to download screenshot: {e}", "History Screenshot Download Error")


@frappe.whitelist()
def get_history(reference_doctype: str, reference_name: str, since_date=None) -> list:
	from frappe.utils import add_months, today

	if not since_date:
		since_date = add_months(today(), -3)

	or_filters = {reference_doctype: reference_name}
	if reference_doctype == "CRM Lead":
		lead = frappe.get_doc("CRM Lead", reference_name)
		if lead.organization:
			or_filters["CRM Organization"] = lead.organization

	histories = []
	for ref_dt, ref_name in or_filters.items():
		histories.extend(
			frappe.get_all(
				"History",
				filters={
					"reference_doctype": ref_dt,
					"reference_name": ref_name,
					"creation": [">=", since_date],
				},
				fields=["name", "markdown", "screenshot", "creation"],
				order_by="creation asc",
			)
		)

	# Sort the combined histories by creation date
	histories.sort(key=lambda x: x.creation)

	messages = []
	from markdownify import markdownify

	for h in histories:
		content_blocks = []
		if h.markdown:
			content_blocks.append({"type": "text", "text": markdownify(h.markdown)})

		if h.screenshot:
			try:
				file_doc = frappe.get_doc("File", {"file_url": h.screenshot})
				content_blocks.append({"type": "image_url", "image_url": {"url": file_doc.presigned_url}})
			except frappe.DoesNotExistError:
				pass

		if content_blocks:
			messages.append({"role": "user", "content": content_blocks})

	return messages
