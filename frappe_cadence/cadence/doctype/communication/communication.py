import frappe
from frappe_controller.utils.controller import emit_event

def on_update(doc, method=None):
    """
    On Communication update, if referenced to Multi Channel Cadence,
    evaluate MCC status transitions:
    - If MCC is in Draft and all steps are Scheduled or Sent:
      - If any step is Sent -> transition MCC to In Progress
      - Else -> transition MCC to Scheduled
    - If MCC is in Scheduled and any step is Sent -> transition MCC to In Progress
    """
    try:
        reference_doctype = getattr(doc, "reference_doctype", None)
        reference_name = getattr(doc, "reference_name", None)

        if reference_doctype != "Multi Channel Cadence" or not reference_name:
            return

        mcc_name = reference_name
        if not frappe.db.exists("Multi Channel Cadence", mcc_name):
            return

        mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
        if mcc.status not in ["Draft", "Scheduled"]:
            return

        if not mcc.cadence_name or not frappe.db.exists("Cadence", mcc.cadence_name):
            return

        cadence = frappe.get_doc("Cadence", mcc.cadence_name)
        if not cadence.cadence_schedules:
            return

        schedule_names = [s.name for s in cadence.cadence_schedules]

        comms = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "Multi Channel Cadence",
                "reference_name": mcc_name,
                "cadence_schedule": ["in", schedule_names],
                "delivery_status": ["in", ["Scheduled", "Sent"]]
            },
            fields=["cadence_schedule", "delivery_status"]
        )

        completed_schedules = {c.cadence_schedule for c in comms}
        if len(completed_schedules) < len(schedule_names):
            return

        has_sent = any(c.delivery_status == "Sent" for c in comms)

        if mcc.status == "Draft":
            target_status = "In Progress" if has_sent else "Scheduled"
        elif mcc.status == "Scheduled":
            if has_sent:
                target_status = "In Progress"
            else:
                return
        else:
            return

        if mcc.status != target_status:
            mcc.status = target_status
            mcc.flags.ignore_permissions = True
            mcc.save()

            event_key = "mcc_in_progress" if target_status == "In Progress" else "mcc_scheduled"
            emit_event(event_key, {"doctype": "Multi Channel Cadence", "name": mcc_name})
    except Exception as e:
        frappe.log_error("Failed to transition MCC status on communication update", str(e))
