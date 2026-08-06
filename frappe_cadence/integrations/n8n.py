import json
import requests
import frappe
from frappe.utils import get_url

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

    webhook_secret = None
    if hasattr(template, "get_password"):
        webhook_secret = template.get_password("webhook_secret")
    else:
        webhook_secret = getattr(template, "webhook_secret", None)

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"

    callback_url = get_url(f"/api/method/frappe_cadence.cadence.{channel.lower()}_template.callback")
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
