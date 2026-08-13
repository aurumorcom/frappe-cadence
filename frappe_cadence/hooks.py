app_name = "frappe_cadence"
app_title = "Frappe Cadence"
app_publisher = "Aurumor"
app_description = "Open-Source Cold Outreach & Sales Engagement Automation"
app_email = "hello@aurumor.com"
app_license = "mit"

required_apps = ["frappe_controller", "frappe_playbook", "crm"]

# include js in doctype views
doctype_js = {
	"User": "cadence/doctype/user/user.js",
	"Cadence": "cadence/doctype/cadence/cadence.js",
	"Listmonk Settings": "cadence/doctype/listmonk_settings/listmonk_settings.js",
}
doctype_list_js = {
	"Multi Channel Cadence": "cadence/doctype/multi_channel_cadence/multi_channel_cadence_list.js",
}

controller_events = {
	# Listmonk Integration Jobs
	"frappe_cadence.integrations.listmonk.jobs.webhook.setup_webhook": {
		"rate_limit_per_minute": 30,
		"retries": 3,
	},
	"frappe_cadence.integrations.listmonk.jobs.contact.sync_all_crm_leads": {
		"rate_limit_per_minute": 10,
		"retries": 1,
	},
	"frappe_cadence.integrations.listmonk.jobs.contact.upsert_contact": {
		"rate_limit_per_minute": 120,
		"retries": 3,
	},
	"frappe_cadence.integrations.listmonk.jobs.contact.delete_contact": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	# Core Cadence Jobs
	"frappe_cadence.jobs.cadence.upsert_sequence": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_cadence.jobs.cadence.update_sequence_status": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_cadence.jobs.cadence.delete_sequence": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_cadence.jobs.cadence.evaluate_leads_for_cadence": {"rate_limit_per_minute": 30, "retries": 1},
	"frappe_cadence.jobs.cadence.evaluate_cadences_for_lead": {"rate_limit_per_minute": 60, "retries": 1},
	"frappe_cadence.jobs.cadence.add_lead_batch_to_cadence": {"rate_limit_per_minute": 60, "retries": 3},
	# Multi Channel Cadence Jobs
	"frappe_cadence.jobs.multi_channel_cadence.add_contact_to_sequence": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	"frappe_cadence.jobs.multi_channel_cadence.remove_contact_from_sequence": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
}

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
}

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "in", ["Cadence", "CRM"]]]},
	{"dt": "Property Setter", "filters": [["module", "in", ["Cadence"]]]},
]
