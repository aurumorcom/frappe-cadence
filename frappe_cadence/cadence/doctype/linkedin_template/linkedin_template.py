import frappe
from frappe.model.document import Document

class LinkedInTemplate(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from frappe_cadence.cadence.doctype.linkedin_template_annotation.linkedin_template_annotation import LinkedinTemplateAnnotation

        annotations: DF.Table[LinkedinTemplateAnnotation]
        enabled: DF.Check
        linkedin_template_code: DF.Data | None
        message: DF.TextEditor | None
        provider: DF.Literal["Frappe", "DSPy", "n8n"]
        request_url: DF.Data | None
        sift_id: DF.Data | None
        status: DF.Literal["Enabled", "Disabled", "Optimizing", "Predicting"]
        title: DF.Data
        webhook_secret: DF.Password | None
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

