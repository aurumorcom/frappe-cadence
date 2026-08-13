from typing import Optional
import frappe
from frappe.model.document import Document
from frappe_cadence.integrations.listmonk import (
	ensure_listmonk_authorized,
	ensure_user_bio_provisioned,
	modify_contact_sequences,
	update_contact,
)


class MultiChannelCadence(Document):
	def before_insert(self) -> None:
		if not self.status:
			self.status = "Draft"

	def on_update(self) -> None:
		if self.status == "Draft" and not self.playbook_execution:
			cadence = frappe.get_doc("Cadence", self.cadence_name) if frappe.db.exists("Cadence", self.cadence_name) else None
			playbook_name = cadence.reference_playbook if cadence else None

			if playbook_name and frappe.db.exists("Playbook", playbook_name):
				try:
					pe = frappe.get_doc({
						"doctype": "Playbook Execution",
						"playbook": playbook_name,
						"multi_channel_cadence": self.name,
						"status": "Queued",
					}).insert(ignore_permissions=True)
					self.db_set("playbook_execution", pe.name)
				except Exception as exc:
					frappe.logger("cadence").error(f"Failed to create Playbook Execution for MCC {self.name}: {exc}")

	def on_trash(self) -> None:
		if self.listmonk_contact_id and self.listmonk_sequence_id:
			frappe.enqueue(
				"frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.remove_contact_from_sequence",
				queue="high",
				mcc_name=self.name,
				listmonk_contact_id=self.listmonk_contact_id,
				listmonk_sequence_id=self.listmonk_sequence_id,
			)


def on_update(doc, method=None) -> None:
	if hasattr(doc, "on_update"):
		doc.on_update()


def on_trash(doc, method=None) -> None:
	if hasattr(doc, "on_trash"):
		doc.on_trash()


def add_contact_to_sequence(mcc_name: str) -> None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("Multi Channel Cadence", mcc_name):
		return

	mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
	if not frappe.db.exists("CRM Lead", mcc.recipient):
		return

	lead = frappe.get_doc("CRM Lead", mcc.recipient)
	if not frappe.db.exists("Cadence", mcc.cadence_name):
		return

	cadence = frappe.get_doc("Cadence", mcc.cadence_name)
	listmonk_sequence_id = cadence.listmonk_id
	if not listmonk_sequence_id:
		from frappe_cadence.cadence.doctype.cadence.cadence import upsert_sequence
		upsert_sequence(cadence.name)
		cadence.reload()
		listmonk_sequence_id = cadence.listmonk_id

	sender_user = mcc.sender or mcc.owner or frappe.session.user
	bio_content = ensure_user_bio_provisioned(sender_user, mcc.cadence_name)

	user_doc = frappe.get_doc("User", sender_user) if frappe.db.exists("User", sender_user) else None
	user_dict = {
		"id": user_doc.name if user_doc else sender_user,
		"name": user_doc.full_name if user_doc else sender_user,
		"email_id": user_doc.email if user_doc else "",
		"bio": bio_content,
	}

	ctx_text = frappe.db.get_value("Context", {"reference_doc": mcc.name}, "content")
	if not ctx_text:
		ctx_text = frappe.db.get_value("Context", {"reference_doc": mcc.recipient}, "content") or ""

	context_dict = {"content": ctx_text}

	listmonk_contact_id = lead.listmonk_id
	if not listmonk_contact_id:
		from frappe_cadence.cadence.doctype.crm_lead.crm_lead import upsert_contact
		upsert_contact(lead.name)
		lead.reload()
		listmonk_contact_id = lead.listmonk_id

	if not listmonk_contact_id:
		frappe.logger("cadence").error(f"Failed to resolve listmonk_contact_id for lead {lead.name}")
		return

	payload = {
		"email": lead.get("email_id") or lead.get("email") or "",
		"name": lead.get("lead_name") or lead.get("first_name") or lead.name,
		"status": "enabled",
		"sequences": [int(listmonk_sequence_id)],
		"attribs": {
			"user": user_dict,
			"context": context_dict,
			"lead_id": lead.name,
			"company_name": lead.get("company_name") or "",
			"lead_status": lead.get("status") or "",
		},
	}

	update_contact(int(listmonk_contact_id), payload)

	mcc.db_set("listmonk_contact_id", int(listmonk_contact_id))
	mcc.db_set("listmonk_sequence_id", int(listmonk_sequence_id))
	mcc.db_set("status", "Scheduled")


def remove_contact_from_sequence(
	mcc_name: str,
	listmonk_contact_id: Optional[int] = None,
	listmonk_sequence_id: Optional[int] = None,
) -> None:
	ensure_listmonk_authorized()

	if not listmonk_contact_id or not listmonk_sequence_id:
		if frappe.db.exists("Multi Channel Cadence", mcc_name):
			mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
			listmonk_contact_id = listmonk_contact_id or mcc.listmonk_contact_id
			listmonk_sequence_id = listmonk_sequence_id or mcc.listmonk_sequence_id

	if listmonk_contact_id and listmonk_sequence_id:
		modify_contact_sequences(
			action="remove",
			contact_ids=[int(listmonk_contact_id)],
			sequence_ids=[int(listmonk_sequence_id)],
		)
