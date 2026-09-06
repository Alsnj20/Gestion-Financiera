from pydantic import BaseModel, Field
from modules.tags.application.use_cases.create_tag import CreateTagInput


class CreateTagRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=40)

    def to_input_dto(self) -> CreateTagInput:
        return CreateTagInput(user_id=self.user_id, name=self.name)


class TagResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
