# schemas.py
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    title: str = Field(..., description="Short label for the action item.")
    owner: Optional[str] = Field(
        None, description="Person responsible for this item, if mentioned."
    )
    dueDate: Optional[date] = Field(
        None,
        description="Due date in ISO format YYYY-MM-DD, or null if no clear date.",
    )
    priority: Literal["low", "medium", "high"] = Field(
        "medium", description="Importance level inferred from the text."
    )


class ConversationAnalysis(BaseModel):
    """
    Structured analysis of a free-form user message or conversation.

    This is the main schema enforced by the structured chat client.
    """

    summary: str = Field(
        ...,
        description="One-paragraph summary of the user's message in plain English.",
    )
    intent: str = Field(
        ...,
        description="Primary intent of the user (e.g., 'bug_report', 'feature_request', 'planning', 'chitchat').",
    )
    sentiment: Literal["positive", "neutral", "negative", "mixed"] = Field(
        ...,
        description="Overall sentiment detected in the message.",
    )
    actionItems: List[ActionItem] = Field(
        default_factory=list,
        description="List of concrete tasks implied by the message.",
    )
    needsFollowUp: bool = Field(
        ...,
        description="True if a human should follow up, False otherwise.",
    )
    riskLevel: Literal["none", "low", "medium", "high"] = Field(
        "none",
        description="Risk level based on the message (e.g., compliance, escalation, safety).",
    )
