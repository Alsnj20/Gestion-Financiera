from pydantic import BaseModel, Field
from modules.conversations.application.use_cases.create_conversation_message import CreateConversationMessageInput


class CreateConversationMessageRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    channel: str = Field(default="DASHBOARD", max_length=20)
    external_message_id: str = Field(..., min_length=1, max_length=120)
    direction: str = Field(default="INBOUND", max_length=20)
    content: str = Field(default="", max_length=5000)
    parsed_intent: str = Field(default="", max_length=60)
    parsed_payload: dict | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    def to_input_dto(self) -> CreateConversationMessageInput:
        return CreateConversationMessageInput(
            user_id=self.user_id,
            channel=self.channel,
            external_message_id=self.external_message_id,
            direction=self.direction,
            content=self.content,
            parsed_intent=self.parsed_intent,
            parsed_payload=self.parsed_payload,
            confidence=self.confidence,
        )


class ConversationMessageResponseSchema(BaseModel):
    id: str
    user_id: str
    channel: str
    external_message_id: str
    direction: str
    content: str
    parsed_intent: str
