from typing import Optional

from pydantic import BaseModel, Field


class ListCreateRequest(BaseModel):
	name: str
	type: str = "public"  # public, private
	optin: str = "single"  # single, double
	tags: list[str] = Field(default_factory=list)


class ListUpdateRequest(BaseModel):
	name: str | None = None
	type: str | None = None
	optin: str | None = None
	tags: list[str] | None = None


class ListResponse(BaseModel):
	id: int
	name: str
	type: str
	optin: str


ListCreateRequest.model_rebuild()
ListUpdateRequest.model_rebuild()
ListResponse.model_rebuild()
