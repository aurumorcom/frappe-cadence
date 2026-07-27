from frappe.tests import UnitTestCase

class TestCommunicationEvents(UnitTestCase):
    def test_module_load(self):
        import frappe_cadence.cadence.doctype.communication.communication as comm_module
        self.assertIsNotNone(comm_module)
