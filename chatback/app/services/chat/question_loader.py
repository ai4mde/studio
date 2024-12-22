import os
from typing import Dict, List, Tuple
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def load_interview_questions() -> Tuple[Dict[int, str], Dict[int, List[str]]]:
    """Load interview sections and questions from markdown file."""
    try:
        questions_path = os.path.join(settings.CHATBACK_DATA_PATH, "interviews", "interview_questions.md")
        
        # Check if file exists
        if not os.path.exists(questions_path):
            logger.error(f"Interview questions file not found at: {questions_path}")
            raise FileNotFoundError(
                f"Required file 'interview_questions.md' not found. "
                f"Please ensure it exists at {questions_path}"
            )

        # Check if file is readable
        if not os.access(questions_path, os.R_OK):
            logger.error(f"Interview questions file is not readable: {questions_path}")
            raise PermissionError(
                f"Cannot read interview questions file. "
                f"Please check file permissions at {questions_path}"
            )

        with open(questions_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode interview questions file: {str(e)}")
                raise ValueError(
                    f"Interview questions file has invalid encoding. "
                    f"Please ensure it is UTF-8 encoded."
                )

        sections = {}
        questions = {}
        current_section = None
        current_questions = []
        section_index = 1

        if not content.strip():
            logger.error("Interview questions file is empty")
            raise ValueError("Interview questions file is empty")

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('##'):
                if current_section is not None:
                    questions[section_index] = current_questions
                    section_index += 1
                current_questions = []
                current_section = line[2:].strip()
                sections[section_index] = current_section
            elif line[0].isdigit():
                question = line[line.find(' ') + 1:].strip()
                current_questions.append(question)

        # Add the last section
        if current_questions:
            questions[section_index] = current_questions

        # Validate loaded content
        if not sections:
            logger.error("No sections found in interview questions file")
            raise ValueError("No sections found in interview questions file")

        if not questions:
            logger.error("No questions found in interview questions file")
            raise ValueError("No questions found in interview questions file")

        logger.info(f"Successfully loaded {len(sections)} sections with {sum(len(q) for q in questions.values())} questions")
        return sections, questions

    except Exception as e:
        logger.error(f"Error loading interview questions: {str(e)}")
        # Add context to the error
        if isinstance(e, (FileNotFoundError, PermissionError, ValueError)):
            raise
        raise RuntimeError(f"Failed to load interview questions: {str(e)}") from e

def count_total_questions(questions: Dict[int, List[str]]) -> int:
    """Count total number of questions across all sections."""
    return sum(len(questions[section]) for section in questions)