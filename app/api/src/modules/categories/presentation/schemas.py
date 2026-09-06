from pydantic import BaseModel, Field
from modules.categories.application.use_cases.create_category import CreateCategoryInput


class CreateCategoryRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=80)
    type: str = Field(default="BOTH", max_length=20)
    parent_id: str = Field(default="", max_length=100)

    def to_input_dto(self) -> CreateCategoryInput:
        return CreateCategoryInput(user_id=self.user_id, name=self.name, type=self.type, parent_id=self.parent_id)


class CategoryResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    parent_id: str
    status: str
