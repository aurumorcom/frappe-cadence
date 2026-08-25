from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class WebhookCreateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str
	url: str
	events: list[str] = Field(default_factory=list)
	enabled: bool = True
	secret: str | None = None


class WebhookUpdateRequest(BaseModel):
	model_config = ConfigDict(extra="ignore")

	name: str | None = None
	url: str | None = None
	events: list[str] | None = None
	enabled: bool | None = None
	secret: str | None = None


class WebhookResponse(BaseModel):
	model_config = ConfigDict(extra="ignore")

	id: int
	name: str
	url: str
	events: list[str] = Field(default_factory=list)
	enabled: bool


class WebhookEventPayload(BaseModel):
	model_config = ConfigDict(extra="ignore")

	event: str | None = None
	event_type: str | None = None
	data: dict[str, Any] = Field(default_factory=dict)
