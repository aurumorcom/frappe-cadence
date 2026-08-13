from pydantic import BaseModel


class MCCStatusUpdateRequest(BaseModel):
	mcc_name: str
	status: str
	reason: str | None = None


MCCStatusUpdateRequest.model_rebuild()
