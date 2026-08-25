import frappe


def setUpModule() -> None:
	doctypes = [
		"Listmonk Settings",
		"Deep Research",
		"Deep Research Rule",
		"Deep Research History",
		"List",
		"CRM Lead List",
		"CRM Organization List",
	]
	for dt in doctypes:
		frappe.db.sql("UPDATE `tabDocType` SET module='Listmonk' WHERE name=%s", dt)
	frappe.db.commit()
	frappe.clear_cache()
