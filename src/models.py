from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(str, Enum):
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    CONFERENCE = "conference"
    REFERRAL = "referral"
    EMAIL = "email"
    COLD_OUTREACH = "cold_outreach"
    OTHER = "other"


class InteractionType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    LINKEDIN_MESSAGE = "linkedin_message"
    NOTE = "note"


class LeadBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    lead_source: Optional[LeadSource] = LeadSource.OTHER
    status: LeadStatus = LeadStatus.NEW
    score: int = Field(0, ge=0, le=100)
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    lead_source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class Lead(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    lead_id: int
    interaction_type: InteractionType
    content: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class Interaction(InteractionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeadWithInteractions(Lead):
    interactions: list[Interaction] = []


class LeadResponse(BaseModel):
    leads: list[Lead]
    total: int
    page: int = 1
    per_page: int = 10


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class LeadQualificationRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    additional_context: Optional[str] = None


class LeadQualificationResponse(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Lead qualification score from 0-100")
    reasoning: str = Field(..., min_length=10, description="Detailed reasoning for the score")
    key_factors: list[str] = Field(..., description="Key factors that influenced the score")
    recommended_actions: list[str] = Field(..., description="Recommended next steps")
    priority_level: str = Field(..., description="Priority level: high, medium, low")


class MessagePersonalizationRequest(BaseModel):
    lead_name: str
    lead_email: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    lead_source: Optional[str] = None
    previous_interactions: Optional[list[str]] = None
    campaign_type: str = Field(..., description="Type of campaign: cold_outreach, follow_up, demo_request, etc.")
    message_tone: str = Field(default="professional", description="Tone: professional, casual, friendly, formal")


class MessageVariant(BaseModel):
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    channel: str = Field(default="email", description="Communication channel")
    estimated_effectiveness: int = Field(..., ge=0, le=100, description="Estimated effectiveness score")


class MessagePersonalizationResponse(BaseModel):
    variants: list[MessageVariant] = Field(..., min_items=1, max_items=3, description="Message variants")
    personalization_factors: list[str] = Field(..., description="Factors used for personalization")
    best_send_time: Optional[str] = Field(None, description="Recommended send time")
    follow_up_strategy: str = Field(..., description="Recommended follow-up approach")


class ScoringCriteriaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    weight: int = Field(..., ge=1, le=100, description="Weight percentage (1-100)")
    is_active: bool = True


class ScoringCriteriaCreate(ScoringCriteriaBase):
    pass


class ScoringCriteriaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    weight: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None


class ScoringCriteria(ScoringCriteriaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PipelineStageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    stage_order: int = Field(..., ge=1)
    is_active: bool = True
    auto_progression_rules: Optional[str] = None

class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    stage_order: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    auto_progression_rules: Optional[str] = None


class PipelineStage(PipelineStageBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeadPipelineHistoryBase(BaseModel):
    lead_id: int
    stage_id: int
    previous_stage_id: Optional[int] = None
    notes: Optional[str] = None


class LeadPipelineHistoryCreate(LeadPipelineHistoryBase):
    pass


class LeadPipelineHistory(LeadPipelineHistoryBase):
    id: int
    entered_at: datetime
    exited_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LeadWithPipeline(Lead):
    current_stage: Optional[PipelineStage] = None
    pipeline_history: list[LeadPipelineHistory] = []
    interactions: list[Interaction] = []


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: Optional[dict] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
