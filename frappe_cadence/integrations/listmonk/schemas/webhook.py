from typing import Any, Optional

from pydantic import BaseModel, Field


class WebhookCreateRequest(BaseModel):
	name: str
	url: str
	events: list[str] = Field(
		default_factory=lambda: ["campaign.started", "subscriber.bounced", "campaign.sent"]
	)
	headers: dict[str, str] = Field(default_factory=dict)
	secret: str | None = None
	enabled: bool = True


class WebhookUpdateRequest(BaseModel):
	name: str | None = None
	url: str | None = None
	events: list[str] | None = None
	headers: dict[str, str] | None = None
	secret: str | None = None
	enabled: bool | None = None


class WebhookResponse(BaseModel):
	id: int
	name: str
	url: str
	events: list[str] = Field(default_factory=list)
	enabled: bool = True


class WebhookEventPayload(BaseModel):
	event: str  # campaign.started, campaign.sent, campaign.link_clicked, subscriber.bounced
	data: dict[str, Any] = Field(default_factory=dict)


WebhookCreateRequest.model_rebuild()
WebhookUpdateRequest.model_rebuild()
WebhookResponse.model_rebuild()
WebhookEventPayload.model_rebuild()
