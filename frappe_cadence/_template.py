import json
import frappe
from typing import Dict, Any, Union
from frappe_controller.utils.controller import emit_event

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

def update_annotation_output(annotation_doctype: str, annotation_id: str, output_text: str) -> bool:
    if not annotation_id or not output_text or not annotation_doctype:
        return False

    if output_text.strip().startswith("{"):
        try:
            parsed = json.loads(output_text)
            for key, value in parsed.items():
                frappe.db.set_value(annotation_doctype, annotation_id, key, value)
            return True
        except Exception:
            if frappe.get_meta(annotation_doctype).has_field("output"):
                frappe.db.set_value(annotation_doctype, annotation_id, "output", output_text)
                return True
    else:
        frappe.db.set_value(annotation_doctype, annotation_id, "output", output_text)
        return True

    return False

def handle_callback() -> dict:
    """
    Unified webhook callback handler for template Sift/n8n AI callbacks.
    """
    try:
        payload = frappe.request.json
        event_type = payload.get("type")
        
        if event_type and event_type.endswith(".started"):
            return {"status": "ignored"}
            
        communication_id = payload.get("metadata", {}).get("name")
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

            if event_type and event_type.endswith(".failed"):
                error_msg = payload.get("error") or "Unknown error"
                frappe.log_error(title="Sift Callback Failed", message=error_msg)
                comm.delivery_status = "Failed"
                comm.content = f"AI Generation Failed: {error_msg}"
                comm.save(ignore_permissions=True)
                emit_event("callback", {"communication_id": communication_id, "error": error_msg})
                return {"status": "failed"}

        if not communication_id:
            return {"status": "error", "message": "Missing communication_id in metadata"}
            
        data = payload.get("data", [])
        output_text = ""
        if isinstance(data, list) and len(data) > 0:
            content_list = data[0].get("content", [])
            if content_list and isinstance(content_list, list) and len(content_list) > 0:
                output_text = content_list[0].get("text", "")
                
        if not output_text:
            return {"status": "error", "message": "Missing output text"}
            
        parsed_json = json.loads(output_text)
        
        comm = frappe.get_doc("Communication", communication_id)
        if parsed_json.get("subject"):
            comm.subject = parsed_json.get("subject")
        else:
            comm.subject = f"{comm.communication_medium} Message"
        comm.content = parsed_json.get("content")
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
        
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(title="Sift Callback Error", message=str(e))
        return {"status": "error", "message": str(e)}
