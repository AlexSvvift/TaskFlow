from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class OrderStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    company: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None
    email: EmailStr | None
    phone: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class OrderCreate(BaseModel):
    client_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: OrderStatus = OrderStatus.NEW
    amount: float = Field(default=0, ge=0, le=100_000_000)


class OrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: OrderStatus | None = None
    amount: float | None = Field(default=None, ge=0, le=100_000_000)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    created_by_id: int
    title: str
    description: str | None
    status: OrderStatus
    amount: float
    client_name: str | None = None
    created_at: datetime
    updated_at: datetime


class DashboardResponse(BaseModel):
    total_clients: int
    total_orders: int
    new_orders: int
    active_orders: int
    completed_orders: int
    total_revenue: float


class HealthResponse(BaseModel):
    status: str
    service: str


class ErrorResponse(BaseModel):
    detail: str
