import os
from collections.abc import Generator

import frappe
import pytest
import requests
import vcr

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")

cadence_vcr = vcr.VCR(
	cassette_library_dir=CASSETTES_DIR,
	record_mode="new_episodes",
	match_on=["method", "scheme", "host", "port", "path", "query"],
	filter_headers=["Authorization"],
)


def get_test_listmonk_config() -> dict[str, str]:
	base_url = (
		frappe.conf.get("listmonk_base_url")
		or frappe.db.get_single_value("Listmonk Settings", "base_url")
		or "https://listmonk-dev.aurumor.com"
	).rstrip("/")
	token = (
		frappe.conf.get("listmonk_access_token")
		or frappe.get_doc("Listmonk Settings").get_password("access_token")
		or "IjRNcBZiUmG4DJ0JXnaU8cxmVp0mgQCam5KqqMMt2CXGEiqa"
	)
	webhook_secret = (
		frappe.conf.get("listmonk_webhook_secret")
		or frappe.get_doc("Listmonk Settings").get_password("webhook_secret")
		or "test_secret_key_12345"
	)
	return {
		"base_url": base_url,
		"username": "crm",
		"token": token or "IjRNcBZiUmG4DJ0JXnaU8cxmVp0mgQCam5KqqMMt2CXGEiqa",
		"webhook_secret": webhook_secret or "test_secret_key_12345",
	}


def is_listmonk_live() -> bool:
	config = get_test_listmonk_config()
	try:
		auth = None
		token = config["token"]
		username = config.get("username", "crm")
		headers = {"Content-Type": "application/json"}
		if token.startswith("token ") or token.startswith("Bearer ") or token.startswith("Basic "):
			headers["Authorization"] = token
		elif ":" in token:
			headers["Authorization"] = f"token {token}"
		else:
			headers["Authorization"] = f"token {username}:{token}"
		res = requests.get(f"{config['base_url']}/api/campaigns", headers=headers, auth=auth, timeout=3)
		return res.status_code == 200
	except Exception:
		return False


@pytest.fixture(scope="session")
def listmonk_config() -> dict[str, str]:
	return get_test_listmonk_config()


@pytest.fixture(autouse=True)
def setup_listmonk_settings(listmonk_config: dict[str, str]) -> Generator[None]:
	settings = frappe.get_doc("Listmonk Settings")
	settings.enabled = 1
	settings.base_url = listmonk_config["base_url"]
	settings.username = listmonk_config.get("username", "crm")
	settings.access_token = listmonk_config["token"]
	settings.status = "Authorized"
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	yield
