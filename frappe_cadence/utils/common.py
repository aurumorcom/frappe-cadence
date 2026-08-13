import re
from datetime import datetime, timedelta
from typing import Optional

import frappe
from frappe.utils import add_days, now_datetime


def calculate_delay_date(days: int, start_date: datetime | None = None) -> datetime:
	base = start_date or now_datetime()
	return base + timedelta(days=days)


def clean_html(raw_html: str) -> str:
	if not raw_html:
		return ""
	clean = re.sub(r"<[^>]+>", "", raw_html)
	return clean.strip()


def format_signature(user_name: str, role: str | None = None, company: str | None = None) -> str:
	parts = [f"<b>{user_name}</b>"]
	if role:
		parts.append(role)
	if company:
		parts.append(company)
	return "<br>".join(parts)
