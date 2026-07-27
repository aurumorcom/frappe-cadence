import unittest
from unittest.mock import patch, MagicMock
import frappe
from frappe.tests import UnitTestCase

from frappe_cadence.cadence.doctype.communication.communication import on_update, after_insert

class TestCommunicationEvents(UnitTestCase):

    def test_on_update(self):
        doc = MagicMock()
        on_update(doc)

    def test_after_insert(self):
        doc = MagicMock()
        after_insert(doc)
