import frappe
import requests
from typing import Dict, Any, Union
from frappe_cadence._template import (
    WebhookResponse,
    get_raw_payload,
    extract_output_text,
    extract_agent_name,
    get_annotation_system_fields,
    is_annotation_pending,
    get_annotation_response,
    get_annotation_schema,
    build_annotation_messages,
    update_annotation_output
)

def get_sift_settings() -> tuple:
    settings = frappe.get_single("Sift Settings")
    base_url = settings.sift_base_url or frappe.conf.get("sift_base_url")
    api_key = settings.get_password('sift_api_key') or frappe.conf.get("sift_api_key")
    
    if not base_url or not api_key:
        frappe.throw("Sift Base URL and API Key must be configured in Sift Settings or site config.")
        
    return base_url.rstrip('/'), api_key

@frappe.whitelist()
def optimize(template_doctype: str, template_name: str) -> None:
    template = frappe.get_doc(template_doctype, template_name)
    
    if not template.model:
        frappe.throw(f"No LLM Model linked to {template_doctype} {template_name}.")
    
    model_doc = frappe.get_doc("Model", template.model)
    
    if model_doc.provider and "/" not in model_doc.model_name:
        model_str = f"{model_doc.provider.lower()}/{model_doc.model_name}"
    else:
        model_str = model_doc.model_name
    
    template.status = "Optimizing"
    template.flags.ignore_links = True
    template.save(ignore_permissions=True)
    
    base_url, api_key = get_sift_settings()
    
    annotations = template.get("annotations", [])
    train_data = []
    
    for ann in annotations:
        if not is_annotation_pending(ann):
            messages = build_annotation_messages(ann)
            
            train_data.append({
                "trace_id": ann.name,
                "score": ann.score if getattr(ann, "score", None) is not None else 1.0,
                "messages": messages,
                "response": get_annotation_response(ann),
                "feedback": getattr(ann, "feedback", "")
            })
            
    code_fieldname = f"{template_doctype.lower().replace(' ', '_')}_code"
    agent_name = template.get(code_fieldname)

    payload = {
        "agent_name": agent_name,
        "webhook": {
            "url": f"{frappe.utils.get_url()}/api/method/frappe_cadence.integrations.sift.optimize_callback",
            "events": ["completed", "failed"],
            "metadata": {
                "doctype": template_doctype,
                "name": template_name
            }
        },
        "litellm_params": {
            "model": model_str
        },
        "dspy_params": {
            "state": {
                "predict": {
                    "train": train_data
                }
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        endpoint = f"{base_url}/agents"
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        template.status = "Enabled"
        template.enabled = 1
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        frappe.throw(f"Failed to initiate optimization with Sift: {str(e)}")

@frappe.whitelist(allow_guest=True)
def optimize_callback(**kwargs) -> Dict[str, Any]:
    raw_payload = get_raw_payload(kwargs)
    payload = WebhookResponse(raw_payload)

    if payload.is_started:
        return {"status": "ignored"}
        
    template_doctype = payload.metadata.get("doctype")
    template_name = payload.metadata.get("name")
    template = frappe.get_doc(template_doctype, template_name) if template_doctype and template_name and frappe.db.exists(template_doctype, template_name) else None

    if payload.is_failed:
        error = payload.error or "Unknown error"
        frappe.log_error("Sift Optimize Failed", error)
        if template:
            template.status = "Enabled" if template.enabled else "Disabled"
            template.flags.ignore_links = True
            template.save(ignore_permissions=True)
            return {"status": "failed", "error": error, "template": template.as_dict()}
        return {"status": "failed", "error": error}
        
    if payload.is_completed:
        agent_name = extract_agent_name(payload.data)
            
        if not template_doctype or not template_name or not agent_name or not template:
            frappe.throw("Invalid webhook payload")
            
        template.sift_id = agent_name
        template.status = "Disabled"
        template.enabled = 0
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        
        return template.as_dict()
        
    return {"status": "ignored"}

@frappe.whitelist()
def predict(template_doctype: str, template_name: str) -> None:
    template = frappe.get_doc(template_doctype, template_name)
    
    if not template.sift_id:
        frappe.throw("Template must be optimized first (missing sift_id)")
        
    template.status = "Predicting"
    template.flags.ignore_links = True
    template.save(ignore_permissions=True)
    
    base_url, api_key = get_sift_settings()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    annotations = template.get("annotations", [])
    webhook_url = f"{frappe.utils.get_url()}/api/method/frappe_cadence.integrations.sift.predict_callback"
    
    has_pending = False
    
    from markdownify import markdownify

    tpl_subject = getattr(template, "subject", "") or ""
    tpl_response = template.get("response_html") if template.get("use_html") else (template.get("response") or template.get("message") or "")
    if not isinstance(tpl_response, str):
        tpl_response = str(tpl_response) if tpl_response else ""

    tpl_response_md = markdownify(tpl_response) if tpl_response else ""

    for ann in annotations:
        if is_annotation_pending(ann):
            has_pending = True
            messages = build_annotation_messages(ann)
            
            payload = {
                "model": template.sift_id,
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
                endpoint = f"{base_url}/responses"
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
            except Exception as e:
                frappe.log_error(f"Sift Predict Error for annotation {ann.name}: {str(e)}", "Sift API")
                
    if not has_pending:
        template.status = "Disabled"
        template.enabled = 0
        template.flags.ignore_links = True
        template.save(ignore_permissions=True)
        frappe.msgprint("No pending annotations without output found.")

@frappe.whitelist(allow_guest=True)
def predict_callback(**kwargs) -> Dict[str, Any]:
    raw_payload = get_raw_payload(kwargs)
    payload = WebhookResponse(raw_payload)

    if payload.is_started:
        return {"status": "ignored"}
        
    annotation_id = payload.metadata.get("name")
    annotation_doctype = payload.metadata.get("doctype")
    
    if payload.is_failed:
        error = payload.error or "Unknown error"
        frappe.log_error("Sift Predict Failed", error)
        return {"status": "failed", "error": error}
        
    if payload.is_completed:
        output_text = extract_output_text(payload.data)
        if not annotation_id or not output_text or not annotation_doctype:
            frappe.throw("Invalid webhook payload")
            
        update_annotation_output(annotation_doctype, annotation_id, output_text)
        ann = frappe.get_doc(annotation_doctype, annotation_id)
        return ann.as_dict()
        
    return {"status": "ignored"}
