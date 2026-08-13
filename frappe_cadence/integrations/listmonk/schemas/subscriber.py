from typing import Any, Optional

from pydantic import BaseModel, Field


class SubscriberCreateRequest(BaseModel):
	email: str
	name: str
	status: str = "enabled"
	lists: list[int] = Field(default_factory=list)
	attribs: dict[str, Any] = Field(default_factory=dict)
	preconfirm_subscriptions: bool = True


class SubscriberUpdateRequest(BaseModel):
	email: str | None = None
	name: str | None = None
	status: str | None = None
	lists: list[int] | None = None
	attribs: dict[str, Any] | None = None


class SubscriberResponse(BaseModel):
	id: int
	email: str
	name: str
	status: str
	lists: list[dict[str, Any]] = Field(default_factory=list)
	attribs: dict[str, Any] = Field(default_factory=dict)


class SubscriberListModifyRequest(BaseModel):
	action: str  # add, remove, unsubscribe
	ids: list[int]
	target_list_ids: list[int]
	status: str = "confirmed"


SubscriberCreateRequest.model_rebuild()
SubscriberUpdateRequest.model_rebuild()
SubscriberResponse.model_rebuild()
SubscriberListModifyRequest.model_rebuild()
