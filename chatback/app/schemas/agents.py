from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

class DiagramType(str, Enum):
    CLASS = "class"
    ACTIVITY = "activity"
    USECASE = "usecase"
    SEQUENCE = "sequence"

class Message(BaseModel):
    type: str = Field(..., description="Type of message (human/ai)")
    content: str = Field(..., description="Content of the message")

# Interview Models
class InterviewSession(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    username: str = Field(..., description="Username of the session owner")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    messages: List[Message] = Field(default_factory=list, description="List of conversation messages")
    status: str = Field(..., description="Current session status")

class InterviewResponse(BaseModel):
    message: str = Field(..., description="Response message from the interview agent")
    session_id: Optional[str] = Field(None, description="Session ID for the interview")

class InterviewSessionList(BaseModel):
    sessions: List[InterviewSession] = Field(..., description="List of interview sessions")

# Document Models
class Document(BaseModel):
    document_id: str = Field(..., description="Document identifier")
    chat_name: str = Field(..., description="Name of the chat session")
    created_at: datetime = Field(..., description="Document creation timestamp")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    content: str = Field(..., description="Document content")
    status: str = Field(..., description="Current document status")

class DocumentList(BaseModel):
    documents: List[Document] = Field(..., description="List of documents")

class DiagramRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of conversation messages")

class DiagramResponse(BaseModel):
    uml_diagrams: str = Field(..., description="Generated UML diagrams in PlantUML format")
    message: str = Field(..., description="Status message")

class DocumentRequest(BaseModel):
    chat_name: str = Field(..., description="Name of the chat session")
    messages: List[Message] = Field(..., description="List of conversation messages")
    uml_diagrams: str = Field(..., description="UML diagrams in PlantUML format")

class DocumentResponse(BaseModel):
    file_path: str = Field(..., description="Path to the generated document")
    message: str = Field(..., description="Status message")

# Review Models
class ReviewHistoryEntry(BaseModel):
    review_id: str = Field(..., description="Review identifier")
    document_id: str = Field(..., description="Document identifier")
    created_at: datetime = Field(..., description="Review creation timestamp")
    reviewer: str = Field(..., description="Username of the reviewer")
    status: str = Field(..., description="Review status")
    metrics: Dict = Field(..., description="Review metrics summary")

class ReviewHistory(BaseModel):
    reviews: List[ReviewHistoryEntry] = Field(..., description="List of review history entries")

class ReviewRequest(BaseModel):
    document_content: str = Field(..., description="Content of the SRS document")
    uml_diagrams: str = Field(..., description="UML diagrams to review")

class ReviewMetrics(BaseModel):
    total_issues: int = Field(..., description="Total number of issues found")
    critical_issues: int = Field(..., description="Number of critical issues")
    major_issues: int = Field(..., description="Number of major issues")
    minor_issues: int = Field(..., description="Number of minor issues")
    quality_score: float = Field(..., description="Overall quality score")

class ReviewResponse(BaseModel):
    review_report: Dict = Field(..., description="Detailed review report")
    metrics: ReviewMetrics = Field(..., description="Review metrics")
    message: str = Field(..., description="Status message")

# Converter Models
class ConverterRequest(BaseModel):
    plantuml_code: str = Field(..., description="PlantUML code to convert")
    diagram_type: DiagramType = Field(..., description="Type of diagram")

class ConverterResponse(BaseModel):
    json_data: Dict = Field(..., description="Converted JSON representation")
    message: str = Field(..., description="Status message")

# Modification Models
class ModificationHistoryEntry(BaseModel):
    modification_id: str = Field(..., description="Modification identifier")
    document_id: str = Field(..., description="Document identifier")
    created_at: datetime = Field(..., description="Modification timestamp")
    user: str = Field(..., description="Username who made the modification")
    type: str = Field(..., description="Type of modification")
    status: str = Field(..., description="Modification status")
    changes_summary: Dict = Field(..., description="Summary of changes made")

class ModificationHistory(BaseModel):
    modifications: List[ModificationHistoryEntry] = Field(..., description="List of modification history entries")

class ModificationRequest(BaseModel):
    request: str = Field(..., description="Change request description")
    current_content: Dict = Field(..., description="Current document and diagram content")

class ModificationSuggestion(BaseModel):
    section: str = Field(..., description="Section to modify")
    changes: str = Field(..., description="Detailed description of changes")
    reason: str = Field(..., description="Justification for the change")

class ModificationImpact(BaseModel):
    srs_changes: List[str] = Field(default_factory=list, description="Affected SRS sections")
    diagram_changes: List[str] = Field(default_factory=list, description="Affected diagrams")
    dependencies: List[str] = Field(default_factory=list, description="Change dependencies")
    risk_level: str = Field(..., description="Risk level of changes")

class ModificationAnalysisResponse(BaseModel):
    suggestions: Dict[str, List[ModificationSuggestion]] = Field(..., description="Suggested modifications")
    impact_analysis: ModificationImpact = Field(..., description="Impact analysis of changes")
    history: Dict = Field(..., description="Modification history")
    message: str = Field(..., description="Status message")

class ModificationApplyRequest(BaseModel):
    suggestions: Dict = Field(..., description="Approved modification suggestions")
    current_content: Dict = Field(..., description="Current content to modify")

class ModificationApplyResponse(BaseModel):
    updated_content: Dict = Field(..., description="Modified content")
    history: Dict = Field(..., description="Modification history")
    message: str = Field(..., description="Status message")

# Common Response Models
class DeleteResponse(BaseModel):
    message: str = Field(..., description="Status message")
    id: str = Field(..., description="ID of the deleted resource") 