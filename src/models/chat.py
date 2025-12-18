# src\models\chat.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=5000, description="The user's chat message.")
    history: List[Dict[str, str]] = Field(default=[], description="A list of previous conversation turns.")
    selected_text: Optional[str] = Field(default=None, max_length=10000, description="Text selected by user from the documentation.")
