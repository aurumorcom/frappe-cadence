from typing import Any, Optional

from pydantic import BaseModel, Field


class CampaignCreateRequest(BaseModel):
	name: str
	subject: str
	lists: list[int]
	type: str = "regular"
	content_type: str = "richtext"
	body: str
	send_at: str | None = None


class CampaignResponse(BaseModel):
	id: int
	name: str
	status: str


class TransactionalEmailRequest(BaseModel):
	subscriber_email: str
	template_id: int
	data: dict[str, Any] = Field(default_factory=dict)
	headers: list[dict[str, str]] = Field(default_factory=list)


CampaignCreateRequest.model_rebuild()
CampaignResponse.model_rebuild()
TransactionalEmailRequest.model_rebuild()
