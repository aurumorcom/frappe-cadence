app_name = "frappe_listmonk"
app_title = "Frappe Listmonk"
app_publisher = "Aurumor"
app_description = "Listmonk Integration & Deep Research Automation for Frappe CRM"
app_email = "hello@aurumor.com"
app_license = "mit"

required_apps = ["frappe_controller", "frappe_playbook", "crm"]

# include js in doctype views
doctype_js = {
	"User": "listmonk/doctype/user/user.js",
	"Listmonk Settings": "listmonk/doctype/listmonk_settings/listmonk_settings.js",
	"List": "listmonk/doctype/list/list.js",
	"Deep Research Rule": "listmonk/doctype/deep_research_rule/deep_research_rule.js",
	"Deep Research": "listmonk/doctype/deep_research/deep_research.js",
}

controller_events = {
	# Listmonk Integration Jobs
	"frappe_listmonk.jobs.webhook.setup_webhook": {
		"rate_limit_per_minute": 30,
		"retries": 3,
	},
	"frappe_listmonk.jobs.subscriber.sync_all_subscribers": {
		"rate_limit_per_minute": 10,
		"retries": 1,
	},
	"frappe_listmonk.jobs.subscriber.upsert_subscriber": {
		"rate_limit_per_minute": 120,
		"retries": 3,
	},
	"frappe_listmonk.jobs.subscriber.delete_subscriber": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	"frappe_listmonk.jobs.user.sync_all_crm_users": {
		"rate_limit_per_minute": 10,
		"retries": 1,
	},
	"frappe_listmonk.jobs.user.update_user": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	"frappe_listmonk.jobs.list.sync_all_lists": {
		"rate_limit_per_minute": 30,
		"retries": 1,
	},
	"frappe_listmonk.jobs.list.upsert_list": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	"frappe_listmonk.jobs.list.evaluate_doc_for_list": {
		"rate_limit_per_minute": 60,
		"retries": 1,
	},
	"frappe_listmonk.jobs.subscriber.process_deep_research_request": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
	"frappe_listmonk.jobs.subscriber.update_subscriber_campaign_subscriber": {
		"rate_limit_per_minute": 60,
		"retries": 3,
	},
}

doc_events = {
	"User": {
		"on_update": "frappe_listmonk.listmonk.doctype.user.user.on_update",
	},
	"CRM Lead": {
		"on_update": "frappe_listmonk.listmonk.doctype.crm_lead.crm_lead.on_update",
		"on_trash": "frappe_listmonk.listmonk.doctype.crm_lead.crm_lead.on_trash",
	},
	"Playbook Execution": {
		"on_update": "frappe_listmonk.listmonk.doctype.playbook_execution.playbook_execution.on_update",
	},
}

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "in", ["Listmonk", "CRM"]]]},
	{"dt": "Property Setter", "filters": [["module", "in", ["Listmonk"]]]},
]
