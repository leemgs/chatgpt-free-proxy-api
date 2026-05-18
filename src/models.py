from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: List[ChatMessage]
    stream: bool = False
