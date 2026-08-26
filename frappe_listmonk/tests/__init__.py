try:
	import frappe

	def setUpModule() -> None:
		doctypes = [
			"Listmonk Settings",
			"Deep Research",
			"Deep Research Rule",
			"Source",
			"Deep Research Source",
			"List",
			"CRM Lead List",
			"CRM Organization List",
		]
		if hasattr(frappe, "db") and frappe.db:
			for dt_name in ["source", "deep_research_source"]:
				try:
					frappe.reload_doc("listmonk", "doctype", dt_name, force=True)
				except Exception:
					pass
			for dt in doctypes:
				frappe.db.sql("UPDATE `tabDocType` SET module='Listmonk' WHERE name=%s", dt)
			frappe.db.commit()
			frappe.clear_cache()
except ImportError:
	pass
