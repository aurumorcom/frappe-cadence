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

def send_request(template, payload: dict, channel: str, cadence_name: str, schedule_name: str) -> bool:
    """
    Sends the AI agent generation payload to the n8n webhook URL configured on the template.
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

@frappe.whitelist()
def optimize(template_doctype: str, template_name: str) -> Dict[str, Any]:
    template = frappe.get_doc(template_doctype, template_name)

    request_url = template.get("request_url")
    if not request_url:
        frappe.throw(f"Request URL not configured on {template_doctype} {template_name}.")

    template.status = "Optimizing"
    template.flags.ignore_links = True
    template.save(ignore_permissions=True)

    test_url = get_test_request_url(request_url)

    webhook_secret = _get_webhook_secret(template)

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"

    tpl_subject = getattr(template, "subject", "") or ""
    tpl_response = template.get("response_html") if template.get("use_html") else (template.get("response") or template.get("message") or "")

    payload = {
        "subject": tpl_subject,
        "response": tpl_response,
        "metadata": {
            "doctype": template_doctype,
            "name": template_name,
            "event_type": "optimize"
        },
        "background": True,
        "webhook": {
            "url": get_url("/api/method/frappe_cadence.integrations.n8n.optimize_callback"),
            "events": ["completed", "failed"]
        },
        "response_format": {
            "type": "json_schema",
            "json_schema": get_annotation_schema(template_doctype)
        },
        "input": [],
        "model": getattr(template, "sift_id", None) or "n8n-workflow"
    }

    payload_json = json.dumps(payload, separators=(',', ':'))

    try:
        response = requests.post(test_url, headers=headers, data=payload_json, timeout=10)
        response.raise_for_status()
        frappe.msgprint("Test event sent to n8n test workflow successfully.", alert=True, indicator="green")
        return {"status": "success"}
    except Exception as e:
        template.status = "Enabled"
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        frappe.log_error(
            title="n8n Optimize Warning",
            message=f"n8n test workflow not listening at {test_url}: {str(e)}"
        )
        frappe.msgprint(
            f"Failed to send test event. The n8n test workflow may not be listening: {str(e)}",
            alert=True,
            indicator="orange"
        )
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
            template.status = "Enabled"
            template.flags.ignore_links = True
            template.save(ignore_permissions=True)
        return {"status": "failed"}

    if event_type in ("completed", "agent.completed", "response.completed"):
        if template_doctype and template_name:
            template = frappe.get_doc(template_doctype, template_name)
            template.status = "Disabled"
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
