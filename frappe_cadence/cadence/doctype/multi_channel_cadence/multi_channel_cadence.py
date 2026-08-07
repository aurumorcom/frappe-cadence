import frappe
import requests
import json
import urllib.parse
import hmac
import hashlib
import base64
from frappe.utils import add_months, today, get_url
from frappe.model.document import Document
from frappe_controller.utils.background_jobs import enqueue
from frappe_controller.utils.controller import wait_for_event, emit_event

class MultiChannelCadence(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from frappe_cadence.cadence.doctype.mcc_cadence_provider.mcc_cadence_provider import MCCCadenceProvider

        cadence_for: DF.Literal["", "CRM Lead", "Contact", "Email Group"]
        cadence_name: DF.Link
        end_date: DF.Date | None
        provider: DF.Table[MCCCadenceProvider]
        recipient: DF.DynamicLink
        sender: DF.Link | None
        start_date: DF.Date
        status: DF.Literal["Provisioning", "Draft", "Scheduled", "In Progress", "Completed", "Unsubscribed", "Error"]
    # end: auto-generated types

    def before_insert(self):
        if not self.status:
            self.status = "Provisioning"
        from frappe_cadence.cadence.doctype.cadence_provider.cadence_provider import resolve_providers_for_mcc
        seed = self.name if self.name else f"{self.cadence_name}-{self.recipient}"
        resolved = resolve_providers_for_mcc(seed)
        
        for channel, provider in resolved.items():
            self.append("provider", {
                "channel": channel,
                "cadence_provider": provider
            })

    def on_update(self):
        cadence = frappe.get_doc("Cadence", self.cadence_name)
        
        # Check if providers changed
        old_doc = self.get_doc_before_save()
        if old_doc:
            old_providers = {row.channel: row.cadence_provider for row in (old_doc.get("provider") or []) if row.cadence_provider}
            current_providers = {row.channel: row.cadence_provider for row in (self.get("provider") or []) if row.cadence_provider}
            
            new_providers = {}
            for channel, provider in current_providers.items():
                if old_providers.get(channel) != provider:
                    new_providers[channel] = provider
            
            if new_providers:
                for channel, provider in new_providers.items():
                    comms = frappe.get_all("Communication", filters={
                        "reference_doctype": "Multi Channel Cadence",
                        "reference_name": self.name,
                        "communication_medium": channel,
                        "reference_cadence_provider": ["is", "not set"]
                    })
                    for comm_info in comms:
                        comm = frappe.get_doc("Communication", comm_info.name)
                        comm.reference_cadence_provider = provider
                        comm.save(ignore_permissions=True)
        
        if self.has_value_changed("status") or self.status == "Draft":
            if self.status in ["Draft", "Scheduled", "In Progress"]:
                _enqueue_schedule_jobs(self, cadence)
                
            if self.status in ["Scheduled", "In Progress"]:
                emit_event("mcc_scheduled", {"doctype": self.doctype, "name": self.name})
                emit_event("mcc_in_progress", {"doctype": self.doctype, "name": self.name})




def _enqueue_schedule_jobs(mcc_doc, cadence_doc):
    """
    Idempotently enqueues process_schedule jobs for all schedules in a cadence.
    """
    existing_jobs = False
    jobs = frappe.get_all("FS Job", filters={"status": ["in", ["queued", "started", "deferred"]]}, fields=["name", "arguments"])
    for job in jobs:
        try:
            kwargs = json.loads(job.arguments)
            if kwargs.get("cadence_name") == mcc_doc.name:
                existing_jobs = True
                break
        except Exception:
            pass

    if not existing_jobs:
        for idx, schedule in enumerate(cadence_doc.cadence_schedules):
            comm = frappe.get_all("Communication", filters={
                "reference_doctype": "Multi Channel Cadence",
                "reference_name": mcc_doc.name,
                "cadence_schedule": schedule.name
            }, fields=["name", "delivery_status"])

            if comm:
                if comm[0].delivery_status == "Sent":
                    continue
                elif mcc_doc.status in ["Scheduled", "In Progress"]:
                    frappe.delete_doc("Communication", comm[0].name)

            previous_schedule_name = cadence_doc.cadence_schedules[idx - 1].name if idx > 0 else None

            enqueue(
                "frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.process_schedule",
                queue="medium",
                cadence_name=mcc_doc.name,
                schedule_name=schedule.name,
                previous_schedule_name=previous_schedule_name
            )

def on_update(doc, method):
 """Update the hidden 'cadences' child table on CRM Lead for filtering purposes"""
 if getattr(doc, "cadence_for", getattr(doc, "email_cadence_for", None)) == "CRM Lead":
  if not frappe.db.exists("CRM Lead", doc.recipient):
   return

  lead = frappe.get_doc("CRM Lead", doc.recipient)
  
  if not hasattr(lead, "cadences"):
   return

  # Check if already exists in child table
  if not any(row.cadence_name == doc.cadence_name for row in lead.cadences):
   lead.append("cadences", {
    "cadence_name": doc.cadence_name
   })
   lead.save(ignore_permissions=True)

def on_trash(doc, method):
 """Remove the reference from CRM Lead when an Email Cadence is deleted"""
 if getattr(doc, "cadence_for", getattr(doc, "email_cadence_for", None)) == "CRM Lead":
  if not frappe.db.exists("CRM Lead", doc.recipient):
   return

  lead = frappe.get_doc("CRM Lead", doc.recipient)
  if not hasattr(lead, "cadences"):
   return

  # Since we don't have the email_cadence link anymore,
  # we should check if any OTHER email cadences for this lead and cadence still exist
  other_exists = frappe.db.exists("Multi Channel Cadence", {
   "cadence_name": doc.cadence_name,
   "recipient": doc.recipient,
   "name": ("!=", doc.name)
  })

  if not other_exists:
   lead.set("cadences", [
    row for row in lead.cadences if row.cadence_name != doc.cadence_name
   ])
   lead.save(ignore_permissions=True)

def process_schedule(cadence_name, schedule_name, previous_schedule_name=None):
    """
    Processes a single step in a multi-channel cadence.
    Must be idempotent as it executes from line 1 when resumed.
    """
    # 1. MCC State Check
    mcc = frappe.get_doc("Multi Channel Cadence", cadence_name)
    if mcc.status in ["Completed", "Error", "Unsubscribed"]:
        return

    if mcc.status == "Provisioning":
        wait_for_event(
            event_key=f"doc:Multi Channel Cadence:{cadence_name}:on_update",
            condition="argument.get('status') in ['Draft', 'Scheduled', 'In Progress']"
        )
        return

    # 2. Wait for Previous Step
    if previous_schedule_name:
        prev_comm = frappe.get_all("Communication", filters={
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": cadence_name,
            "cadence_schedule": previous_schedule_name,
            "delivery_status": ["in", ["Scheduled", "Sent"]]
        })
        if not prev_comm:
            wait_for_event(
                "cadence_step_completed",
                condition=f"argument.get('cadence_name') == '{cadence_name}' and argument.get('schedule_name') == '{previous_schedule_name}'"
            )
            return

    # 3. Idempotency Check
    curr_comm = frappe.get_all("Communication", filters={
        "reference_doctype": "Multi Channel Cadence",
        "reference_name": cadence_name,
        "cadence_schedule": schedule_name,
        "delivery_status": ["in", ["Scheduled", "Sent"]]
    })
    if curr_comm:
        emit_event("cadence_step_completed", {"cadence_name": cadence_name, "schedule_name": schedule_name})
        return

    # 4. Template State Check & Process Template
    schedule = frappe.get_doc("Cadence Multi Channel Schedule", schedule_name)
    
    template_doctype = f"{schedule.reference_doctype}"
    template_name = schedule.reference_name
    template = frappe.get_doc(template_doctype, template_name)
    
    if template.status != "Enabled":
        event_key = f"doc:{template_doctype}:on_update"
        wait_for_event(
            event_key=event_key,
            condition=f"argument.get('name') == '{template_name}' and (argument.get('status') == 'Enabled' or argument.get('enabled') == 1)"
        )
        return

    channel = template_doctype.replace(" Template", "")

    reference_cadence_provider = None
    for row in (mcc.get("provider") or []):
        if row.channel == channel:
            reference_cadence_provider = row.cadence_provider
            break

    template_provider = getattr(template, "provider", "Frappe") or "Frappe"
    if str(template_provider) not in ["DSPy", "n8n"]:
        template_provider = "Frappe"

    if template_provider == "Frappe" and template.status == "Enabled":
        comm = frappe.get_doc({
            "doctype": "Communication",
            "communication_medium": channel,
            "subject": getattr(template, "subject", template.get("title", f"{channel} Message")),
            "content": template.get("message") or template.get("response"),
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": cadence_name,
            "cadence_schedule": schedule_name,
            "status": "Open",
            "delivery_status": "Scheduled",
            "reference_cadence_provider": reference_cadence_provider
        })
        comm.insert(ignore_permissions=True)
        emit_event("cadence_step_completed", {"cadence_name": cadence_name, "schedule_name": schedule_name})
        return

    if template_provider in ["DSPy", "n8n"] and template.status == "Enabled":
        draft_comm = frappe.get_all("Communication", filters={
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": cadence_name,
            "cadence_schedule": schedule_name,
            "status": "Open"
        })
        
        if not draft_comm:
            comm = frappe.get_doc({
                "doctype": "Communication",
                "communication_medium": channel,
                "subject": f"Draft {channel} Message",
                "reference_doctype": "Multi Channel Cadence",
                "reference_name": cadence_name,
                "cadence_schedule": schedule_name,
                "status": "Open",
                "reference_cadence_provider": reference_cadence_provider
            })
            comm.insert(ignore_permissions=True)
            comm_name = comm.name
            
            # Construct AI Agent payload
            cadence = frappe.get_doc("Multi Channel Cadence", cadence_name)
            lead = frappe.get_doc(cadence.cadence_for, cadence.recipient)
            
            from markdownify import markdownify

            if channel == "Email":
                schema_properties = {
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email"
                    },
                    "content": {
                        "type": "string",
                        "description": "The main body content of the email"
                    }
                }
                required_fields = ["subject", "content"]
            else:
                schema_properties = {
                    "content": {
                        "type": "string",
                        "description": "The main body content of the message"
                    }
                }
                required_fields = ["content"]
                
            tpl_subject = getattr(template, "subject", "") or ""
            if not isinstance(tpl_subject, str):
                tpl_subject = str(tpl_subject) if tpl_subject else ""

            tpl_response = template.get("response_html") if template.get("use_html") else (template.get("response") or template.get("message") or "")
            if not isinstance(tpl_response, str):
                tpl_response = str(tpl_response) if tpl_response else ""
            
            tpl_response_md = markdownify(tpl_response) if tpl_response else ""

            payload = {
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "communication_generation",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": schema_properties,
                            "required": required_fields,
                            "additionalProperties": False
                        }
                    }
                },
            }
            
            from frappe_cadence.cadence.doctype.history.history import get_history
            from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio
            
            sender_user = mcc.sender or mcc.owner
            sender_bio_content = get_user_bio(sender_user, mcc.cadence_name)
            if not sender_bio_content:
                wait_for_event(
                    event_key="doc:User Bio:on_update",
                    condition=f"argument.get('reference_user') == '{sender_user}' and argument.get('enabled') == 1 and (argument.get('reference_cadence') == '{mcc.cadence_name}' or argument.get('is_default') == 1)"
                )
                return
                
            sender = frappe.db.get_value("User", sender_user, ["full_name"], as_dict=True) or {}
            sender_name = sender.get("full_name") or ""
            sender_bio = markdownify(sender_bio_content)
            
            payload["input"] = []
            if sender_name or sender_bio:
                payload["input"].append({
                    "role": "user",
                    "content": f"Sender Name: {sender_name}\nSender Bio:\n{sender_bio}"
                })

            if tpl_subject:
                payload["input"].append({
                    "role": "user",
                    "content": f"Template Subject: {tpl_subject}"
                })

            if tpl_response_md:
                payload["input"].append({
                    "role": "user",
                    "content": f"Template Response:\n{tpl_response_md}"
                })
            
            # Fetch and format History records
            three_months_ago = add_months(today(), -3)
            history_messages = get_history(cadence.cadence_for, cadence.recipient, since_date=three_months_ago)
            payload["input"].extend(history_messages)

            if template_provider == "n8n":
                raw_model = getattr(template, "model", None)
            elif template_provider == "DSPy":
                raw_model = getattr(template, "sift_id", None)
            else:
                raw_model = None

            if isinstance(raw_model, str):
                payload["model"] = raw_model
            elif raw_model and isinstance(raw_model, (int, float)):
                payload["model"] = str(raw_model)
            else:
                payload["model"] = None
            
            cache_val = frappe.cache().get_value(f"ai_req:{cadence_name}:{schedule_name}")
            
            if not cache_val:
                webhook_url = get_url(f"/api/method/frappe_cadence.{channel.lower()}_template.callback")
                payload["background"] = True
                payload["webhook"] = {
                    "url": webhook_url,
                    "events": ["completed", "failed"],
                    "metadata": {
                        "name": comm_name
                    }
                }

                if template_provider == "n8n":
                    from frappe_cadence.integrations.n8n import trigger_execution
                    trigger_execution(template, payload, channel, cadence_name, schedule_name)
                else:
                    sift_settings = frappe.get_single("Sift Settings")
                    sift_base_url = sift_settings.sift_base_url
                    sift_api_key = sift_settings.get_password("sift_api_key")
                    
                    if sift_base_url:
                        headers = {"Content-Type": "application/json"}
                        if sift_api_key:
                            headers["Authorization"] = f"Bearer {sift_api_key}"

                        payload_json = json.dumps(payload, separators=(',', ':'))
                        
                        try:
                            requests.post(f"{sift_base_url}/responses", headers=headers, data=payload_json, timeout=10)
                            frappe.cache().set_value(f"ai_req:{cadence_name}:{schedule_name}", 1, expires_in_sec=86400)
                        except Exception as e:
                            frappe.log_error(title="Agent Error", message=f"Failed to send task to Agent: {str(e)}")
                            return
                    else:
                        frappe.log_error(title="Sift Configuration Error", message="Sift Base URL not configured.")
                        return
        else:
            comm_name = draft_comm[0].name
            
        wait_for_event("callback", condition=f"argument.get('communication_id') == '{comm_name}'")
