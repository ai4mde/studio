import pytest
import asyncio
from typing import Dict, List

from app.agents.interview import InterviewAgent
from app.agents.document import SRSDocumentAgent
from app.agents.diagram import DiagramAgent
from app.agents.review import ReviewAgent
from app.agents.converter import UMLConverterAgent
from app.agents.modification import ModificationAgent

# Test data
TEST_SESSION_ID = "test_session_123"
TEST_USERNAME = "test_user"
TEST_INTERVIEW_MESSAGES = [
    {"type": "human", "content": "I need a web application for managing student records."},
    {"type": "ai", "content": "Could you tell me more about the key features needed?"},
    {"type": "human", "content": "We need to store student details, grades, and attendance."}
]

TEST_UML_DIAGRAMS = """
### Class Diagram
@startuml
class Student {
    +id: String
    +name: String
    +email: String
    +addGrade(subject: String, grade: Float)
    +updateAttendance(date: Date, present: Boolean)
}
@enduml

### Use Case Diagram
@startuml
actor Teacher
usecase "Manage Students" as MS
usecase "Record Grades" as RG
usecase "Track Attendance" as TA
Teacher --> MS
Teacher --> RG
Teacher --> TA
@enduml
"""

@pytest.mark.asyncio
async def test_interview_agent():
    """Test InterviewAgent functionality."""
    agent = InterviewAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test initial message
    response = await agent.process_message("Hello")
    assert response is not None
    assert isinstance(response, str)
    assert "my name is" in response.lower()
    
    # Test next question
    response = await agent.process_message("next")
    assert response is not None
    assert isinstance(response, str)
    assert "?" in response  # Should contain a question

@pytest.mark.asyncio
async def test_diagram_agent():
    """Test DiagramAgent functionality."""
    agent = DiagramAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test UML generation
    result = await agent.generate_uml_diagrams(TEST_INTERVIEW_MESSAGES)
    assert result is not None
    assert isinstance(result, dict)
    assert "uml_diagrams" in result
    assert "@startuml" in result["uml_diagrams"]
    assert "@enduml" in result["uml_diagrams"]

@pytest.mark.asyncio
async def test_document_agent():
    """Test SRSDocumentAgent functionality."""
    agent = SRSDocumentAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test document generation
    result = await agent.generate_srs_document(
        chat_name="test_chat",
        messages=TEST_INTERVIEW_MESSAGES,
        uml_diagrams=TEST_UML_DIAGRAMS
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "file_path" in result
    assert "message" in result

@pytest.mark.asyncio
async def test_review_agent():
    """Test ReviewAgent functionality."""
    agent = ReviewAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test document review
    result = await agent.review_document(
        document_content="# Software Requirements Specification\n## Introduction\nThis document...",
        uml_diagrams=TEST_UML_DIAGRAMS
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "review_report" in result
    assert "message" in result
    assert "metrics" in result

@pytest.mark.asyncio
async def test_converter_agent():
    """Test UMLConverterAgent functionality."""
    agent = UMLConverterAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test UML to JSON conversion
    result = await agent.convert_uml_to_json(
        plantuml_code=TEST_UML_DIAGRAMS,
        diagram_type="class"
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "json_data" in result
    assert "message" in result

@pytest.mark.asyncio
async def test_modification_agent():
    """Test ModificationAgent functionality."""
    agent = ModificationAgent(TEST_SESSION_ID, TEST_USERNAME)
    
    # Test content for modifications
    current_content = {
        "srs": "# Software Requirements Specification\n## Introduction\nThis document...",
        "diagrams": {
            "class": TEST_UML_DIAGRAMS
        }
    }
    
    # Test change request analysis
    analysis_result = await agent.analyze_change_request(
        request="Add a new field 'grade' to the Student class",
        current_content=current_content
    )
    assert analysis_result is not None
    assert isinstance(analysis_result, dict)
    assert "suggestions" in analysis_result
    assert "impact_analysis" in analysis_result
    
    # Test applying changes
    apply_result = await agent.apply_changes(
        suggestions=analysis_result["suggestions"],
        current_content=current_content
    )
    assert apply_result is not None
    assert isinstance(apply_result, dict)
    assert "updated_content" in apply_result
    assert "history" in apply_result

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"])) 