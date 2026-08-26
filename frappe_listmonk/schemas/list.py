from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ListCreateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str
	crm_id: str
	type: str = "private"
	optin: str = "single"


class ListUpdateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str | None = None
	crm_id: str | None = None
	type: str = "private"
	optin: str = "single"


class ListResponse(BaseModel):
	model_config = ConfigDict(extra="ignore")

	id: int
	name: str
	crm_id: str | None = None
	type: str = "private"
	optin: str = "single"
