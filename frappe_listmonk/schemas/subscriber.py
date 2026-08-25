from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SubscriberCreateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	email: str
	name: str
	crm_id: str
	status: str = "enabled"
	lists: list[int] = Field(default_factory=list)
	attribs: dict[str, Any] = Field(default_factory=dict)


class SubscriberUpdateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	email: str | None = None
	name: str | None = None
	crm_id: str | None = None
	status: str | None = None
	lists: list[int] | None = None
	attribs: dict[str, Any] | None = None


class SubscriberListModifyRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	ids: list[int] = Field(default_factory=list)
	target_list_ids: list[int] = Field(default_factory=list)
	action: str = "add"
	status: str = "confirmed"


class SubscriberResponse(BaseModel):
	model_config = ConfigDict(extra="ignore")

	id: int
	uuid: str | None = None
	email: str
	name: str
	phone: str | None = None
	crm_id: str | None = None
	status: str
	attribs: dict[str, Any] = Field(default_factory=dict)
