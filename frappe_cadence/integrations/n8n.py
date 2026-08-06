import json
import requests
import frappe
from typing import Dict, Any, Optional
from frappe.utils import get_url
from frappe_cadence._template import (
    get_annotation_schema,
    get_annotation_response,
    is_annotation_pending,
    build_annotation_messages,
    update_annotation_output
)

def get_test_request_url(request_url: str) -> str:
    """
    Dynamically converts a production n8n webhook URL to its corresponding test URL.
    e.g. https://n8n.example.com/webhook/uuid -> https://n8n.example.com/webhook-test/uuid
    """
    if not request_url:
        return ""
    if "/webhook/" in request_url:
        return request_url.replace("/webhook/", "/webhook-test/", 1)
    return request_url

def _get_webhook_secret(template) -> Optional[str]:
    if hasattr(template, "get_password"):
        try:
            return template.get_password("webhook_secret", raise_exception=False)
        except Exception:
            return getattr(template, "webhook_secret", None)
    return getattr(template, "webhook_secret", None)

def trigger_execution(template, payload: dict, channel: str, cadence_name: str, schedule_name: str) -> bool:
    """
    Sends the AI agent generation payload to the production n8n webhook URL configured on the template.
    """
    request_url = template.get("request_url")
    if not request_url:
        frappe.log_error(
            title="n8n Integration Error",
            message=f"Request URL not configured on {template.doctype} {template.name}"
        )
        return False

    webhook_secret = _get_webhook_secret(template)

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"

    callback_url = get_url(f"/api/method/frappe_cadence.{channel.lower()}_template.callback")
    payload["background"] = True
    payload["webhook"] = {
        "url": callback_url,
        "events": ["completed", "failed"]
    }

    payload_json = json.dumps(payload, separators=(',', ':'))

    try:
        response = requests.post(request_url, headers=headers, data=payload_json, timeout=10)
        response.raise_for_status()
        frappe.cache().set_value(f"ai_req:{cadence_name}:{schedule_name}", 1, expires_in_sec=86400)
        return True
    except Exception as e:
        frappe.log_error(
            title="n8n Integration Error",
            message=f"Failed to send request to n8n ({request_url}): {str(e)}"
        )
        return False

def trigger_test_execution(template, payload: dict) -> bool:
    """
    Sends the AI agent generation payload to the n8n test webhook URL corresponding to the template's request_url.
    """
    request_url = template.get("request_url")
    if not request_url:
        frappe.log_error(
            title="n8n Integration Test Error",
            message=f"Request URL not configured on {template.doctype} {template.name}"
        )
        return False

    test_url = get_test_request_url(request_url)
    webhook_secret = _get_webhook_secret(template)

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"

    callback_url = get_url("/api/method/frappe_cadence.integrations.n8n.optimize_callback")
    payload["background"] = True
    payload["webhook"] = {
        "url": callback_url,
        "events": ["completed", "failed"],
        "metadata": {
            "doctype": template.doctype,
            "name": template.name
        }
    }

    payload_json = json.dumps(payload, separators=(',', ':'))

    try:
        response = requests.post(test_url, headers=headers, data=payload_json, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        frappe.log_error(
            title="n8n Test Webhook Endpoint Error",
            message=f"Failed to send test request to n8n test webhook ({test_url}): {str(e)}"
        )
        return False

@frappe.whitelist()
def optimize(template_doctype: str, template_name: str) -> Dict[str, Any]:
    template = frappe.get_doc(template_doctype, template_name)

    request_url = template.get("request_url")
    if not request_url:
        msg = f"Request URL not configured on {template_doctype} {template_name}."
        frappe.msgprint(msg, alert=True, indicator="orange")
        return {"status": "failed", "error": msg}

    schedules = frappe.get_all(
        "Cadence Multi Channel Schedule",
        filters={
            "reference_doctype": template_doctype,
            "reference_name": template_name
        },
        fields=["name", "parent"]
    )

    if not schedules:
        msg = f"No Cadence step found using template {template_name}."
        frappe.msgprint(msg, alert=True, indicator="orange")
        return {"status": "failed", "error": msg}

    cadence_names = list(set([s.parent for s in schedules if s.parent]))

    mcc_list = frappe.get_all(
        "Multi Channel Cadence",
        filters={
            "cadence_name": ["in", cadence_names],
            "status": ["!=", "Provisioning"]
        },
        fields=["name", "cadence_name", "cadence_for", "recipient", "sender", "owner", "status"],
        order_by="modified desc",
        limit=1
    )

    if not mcc_list:
        msg = f"No active Multi Channel Cadence (not in Provisioning status) found using template {template_name}."
        frappe.msgprint(msg, alert=True, indicator="orange")
        return {"status": "failed", "error": msg}

    mcc_doc = frappe.get_doc("Multi Channel Cadence", mcc_list[0].name)
    cadence_doc = frappe.get_doc("Cadence", mcc_doc.cadence_name)

    schedule_name = None
    for sched in cadence_doc.cadence_schedules:
        if sched.reference_doctype == template_doctype and sched.reference_name == template_name:
            schedule_name = sched.name
            break

    if not schedule_name:
        msg = f"Could not determine Cadence step for template {template_name}."
        frappe.msgprint(msg, alert=True, indicator="orange")
        return {"status": "failed", "error": msg}

    channel = template_doctype.replace(" Template", "")

    template.status = "Optimizing"
    template.flags.ignore_links = True
    template.save(ignore_permissions=True)

    try:
        reference_cadence_provider = None
        for row in (mcc_doc.get("provider") or []):
            if row.channel == channel:
                reference_cadence_provider = row.cadence_provider
                break

        draft_comm = frappe.get_all("Communication", filters={
            "reference_doctype": "Multi Channel Cadence",
            "reference_name": mcc_doc.name,
            "cadence_schedule": schedule_name,
            "status": "Open"
        })

        if draft_comm:
            comm_name = draft_comm[0].name
        else:
            comm = frappe.get_doc({
                "doctype": "Communication",
                "communication_medium": channel,
                "subject": f"Draft {channel} Message",
                "reference_doctype": "Multi Channel Cadence",
                "reference_name": mcc_doc.name,
                "cadence_schedule": schedule_name,
                "status": "Open",
                "reference_cadence_provider": reference_cadence_provider
            })
            comm.insert(ignore_permissions=True)
            comm_name = comm.name

        schema_properties = {
            "content": {
                "type": "string",
                "description": "The main body content of the message"
            }
        }
        required_fields = ["content"]

        if channel == "Email":
            schema_properties["subject"] = {
                "type": "string",
                "description": "The subject of the message"
            }
            required_fields.append("subject")

        tpl_subject = getattr(template, "subject", "") or ""
        if not isinstance(tpl_subject, str):
            tpl_subject = str(tpl_subject) if tpl_subject else ""

        tpl_response = template.get("response_html") if template.get("use_html") else (template.get("response") or template.get("message") or "")
        if not isinstance(tpl_response, str):
            tpl_response = str(tpl_response) if tpl_response else ""

        payload = {
            "subject": tpl_subject,
            "response": tpl_response,
            "metadata": {
                "name": comm_name
            },
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
            }
        }

        from markdownify import markdownify
        from frappe.utils import add_months, today
        from frappe_cadence.cadence.doctype.history.history import get_history
        from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio

        sender_user = mcc_doc.sender or mcc_doc.owner
        sender_bio_content = get_user_bio(sender_user, mcc_doc.cadence_name)
        sender = frappe.db.get_value("User", sender_user, ["full_name"], as_dict=True) or {}
        sender_name = sender.get("full_name") or ""
        sender_bio = markdownify(sender_bio_content) if sender_bio_content else ""

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

        if tpl_response:
            payload["input"].append({
                "role": "user",
                "content": f"Template Response:\n{tpl_response}"
            })

        three_months_ago = add_months(today(), -3)
        history_messages = get_history(mcc_doc.cadence_for, mcc_doc.recipient, since_date=three_months_ago)
        payload["input"].extend(history_messages)

        sift_id_val = getattr(template, "sift_id", None)
        payload["model"] = sift_id_val if isinstance(sift_id_val, str) and sift_id_val else "default-model"

        success = trigger_test_execution(template, payload)
        if success:
            frappe.msgprint("Test inference request sent to n8n test workflow successfully. Waiting for n8n test response.", alert=True, indicator="green")
            return {"status": "success"}
        else:
            template.status = "Enabled" if template.enabled else "Disabled"
            template.flags.ignore_links = True
            template.save(ignore_permissions=True)
            frappe.msgprint("Failed to send test request: n8n test webhook is not active. Please click 'Test workflow' in n8n and try again.", alert=True, indicator="orange")
            return {"status": "failed", "error": "n8n test webhook endpoint is not listening."}

    except Exception as e:
        template.status = "Enabled" if template.enabled else "Disabled"
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        frappe.log_error(title="n8n Optimize Error", message=str(e))
        frappe.msgprint(f"Failed to optimize template: {str(e)}", alert=True, indicator="orange")
        return {"status": "failed", "error": str(e)}

@frappe.whitelist(allow_guest=True)
def optimize_callback(**kwargs) -> Dict[str, str]:
    event_type = kwargs.get("type")
    if event_type and event_type.endswith(".started"):
        return {"status": "ignored"}

    metadata = kwargs.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}

    template_doctype = metadata.get("doctype")
    template_name = metadata.get("name")

    if event_type in ("failed", "agent.failed", "response.failed"):
        error = kwargs.get("error") or "Unknown error"
        frappe.log_error("n8n Optimize Callback Failed", error)
        if template_doctype and template_name:
            template = frappe.get_doc(template_doctype, template_name)
            template.status = "Enabled" if template.enabled else "Disabled"
            template.flags.ignore_links = True
            template.save(ignore_permissions=True)
        return {"status": "failed"}

    if event_type in ("completed", "agent.completed", "response.completed"):
        if template_doctype and template_name:
            template = frappe.get_doc(template_doctype, template_name)
            template.status = "Enabled" if template.enabled else "Disabled"
            template.flags.ignore_links = True
            template.save(ignore_permissions=True)
            return {"status": "success"}

    return {"status": "ignored"}

@frappe.whitelist()
def predict(template_doctype: str, template_name: str) -> Dict[str, Any]:
    template = frappe.get_doc(template_doctype, template_name)

    request_url = template.get("request_url")
    if not request_url:
        frappe.throw(f"Request URL not configured on {template_doctype} {template_name}.")

    template.status = "Predicting"
    template.flags.ignore_links = True
    template.save(ignore_permissions=True)

    webhook_secret = _get_webhook_secret(template)

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"

    annotations = template.get("annotations", [])
    webhook_url = get_url("/api/method/frappe_cadence.integrations.n8n.predict_callback")

    has_pending = False

    tpl_subject = getattr(template, "subject", "") or ""
    tpl_response = template.get("response_html") if template.get("use_html") else (template.get("response") or template.get("message") or "")

    for ann in annotations:
        if is_annotation_pending(ann):
            has_pending = True
            messages = build_annotation_messages(ann)

            payload = {
                "subject": tpl_subject,
                "response": tpl_response,
                "model": getattr(template, "sift_id", None) or "n8n-workflow",
                "background": True,
                "webhook": {
                    "url": webhook_url,
                    "events": ["completed", "failed"],
                    "metadata": {
                        "name": ann.name,
                        "doctype": ann.doctype
                    }
                },
                "input": messages
            }

            response_schema = get_annotation_response(ann)
            if isinstance(response_schema, dict):
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": get_annotation_schema(ann.doctype)
                }

            try:
                response = requests.post(request_url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
            except Exception as e:
                frappe.log_error(f"n8n Predict Error for annotation {ann.name}: {str(e)}", "n8n API")

    if not has_pending:
        template.status = "Disabled"
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        frappe.msgprint("No pending annotations without output found.")

    return {"status": "success"}

@frappe.whitelist(allow_guest=True)
def predict_callback(**kwargs) -> Dict[str, str]:
    event_type = kwargs.get("type")
    if event_type and event_type.endswith(".started"):
        return {"status": "ignored"}

    metadata = kwargs.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}

    annotation_id = metadata.get("name")
    annotation_doctype = metadata.get("doctype")

    data = kwargs.get("data", [])
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = []

    if event_type in ("failed", "response.failed"):
        error = kwargs.get("error") or "Unknown error"
        frappe.log_error("n8n Predict Failed", error)
        return {"status": "failed"}

    if event_type in ("completed", "response.completed"):
        output_text = ""
        if isinstance(data, list) and len(data) > 0:
            content_list = data[0].get("content", [])
            if content_list and isinstance(content_list, list) and len(content_list) > 0:
                output_text = content_list[0].get("text", "")
        elif isinstance(data, dict):
            content_list = data.get("content", [])
            if content_list and isinstance(content_list, list) and len(content_list) > 0:
                output_text = content_list[0].get("text", "")

        if not annotation_id or not output_text or not annotation_doctype:
            frappe.throw("Invalid webhook payload")

        update_annotation_output(annotation_doctype, annotation_id, output_text)
        return {"status": "success"}

    return {"status": "ignored"}
