from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
	model_config = ConfigDict(extra="ignore")

	id: int
	email: str
	name: str
	crm_id: str | None = None
