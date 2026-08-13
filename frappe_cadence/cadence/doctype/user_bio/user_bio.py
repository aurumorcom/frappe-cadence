from typing import Optional

import frappe
from frappe import _
from frappe.model.document import Document


class UserBio(Document):
	def validate(self) -> None:
		if self.has_value_changed("content") or self.is_new():
			if frappe.session.user != self.reference_user and "System Manager" not in frappe.get_roles():
				frappe.throw(_("You can only edit your own bio."), frappe.PermissionError)

	def has_permission(self, ptype: str = "read", user: str | None = None) -> bool:
		if not user:
			user = frappe.session.user

		if user != self.reference_user and "System Manager" not in frappe.get_roles(user):
			return False

		return True


@frappe.whitelist()
def get_user_bio(reference_user: str, reference_cadence: str | None = None) -> str | None:
	"""Returns the content of a User Bio based on precedence:

	1. Bio with reference_cadence
	2. Bio with is_default=1
	Both must be enabled.
	Returns None if no matching bio is found.
	"""
	if reference_cadence:
		bio = frappe.get_all(
			"User Bio",
			filters={
				"reference_user": reference_user,
				"reference_cadence": reference_cadence,
				"enabled": 1,
			},
			fields=["content"],
			limit=1,
		)
		if bio:
			return bio[0].get("content") if isinstance(bio[0], dict) else getattr(bio[0], "content", None)

	bio = frappe.get_all(
		"User Bio",
		filters={
			"reference_user": reference_user,
			"is_default": 1,
			"enabled": 1,
		},
		fields=["content"],
		limit=1,
	)
	if bio:
		return bio[0].get("content") if isinstance(bio[0], dict) else getattr(bio[0], "content", None)

	return None
