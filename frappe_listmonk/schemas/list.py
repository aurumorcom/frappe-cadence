from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ListCreateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str
	crm_id: str
	type: str = "public"
	optin: str = "single"
	tags: list[str] = Field(default_factory=list)


class ListUpdateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str | None = None
	crm_id: str | None = None
	type: str = "public"
	optin: str = "single"
	tags: list[str] = Field(default_factory=list)


class ListResponse(BaseModel):
	model_config = ConfigDict(extra="ignore")

	id: int
	name: str
	crm_id: str | None = None
	type: str
	optin: str
	tags: list[str] = Field(default_factory=list)
