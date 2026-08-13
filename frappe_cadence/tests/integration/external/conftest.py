from typing import Generator
import pytest
import requests
import frappe


def get_test_listmonk_config() -> dict[str, str]:
	base_url = (
		frappe.conf.get("listmonk_base_url")
		or frappe.db.get_single_value("Listmonk Settings", "base_url")
		or "http://localhost:9000"
	).rstrip("/")
	token = (
		frappe.conf.get("listmonk_access_token")
		or frappe.get_doc("Listmonk Settings").get_password("access_token")
	)
	webhook_secret = (
		frappe.conf.get("listmonk_webhook_secret")
		or frappe.get_doc("Listmonk Settings").get_password("webhook_secret")
		or "test_secret_key_12345"
	)
	return {
		"base_url": base_url,
		"token": token or "",
		"webhook_secret": webhook_secret or "",
	}


def is_listmonk_live() -> bool:
	config = get_test_listmonk_config()
	try:
		res = requests.get(f"{config['base_url']}/api/health", timeout=2)
		return res.status_code == 200 or res.status_code == 403
	except Exception:
		return False


@pytest.fixture(scope="session")
def listmonk_config() -> dict[str, str]:
	return get_test_listmonk_config()


@pytest.fixture(autouse=True)
def setup_listmonk_settings(listmonk_config: dict[str, str]) -> Generator[None, None, None]:
	settings = frappe.get_doc("Listmonk Settings")
	settings.enabled = 1
	settings.base_url = listmonk_config["base_url"]
	settings.status = "Authorized"
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	yield
