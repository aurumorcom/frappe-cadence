from pydantic import BaseModel, Field


class LeadEvaluationRequest(BaseModel):
	lead_name: str
	lead_status: str
	industry: str | None = None
	country: str | None = None


class LeadEvaluationResponse(BaseModel):
	lead_name: str
	eligible_cadences: list[str] = Field(default_factory=list)


LeadEvaluationRequest.model_rebuild()
LeadEvaluationResponse.model_rebuild()
