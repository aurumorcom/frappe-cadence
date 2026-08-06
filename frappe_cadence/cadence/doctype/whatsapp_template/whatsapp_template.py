import frappe
from frappe.model.document import Document

class WhatsAppTemplate(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from frappe_cadence.cadence.doctype.whatsapp_template_annotation.whatsapp_template_annotation import WhatsappTemplateAnnotation

        annotations: DF.Table[WhatsappTemplateAnnotation]
        enabled: DF.Check
        message: DF.TextEditor | None
        provider: DF.Literal["Frappe", "DSPy", "n8n"]
        request_url: DF.Data | None
        sift_id: DF.Data | None
        status: DF.Literal["Enabled", "Disabled", "Optimizing", "Predicting"]
        title: DF.Data
        webhook_secret: DF.Password | None
        whatsapp_template_code: DF.Data | None
    # end: auto-generated types

def before_save(doc, method=None):
    if doc.has_value_changed("enabled"):
        doc.status = "Enabled" if doc.enabled else "Disabled"
    elif doc.has_value_changed("status"):
        if doc.status == "Disabled":
            doc.enabled = 0
        elif doc.status == "Enabled":
            doc.enabled = 1
    elif doc.status not in ["Optimizing", "Predicting"]:
        doc.status = "Enabled" if doc.enabled else "Disabled"

def on_update(doc, method=None):
    doc_before_save = doc.get_doc_before_save()
    if doc_before_save and doc_before_save.status != doc.status:
        from frappe_controller.utils.controller import emit_event
        event_key = f"{doc.doctype.lower().replace(' ', '_')}_enabled"
        emit_event(
            key=event_key,
            argument={
                "doctype": doc.doctype,
                "name": doc.name,
                "enabled": 1 if doc.status == "Enabled" else 0
            }
        )
