app_name = "frappe_cadence"
app_title = "Frappe Cadence"
app_publisher = "Aurumor"
app_description = "Open-Source Cold Outreach & Sales Engagement Automation"
app_email = "hello@aurumor.com"
app_license = "mit"

# Apps
required_apps = ["frappe_controller", "frappe_playbook", "crm"]

# include js in doctype views
doctype_js = {
	"User": "cadence/doctype/user/user.js",
	"Cadence": "cadence/doctype/cadence/cadence.js",
	"Listmonk Settings": "cadence/doctype/listmonk_settings/listmonk_settings.js",
}
doctype_list_js = {
	"Communication": "cadence/doctype/communication/communication_list.js",
	"Multi Channel Cadence": "cadence/doctype/multi_channel_cadence/multi_channel_cadence_list.js",
}

# Document Events
doc_events = {
	"CRM Lead": {
		"on_update": "frappe_cadence.cadence.doctype.crm_lead.crm_lead.on_update",
		"on_trash": "frappe_cadence.cadence.doctype.crm_lead.crm_lead.on_trash",
	},
	"Cadence": {
		"on_update": "frappe_cadence.cadence.doctype.cadence.cadence.on_update",
		"on_trash": "frappe_cadence.cadence.doctype.cadence.cadence.on_trash",
	},
	"Multi Channel Cadence": {
		"on_update": "frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.on_update",
		"on_trash": "frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.on_trash",
	},
	"Playbook Execution": {
		"on_update": "frappe_cadence.cadence.doctype.playbook_execution.playbook_execution.on_update",
	},
	"Communication": {
		"on_update": "frappe_cadence.cadence.doctype.communication.communication.on_update",
	},
}

# Scheduled Tasks
scheduler_events = {}

# Controller Events
controller_events = {
	"frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings.setup_webhook": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings.sync_all_crm_leads": {
		"retries": 1,
		"timeout": 600,
	},
	"frappe_cadence.cadence.doctype.crm_lead.crm_lead.upsert_contact": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.crm_lead.crm_lead.delete_contact": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.crm_lead.crm_lead.evaluate_cadences_for_lead": {
		"retries": 1,
		"timeout": 300,
	},
	"frappe_cadence.cadence.doctype.cadence.cadence.upsert_sequence": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.cadence.cadence.update_sequence_status": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.cadence.cadence.delete_sequence": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.cadence.cadence.evaluate_leads_for_cadence": {
		"retries": 1,
		"timeout": 300,
	},
	"frappe_cadence.cadence.doctype.cadence.cadence.add_lead_batch_to_cadence": {
		"retries": 3,
		"timeout": 300,
	},
	"frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.add_contact_to_sequence": {
		"retries": 3,
		"timeout": 120,
	},
	"frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.remove_contact_from_sequence": {
		"retries": 3,
		"timeout": 120,
	},
}

export_python_type_annotations = True
require_type_annotated_api_methods = True

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "in", ["Cadence", "CRM"]]]},
	{"dt": "Property Setter", "filters": [["module", "in", ["Cadence"]]]},
]
