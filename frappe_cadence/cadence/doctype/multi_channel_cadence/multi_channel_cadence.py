from typing import Optional

import frappe
from frappe.model.document import Document

from frappe_cadence.jobs.multi_channel_cadence import (
	add_subscriber_to_campaign,
	remove_subscriber_from_campaign,
)


class MultiChannelCadence(Document):
	def before_insert(self) -> None:
		if not self.status:
			self.status = "Draft"

	def on_update(self) -> None:
		if self.status == "Draft" and not self.playbook_execution:
			cadence = (
				frappe.get_doc("Cadence", self.cadence_name)
				if frappe.db.exists("Cadence", self.cadence_name)
				else None
			)
			playbook_name = getattr(cadence, "reference_playbook", None) if cadence else None

			if playbook_name and frappe.db.exists("Playbook", playbook_name):
				try:
					pe = frappe.get_doc(
						{
							"doctype": "Playbook Execution",
							"playbook": playbook_name,
							"multi_channel_cadence": self.name,
							"status": "Queued",
						}
					).insert(ignore_permissions=True)
					self.db_set("playbook_execution", pe.name)
				except Exception as exc:
					frappe.logger("cadence").error(
						f"Failed to create Playbook Execution for MCC {self.name}: {exc}"
					)

	def on_trash(self) -> None:
		subscriber_id = getattr(self, "listmonk_subscriber_id", None)
		list_id = getattr(self, "listmonk_list_id", None)
		campaign_id = getattr(self, "listmonk_campaign_id", None)
		if subscriber_id and (list_id or campaign_id):
			frappe.enqueue(
				"frappe_cadence.jobs.multi_channel_cadence.remove_subscriber_from_campaign",
				queue="high",
				mcc_name=self.name,
				listmonk_subscriber_id=subscriber_id,
				listmonk_campaign_id=campaign_id,
			)


def on_update(doc, method: str | None = None) -> None:
	if hasattr(doc, "on_update"):
		doc.on_update()


def on_trash(doc, method: str | None = None) -> None:
	if hasattr(doc, "on_trash"):
		doc.on_trash()
