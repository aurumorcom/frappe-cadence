import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.cadence.cadence import delete_sequence, upsert_sequence
from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config


class TestCadence(FrappeTestCase):
	def setUp(self) -> None:
		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.base_url
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

		self.cadence = frappe.get_doc({
			"doctype": "Cadence",
			"cadence_name": "External Integration Test Cadence",
			"enabled": 1,
			"description": "Sequence description for external test",
		}).insert(ignore_permissions=True, ignore_links=True)

	def test_upsert_and_delete_sequence_live_sync(self) -> None:
		# Upsert sequence against live Listmonk API
		upsert_sequence(self.cadence.name)
		self.cadence.reload()
		self.assertIsNotNone(self.cadence.listmonk_id)

		seq_id = self.cadence.listmonk_id

		# Delete sequence against live Listmonk API
		delete_sequence(int(seq_id))
