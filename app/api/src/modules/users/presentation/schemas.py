from pydantic import BaseModel, EmailStr, Field
from modules.users.application.use_cases.create_user import CreateUserInput


class CreateUserRequestSchema(BaseModel):
    """Schema Pydantic para deserializar y validar el Request HTTP."""
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=7, max_length=20)
    email: EmailStr | str = ""
    timezone: str = Field(default="America/Lima", max_length=64)
    currency: str = Field(default="PEN", max_length=10)

    def to_input_dto(self) -> CreateUserInput:
        """Traducción explícita del Schema HTTP al DTO de la Capa de Aplicación."""
        return CreateUserInput(
            name=self.name,
            phone=self.phone,
            email=self.email,
            timezone=self.timezone,
            currency=self.currency,
        )


class UserResponseSchema(BaseModel):
    """Presenter DTO para estandarizar la salida JSON."""
    id: str
    name: str
    phone: str
    email: str
    timezone: str
    currency: str
