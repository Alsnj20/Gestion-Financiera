from pydantic import BaseModel


class UserResponseSchema(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    role: str = "USER"
    is_verified: bool = False
    timezone: str
    currency: str
