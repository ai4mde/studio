from typing import Dict, List, Optional
import logging
import json
import os
from datetime import datetime
from string import Template
from fastapi import HTTPException
from redis.exceptions import TimeoutError
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import load_interview_questions, get_time_based_greeting

logger = logging.getLogger(__name__)

class InterviewAgent(BaseAgent):
    """Agent responsible for conducting structured interviews."""
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_SMITH_NAME,
            model_name=settings.AGENT_SMITH_MODEL,
            temperature=settings.AGENT_SMITH_TEMPERATURE,
            redis_prefix="interview"
        )
        
        # Get Redis client from message history
        self.redis_client = self.message_history.redis_client
        self.state_key = f"interview_state_{session_id}"
        
        # Load sections and questions
        self.sections, self.questions = load_interview_questions()
        self.total_questions = sum(len(questions) for questions in self.questions.values())
        
        # Get user info
        self.user_info = {
            "name": username,
            "id": session_id
        }
        
        # Load or initialize state
        state = self.redis_client.get(self.state_key)
        if state:
            state = json.loads(state)
            self.current_section = state.get('section', 1)
            self.current_question_index = state.get('question', 0)
            logger.info(f"Loaded state: section={self.current_section}, "
                      f"question={self.current_question_index}")
        else:
            self.current_section = 1
            self.current_question_index = 0
            self._save_state()
            logger.info("Initialized new state")
        
        self.max_history_messages = 6  # Keep last 6 messages (3 exchanges)
        
        # Setup file paths
        self.user_dir = os.path.join(settings.CHATBOT_DATA_PATH, username, "chats")
        self.template_path = os.path.join(settings.TEMPLATES_PATH, "interview_answered_template.md")
        os.makedirs(self.user_dir, exist_ok=True)
        
        logger.info(f"Initialized user directory: {self.user_dir}")

    def _save_state(self) -> None:
        """Save current interview state to Redis."""
        try:
            progress = self.calculate_progress()
            state = {
                'section': self.current_section,
                'question': self.current_question_index,
                'progress': progress
            }
            self.redis_client.set(self.state_key, json.dumps(state))
            logger.info(f"Saved state with progress {progress}%")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def _get_truncated_messages(self) -> List[BaseMessage]:
        """Get truncated message history to prevent context overflow."""
        messages = self.message_history.messages
        
        # Always keep system message if it exists
        system_message = next((m for m in messages if m.type == 'system'), None)
        
        # Get recent messages
        recent_messages = messages[-self.max_history_messages:]
        
        # Combine with current context
        context_messages = []
        if system_message:
            context_messages.append(system_message)
            
        # Add current section and question context
        context_messages.append({
            "role": "system",
            "content": f"""Current interview status:
            - Section: {self.sections[self.current_section]}
            - Question: {self.questions[self.current_section][self.current_question_index]}
            """
        })
        
        # Add recent messages
        context_messages.extend(recent_messages)
        
        return context_messages

    def _track_message_progress(self, content: str) -> None:
        """Track progress when user says 'next'."""
        if content.lower() in ['next', 'continue', 'proceed']:
            # Get current section's questions
            current_section_questions = self.questions.get(self.current_section, [])
            
            # Check if we have more questions in current section
            if self.current_question_index < len(current_section_questions) - 1:
                self.current_question_index += 1
            else:
                # Move to next section if available
                if self.current_section < len(self.sections):
                    self.current_section += 1
                    self.current_question_index = 0
            
            self._save_state()
            logger.info(f"Progress updated: section={self.current_section}, "
                       f"question={self.current_question_index}, "
                       f"progress={self.calculate_progress()}%")

    def calculate_progress(self) -> float:
        """Calculate interview progress as a percentage."""
        try:
            # If interview is complete, return 100%
            if self.is_interview_complete():
                return 100.0
            
            # Calculate based on current section and question
            completed_sections = self.current_section - 1
            completed_questions = sum(len(self.questions[i]) for i in range(1, completed_sections + 1))
            if self.current_section <= len(self.sections):
                completed_questions += self.current_question_index
            
            progress = (completed_questions / self.total_questions) * 100
            return round(progress, 1)
            
        except Exception as e:
            logger.error(f"Error calculating progress: {str(e)}")
            return 0.0

    def is_interview_complete(self) -> bool:
        """Check if the interview is complete."""
        try:
            # Check if we're past the last section
            if self.current_section > len(self.sections):
                return True
                
            # If we're on the last section, check if we've completed all questions
            if self.current_section == len(self.sections):
                return self.current_question_index >= len(self.questions[self.current_section])
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking interview completion: {str(e)}")
            return False

    async def get_chat_name(self) -> str:
        """Get a sanitized chat name for the file."""
        try:
            # Try to get user's name from Redis
            user_info_key = f"interview:user_info_{self.session_id}"
            user_info = self.message_history.get(user_info_key)
            
            if user_info:
                user_data = json.loads(user_info)
                chat_name = f"interview_{user_data.get('name', 'user')}"
            else:
                chat_name = f"interview_session_{self.session_id}"
                
            # Sanitize filename
            chat_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in chat_name)
            return chat_name
            
        except Exception as e:
            logger.error(f"Error getting chat name: {str(e)}")
            return f"interview_session_{self.session_id}"

    async def save_interview_responses(self, chat_name: str) -> str:
        """Save interview responses to a markdown file."""
        try:
            logger.info(f"Attempting to save interview responses for {chat_name}")
            
            # Ensure user directory exists
            if not os.path.exists(self.user_dir):
                logger.info(f"Creating user directory: {self.user_dir}")
                os.makedirs(self.user_dir, exist_ok=True)
            
            # Check if template exists and is readable
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"Template file not found at: {self.template_path}")
            if not os.access(self.template_path, os.R_OK):
                raise PermissionError(f"Cannot read template file at: {self.template_path}")
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{chat_name}_{timestamp}.md"
            filepath = os.path.join(self.user_dir, filename)
            
            # Read and validate template
            with open(self.template_path, 'r', encoding='utf-8') as template_file:
                template_content = template_file.read()
                if not template_content.strip():
                    raise ValueError("Template file is empty")
            
            # Get all responses from Redis
            responses = {}
            for section_id, questions in self.questions.items():
                for i, question in enumerate(questions):
                    question_key = f"interview:response_{self.session_id}_{section_id}_{i}"
                    response = self.message_history.get(question_key) or "No answer provided"
                    responses[f"section_{section_id}_q_{i}"] = response
            
            # Replace placeholders and save
            template = Template(template_content)
            filled_content = template.safe_substitute(responses)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(filled_content)
            
            logger.info(f"Interview responses saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving interview responses: {str(e)}")
            if isinstance(e, (FileNotFoundError, PermissionError, ValueError, IOError)):
                raise
            raise RuntimeError(f"Failed to save interview responses: {str(e)}") from e

    async def process_message(self, content: str) -> str:
        """Process a user message and return the agent's response."""
        try:
            logger.info(f"Processing message for session {self.session_id}")
            
            # Get existing messages
            messages = self.message_history.messages
            
            # First message handling
            if not messages:
                logger.info("Starting new interview session")
                greeting = get_time_based_greeting()
                user_name = self.user_info.get('name', '')
                name_part = f" {user_name}," if user_name else ","
                first_question = self.questions[self.current_section][self.current_question_index]
                
                intro = f"""{greeting}{name_part} my name is {self.agent_name}. I am a senior business analyst specializing in stakeholder interviews 
                and requirements gathering. I'll be conducting a structured interview to help understand your project needs 
                and requirements thoroughly. We'll go through several sections covering different aspects of your project.

                # Let's begin with our first question!\n\n**{first_question}**"""
                
                self.message_history.add_ai_message(intro)
                return intro
            
            # Handle 'next' command
            if content.lower() in ['next', 'continue', 'proceed']:
                current_section_questions = self.questions[self.current_section]
                next_question = None

                # Check if there are more questions in current section
                if self.current_question_index < len(current_section_questions) - 1:
                    self.current_question_index += 1
                    next_question = current_section_questions[self.current_question_index]
                    response = f"\n\n**{next_question}**"
                else:
                    # Move to next section if available
                    if self.current_section < len(self.sections):
                        self.current_section += 1
                        self.current_question_index = 0
                        next_section = self.sections[self.current_section]
                        next_question = self.questions[self.current_section][0]
                        response = f"\n\nMoving on to section: **{next_section}**\n\n**{next_question}**"
                    else:
                        response = "Thank you for your time and detailed responses. This concludes our requirements gathering session. Goodbye!"

                # Save state and return response
                self._save_state()
                self.message_history.add_ai_message(response)
                return response
            
            # Add user message to history
            self.message_history.add_user_message(content)
            
            # Track progress when user says next
            self._track_message_progress(content)
            
            # Create chain with updated prompt and truncated history
            progress = self.calculate_progress()
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, a senior business analyst conducting a structured interview.

                IMPORTANT RULES:
                1. You must STRICTLY follow the predefined questions list
                2. Never create new questions or deviate from the script
                3. Only ask for clarification about the current question if needed
                4. Wait for the interviewer to explicitly tell you to proceed
                
                Current interview status:
                - Section: {self.sections[self.current_section]} ({progress}% complete)
                - Current question: {self.questions[self.current_section][self.current_question_index]}
                
                Your response should:
                1. Acknowledge the user's answer professionally
                2. If the answer is unclear, ask for clarification about the CURRENT question only
                3. If the answer is clear, add this exact text on a new line:
                   "\nWhen you're ready, please type '**next**' to proceed to the following question."
                4. NEVER introduce a new question unless the user types 'next', 'continue', or 'proceed'"""),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            
            # Get AI response
            ai_message = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={
                    "input": content,
                    "history": self._get_truncated_messages()
                }
            )
            
            # Add AI response to history
            self.message_history.add_ai_message(ai_message)
            
            logger.info(f"Message processed successfully. Section: {self.current_section}, Question: {self.current_question_index}")

            # If interview is complete, save responses
            if self.is_interview_complete():
                try:
                    chat_name = await self.get_chat_name()
                    await self.save_interview_responses(chat_name)
                except Exception as e:
                    logger.error(f"Failed to save interview responses: {str(e)}")
                
                user_name = self.user_info.get('name', '')
                name_part = f" {user_name}" if user_name else ""
                
                completion_message = f"""Thank you{name_part} for completing this comprehensive interview! 🎉

I've successfully saved all your valuable responses and insights. Based on our discussion, I will now proceed with generating a detailed software requirements document that captures:

- Your project objectives and goals
- Key functional requirements
- Technical specifications
- Project constraints and considerations

The document will serve as a solid foundation for your software development project. You'll be able to review it shortly.

Is there anything else you'd like to add before we proceed with the document generation?"""
                
                return completion_message

            return ai_message

        except TimeoutError as e:
            logger.error(f"Timeout error in interview process: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=504,
                detail="Request timed out. Please try again."
            )
        except Exception as e:
            logger.error(f"Error in interview process: {str(e)}", exc_info=True)
            raise 