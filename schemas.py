from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    ip_address: Optional[str] = None
    method: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    timestamp: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditFindingResponse(BaseModel):
    id: int
    rule_id: str
    risk_level: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    description: str
    recommendation: str
    urgency: str
    score: int
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class RiskScoreResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    score: int
    risk_level: str
    breakdown: dict = {}
    calculated_at: Optional[str] = None

    model_config = {"from_attributes": True}
