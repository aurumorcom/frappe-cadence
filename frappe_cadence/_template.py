import json
import frappe
from typing import Dict, Any, Union, Optional
from frappe_controller.utils.controller import emit_event

class WebhookResponse:
    """
    Standardized parser for WebhookResponse schema:
    - success: bool -> Primary decision flag for completed (True) vs failed (False)
    - type: str -> Used only to detect in-between statuses like "started"
    - id: str -> Job ID / UUID
    - webhookId: str -> Delivery UUID
    - data: Any -> Payload content
    - error: Optional[str] -> Error string
    - metadata: Optional[Dict[str, Any]] -> Context metadata
    """
    def __init__(self, raw_payload: dict):
        if isinstance(raw_payload, dict):
            # Unwrap top-level "body" if present (dict or JSON string)
            if "body" in raw_payload:
                body_val = raw_payload["body"]
                if isinstance(body_val, dict) and ("metadata" in body_val or "data" in body_val or "success" in body_val or "error" in body_val):
                    raw_payload = body_val
                elif isinstance(body_val, str) and body_val.strip().startswith("{"):
                    try:
                        parsed_body = json.loads(body_val)
                        if isinstance(parsed_body, dict) and ("metadata" in parsed_body or "data" in parsed_body or "success" in parsed_body or "error" in parsed_body):
                            raw_payload = parsed_body
                    except Exception:
                        pass
        else:
            raw_payload = {}

        self.success: bool = bool(raw_payload.get("success", True))
        self.type: str = str(raw_payload.get("type") or "").strip().lower()
        self.id: str = str(raw_payload.get("id") or "").strip()
        self.webhook_id: str = str(raw_payload.get("webhookId") or raw_payload.get("webhook_id") or "").strip()
        self.error: Optional[str] = raw_payload.get("error")

        # Normalize metadata (dict or stringified JSON)
        raw_meta = raw_payload.get("metadata") or {}
        if isinstance(raw_meta, str):
            try:
                raw_meta = json.loads(raw_meta)
            except Exception:
                raw_meta = {}
        self.metadata: Dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}

        # Fall back if name/communication_id is supplied directly in payload root
        if "name" not in self.metadata:
            fallback_name = raw_payload.get("name") or raw_payload.get("communication_id")
            if fallback_name:
                self.metadata["name"] = str(fallback_name)

        # Normalize data (list, dict, or stringified JSON)
        raw_data = raw_payload.get("data")
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except Exception:
                pass
        self.data: Any = raw_data

    @property
    def is_started(self) -> bool:
        """Type is only inspected to filter out in-between 'started' events."""
        action = self.type.split(".")[-1] if "." in self.type else self.type
        return action in ("started", "start")

    @property
    def is_failed(self) -> bool:
        if self.is_started:
            return False
        return not self.success or bool(self.error)

    @property
    def is_completed(self) -> bool:
        if self.is_started:
            return False
        return self.success and not bool(self.error)


def get_raw_payload(kwargs: Optional[dict] = None) -> dict:
    if kwargs and isinstance(kwargs, dict):
        return kwargs
    if getattr(frappe, "request", None):
        req = frappe.request
        if hasattr(req, "get_json") and callable(req.get_json):
            try:
                json_payload = req.get_json(silent=True)
                if json_payload and isinstance(json_payload, dict):
                    return json_payload
            except Exception:
                pass
        elif hasattr(req, "json") and isinstance(getattr(req, "json", None), dict):
            return req.json
    return getattr(frappe, "form_dict", {}) or {}


def extract_output_text(data: Any) -> Union[str, Dict[str, Any]]:
    """
    Extracts output text or dictionary from data across array, object, or string payloads.
    Recursively handles stringified JSON payloads.
    """
    if isinstance(data, str):
        s_data = data.strip()
        if s_data.startswith("{") or s_data.startswith("["):
            try:
                data = json.loads(s_data)
            except Exception:
                return data
        else:
            return data

    extracted = ""
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict):
            content = first.get("content", [])
            if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                extracted = content[0].get("text", "")
            else:
                extracted = first.get("text") or first.get("output") or ""
        elif isinstance(first, str):
            extracted = first
    elif isinstance(data, dict):
        content = data.get("content", [])
        if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
            extracted = content[0].get("text", "")
        else:
            extracted = data.get("text") or data.get("output") or ""

    if isinstance(extracted, str):
        s_extracted = extracted.strip()
        if s_extracted.startswith("{") or s_extracted.startswith("["):
            try:
                parsed = json.loads(s_extracted)
                if isinstance(parsed, dict):
                    return parsed
                elif isinstance(parsed, list):
                    return extract_output_text(parsed)
            except Exception:
                pass

    return extracted


def extract_agent_name(data: Any) -> Optional[str]:
    """
    Extracts agent_name / sift_id from data across array, object, or string payloads.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return None

    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict):
            return first.get("agent_name") or first.get("sift_id")
    elif isinstance(data, dict):
        return data.get("agent_name") or data.get("sift_id")

    return None


def get_annotation_system_fields() -> list:
    return ['name', 'owner', 'creation', 'modified', 'modified_by', 'parent', 'parentfield', 'parenttype', 'idx', 'reference_doctype', 'reference_name', 'sender', 'score', 'feedback', '_user_tags', '_comments', '_assign', '_liked_by']

def is_annotation_pending(ann) -> bool:
    meta = frappe.get_meta(ann.doctype)
    system_fields = get_annotation_system_fields()
    for field in meta.fields:
        if field.fieldname not in system_fields:
            if not getattr(ann, field.fieldname, None):
                return True
    return False

def get_annotation_response(ann) -> Union[Dict[str, Any], str]:
    meta = frappe.get_meta(ann.doctype)
    system_fields = get_annotation_system_fields()
    response = {}
    for field in meta.fields:
        if field.fieldname not in system_fields:
            response[field.fieldname] = getattr(ann, field.fieldname, "")
            
    if "output" in response and len(response) == 1:
        return response["output"]
        
    return response

def get_annotation_schema(doctype_name: str) -> dict:
    meta = frappe.get_meta(doctype_name)
    system_fields = get_annotation_system_fields()
    properties = {}
    required = []
    for field in meta.fields:
        if field.fieldname not in system_fields:
            field_type = "string"
            if field.fieldtype in ["Int", "Check"]:
                field_type = "integer"
            elif field.fieldtype in ["Float", "Currency"]:
                field_type = "number"
            properties[field.fieldname] = {"type": field_type, "description": field.label or field.fieldname}
            required.append(field.fieldname)
    return {
        "name": doctype_name.replace(" ", ""),
        "schema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }

def build_annotation_messages(ann) -> list:
    messages = []
    from markdownify import markdownify
    from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio
    from frappe_cadence.cadence.doctype.history.history import get_history

    sender_id = getattr(ann, "sender", None)
    cadence_ref = ann.reference_name if getattr(ann, "reference_doctype", None) == "Multi Channel Cadence" else None

    sender_bio_content = get_user_bio(sender_id, cadence_ref) if sender_id else None
    sender_bio = markdownify(sender_bio_content) if sender_bio_content else ""

    sender = frappe.db.get_value("User", sender_id, ["full_name"], as_dict=True) if sender_id else {}
    sender_name = sender.get("full_name") or ""

    if sender_name or sender_bio:
        messages.append({"role": "user", "content": f"Sender Name: {sender_name}\nSender Bio:\n{sender_bio}"})

    history_messages = get_history(ann.reference_doctype, ann.reference_name)
    messages.extend(history_messages)

    return messages

def update_annotation_output(annotation_doctype: str, annotation_id: str, output_text: Union[str, Dict[str, Any]]) -> bool:
    if not annotation_id or not output_text or not annotation_doctype:
        return False

    if isinstance(output_text, dict):
        for key, value in output_text.items():
            frappe.db.set_value(annotation_doctype, annotation_id, key, value)
        return True

    if isinstance(output_text, str):
        if output_text.strip().startswith("{"):
            try:
                parsed = json.loads(output_text)
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        frappe.db.set_value(annotation_doctype, annotation_id, key, value)
                    return True
            except Exception:
                pass

        if frappe.get_meta(annotation_doctype).has_field("output"):
            frappe.db.set_value(annotation_doctype, annotation_id, "output", output_text)
            return True

    return False

def handle_callback(**kwargs) -> dict:
    """
    Unified webhook callback handler for template Sift/n8n AI callbacks.
    """
    try:
        raw_payload = get_raw_payload(kwargs)
        payload = WebhookResponse(raw_payload)
        
        if payload.is_started:
            return {"status": "ignored"}
            
        communication_id = payload.metadata.get("name")
        if communication_id and frappe.db.exists("Communication", communication_id):
            comm = frappe.get_doc("Communication", communication_id)
            if comm.cadence_schedule:
                try:
                    schedule = frappe.get_doc("Cadence Multi Channel Schedule", comm.cadence_schedule)
                    if schedule.reference_doctype and schedule.reference_name:
                        template = frappe.get_doc(schedule.reference_doctype, schedule.reference_name)
                        if template.status == "Optimizing":
                            template.status = "Enabled" if template.enabled else "Disabled"
                            template.flags.ignore_links = True
                            template.save(ignore_permissions=True)
                except Exception as ex:
                    frappe.log_error("Failed to reset template status on callback failure", str(ex))

            if payload.is_failed:
                error_msg = payload.error or "Unknown error"
                frappe.log_error(title="Sift Callback Failed", message=error_msg)
                if comm.reference_doctype == "Multi Channel Cadence" and comm.reference_name:
                    if frappe.db.exists("Multi Channel Cadence", comm.reference_name):
                        mcc = frappe.get_doc("Multi Channel Cadence", comm.reference_name)
                        mcc.status = "Error"
                        mcc.save(ignore_permissions=True)
                emit_event("callback", {"communication_id": communication_id, "error": error_msg})
                return {"status": "failed", "error": error_msg}

        if not communication_id:
            return {"status": "error", "message": "Missing communication_id in metadata"}
            
        output_data = extract_output_text(payload.data)
        if not output_data:
            return {"status": "error", "message": "Missing output text"}
            
        if isinstance(output_data, dict):
            parsed_json = output_data
        elif isinstance(output_data, str):
            if output_data.strip().startswith("{"):
                try:
                    parsed_json = json.loads(output_data)
                    if not isinstance(parsed_json, dict):
                        parsed_json = {"content": output_data}
                except Exception:
                    parsed_json = {"content": output_data}
            else:
                parsed_json = {"content": output_data}
        else:
            parsed_json = {}
        
        comm = frappe.get_doc("Communication", communication_id)
        if parsed_json.get("subject"):
            comm.subject = parsed_json.get("subject")
        else:
            comm.subject = f"{comm.communication_medium} Message"

        if parsed_json.get("content"):
            raw_content = parsed_json.get("content")
        else:
            parts = [parsed_json.get(f) for f in ["salutation", "body", "call_to_action", "sign_off"] if parsed_json.get(f)]
            raw_content = "\n\n".join(parts) if parts else ""

        from frappe.utils import md_to_html
        comm.content = md_to_html(raw_content) if raw_content else ""
        comm.delivery_status = "Scheduled"
        comm.save(ignore_permissions=True)

        if comm.cadence_schedule:
            try:
                schedule = frappe.get_doc("Cadence Multi Channel Schedule", comm.cadence_schedule)
                if schedule.reference_doctype and schedule.reference_name:
                    template = frappe.get_doc(schedule.reference_doctype, schedule.reference_name)
                    if template.status == "Optimizing":
                        template.status = "Enabled" if template.enabled else "Disabled"
                        template.flags.ignore_links = True
                        template.save(ignore_permissions=True)
            except Exception as ex:
                frappe.log_error("Failed to reset template status on callback success", str(ex))
        
        emit_event("callback", {"communication_id": communication_id})

        return comm.as_dict()
    except Exception as e:
        frappe.log_error(title="Sift Callback Error", message=str(e))
        return {"status": "error", "message": str(e)}
