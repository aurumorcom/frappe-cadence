import frappe
from frappe_cadence._template import handle_callback

@frappe.whitelist(allow_guest=True)
def callback():
    """
    Webhook endpoint for Sift callbacks for WhatsApp Template.
    """
    return handle_callback()
