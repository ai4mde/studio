from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.core.config import settings
from typing import List, Dict, Optional
import logging
import json
from redis.exceptions import TimeoutError, ConnectionError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
import time
from openai import APIConnectionError
from langchain_core.runnables import RunnableConfig
from fastapi import HTTPException
from .question_loader import load_interview_questions
from datetime import datetime
import pytz
from langchain_core.messages import BaseMessage
import os
from string import Template
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)

class InterviewAgent:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing InterviewAgent for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Setup Redis client first
            redis_url = (
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                f"?socket_timeout={settings.REDIS_TIMEOUT}"
                f"&socket_connect_timeout={settings.REDIS_TIMEOUT}"
            )
            retry = Retry(ExponentialBackoff(), settings.REDIS_RETRY_ATTEMPTS)
            
            # Initialize Redis client
            self.message_history = RedisChatMessageHistory(
                session_id=f"interview_{session_id}",
                url=redis_url,
                key_prefix="interview:",
                ttl=settings.REDIS_DATA_TTL
            )
            
            # Get Redis client from message history
            self.redis_client = self.message_history.redis_client
            
            # Get user's group info from Redis
            user_info = self._get_user_info()
            self.group_name = user_info.get('group_name', 'default')
            
            # Where to save the interviews - now using group directory
            self.group_dir = os.path.join(settings.CHATBOT_DATA_PATH, self.group_name, "interviews")
            self.template_path = os.path.join(settings.TEMPLATES_PATH, "interview_answered_template.md")
            os.makedirs(self.group_dir, exist_ok=True)
            
            logger.info(f"Initialized group directory: {self.group_dir}")
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_SMITH_NAME
            
            # Load sections and questions from markdown file
            self.sections, self.questions = load_interview_questions()
            
            # Calculate total questions
            self.total_questions = sum(len(questions) for questions in self.questions.values())
            
            # Get user info from Redis (now redis_client is initialized)
            self.user_info = {
                "name": username,
                "id": session_id
            }
            
            # Initialize LLM with GPT-4 and retry settings
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_SMITH_MODEL,
                temperature=settings.AGENT_SMITH_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=5,  # Increase retries
                http_client=httpx.Client(
                    timeout=httpx.Timeout(
                        connect=10.0,    # Connection timeout
                        read=30.0,       # Read timeout
                        write=30.0,      # Write timeout
                        pool=5.0         # Pool timeout
                    ),
                    limits=httpx.Limits(
                        max_keepalive_connections=5,
                        max_connections=10,
                        keepalive_expiry=30.0
                    )
                )
            )
            
            # Setup Redis memory with retry logic and timeouts
            redis_url = (
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                f"?socket_timeout={settings.REDIS_SOCKET_TIMEOUT}"
                f"&socket_connect_timeout={settings.REDIS_CONNECT_TIMEOUT}"
            )
            retry = Retry(ExponentialBackoff(), settings.REDIS_RETRY_ATTEMPTS)
            
            self.message_history = RedisChatMessageHistory(
                session_id=f"interview_{session_id}",
                url=redis_url,
                key_prefix="interview:",
                ttl=settings.REDIS_DATA_TTL
            )
            
            # Initialize Redis client with retry logic
            self.redis_client = self.message_history.redis_client
            self.state_key = f"interview_state_{session_id}"
            
            # Try to load existing state
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
            
            logger.info("InterviewAgent initialized successfully")
            
            self.max_history_messages = 6  # Keep last 6 messages (3 exchanges)
            
            logger.info(f"Initialized user directory: {self.group_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize InterviewAgent: {str(e)}", exc_info=True)
            raise

    def _save_state(self):
        """Save current interview state to Redis"""
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

    def _load_state(self):
        """Load interview state from Redis"""
        try:
            state = self.redis_client.get(self.state_key)
            if state:
                state = json.loads(state)
                self.current_section = state.get('section', 1)
                self.current_question_index = state.get('question', 0)
                progress = state.get('progress', 0)
                logger.info(f"Loaded state with progress {progress}%")
                return progress
            logger.warning("No state found, using defaults")
            return self.calculate_progress()  # Calculate fresh if no state
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return self.calculate_progress()  # Calculate fresh on error

    def _get_introduction(self) -> str:
        """Get the introduction message with the first question"""
        intro = f"""Hello, I am {self.agent_name}, a senior business analyst specializing in stakeholder interviews 
        and requirements gathering. I'll be conducting a structured interview to help understand your project needs 
        and requirements thoroughly. We'll go through several sections covering different aspects of your project.

        Let's begin with our first question!\n\n"""
        first_question = f"**{self.questions[1][0]}**"
        return intro + first_question

    def _get_user_info(self) -> dict:
        """Get user info including group from Redis."""
        try:
            user_info_key = f"user_info:{self.username}"
            user_info = self.redis_client.get(user_info_key)
            if user_info:
                return json.loads(user_info)
            logger.warning(f"No user info found for user {self.username}")
            return {'group_name': 'default'}
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {'group_name': 'default'}

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
            
            total_questions = sum(len(questions) for questions in self.questions.values())
            progress = (completed_questions / total_questions) * 100
            
            return round(progress, 1)
            
        except Exception as e:
            logger.error(f"Error calculating progress: {str(e)}")
            return 0.0

    def _track_message_progress(self, content: str) -> None:
        """Track progress when user says 'next'"""
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

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(
            (httpx.ConnectError, APIConnectionError)
        )
    )
    async def _call_llm_with_retry(self, chain, input_data):
        try:
            return await chain.ainvoke(input_data)
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    async def process_message(self, content: str) -> str:
        try:
            logger.info(f"Processing message for session {self.session_id}")
            
            # Get existing messages
            messages = self.message_history.messages
            
            # First message handling
            if not messages:
                logger.info("Starting new interview session")
                
                # Get time-appropriate greeting and first question
                current_hour = datetime.now(pytz.UTC).hour
                if current_hour < 12:
                    greeting = "Good morning"
                elif current_hour < 17:
                    greeting = "Good afternoon"
                else:
                    greeting = "Good evening"
                
                user_name = self.user_info.get('name', '')
                name_part = f" {user_name}," if user_name else ","
                
                # Get first question from current section
                first_question = self.questions[self.current_section][self.current_question_index]
                
                intro = f"""{greeting}{name_part} my name is {self.agent_name}. I am a senior business analyst specializing in stakeholder interviews and requirements gathering. I'll be conducting a structured interview to help understand your project needs and requirements thoroughly. We'll go through several sections covering different aspects of your project.\n\n### Let's begin with our first question!\n\n**{first_question}**"""
                
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
                        response = f"\n\n### Moving on to section: {next_section}\n\n**{next_question}**"
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

            chain = prompt | self.llm
            response = await self._call_llm_with_retry(
                chain,
                input_data={
                    "input": content,
                    "history": self._get_truncated_messages()
                }
            )

            ai_message = response.content
            
            # Only move to next question if explicitly instructed
            if content.lower().strip() in ["next", "next question", "continue", "proceed"]:
                prev_section = self.current_section
                prev_question = self.current_question_index
                
                if self.current_question_index < len(self.questions[self.current_section]) - 1:
                    self.current_question_index += 1
                    next_question = f"\n\n**{self.questions[self.current_section][self.current_question_index]}**"
                    ai_message = f"Moving to the next question:{next_question}"
                elif self.current_section < len(self.sections):
                    self.current_section += 1
                    self.current_question_index = 0
                    next_question = f"\n\nMoving on to section: **{self.sections[self.current_section]}**\n\n**{self.questions[self.current_section][0]}**"
                    ai_message = next_question
                else:
                    ai_message = "Thank you for your time and detailed responses. This concludes our requirements gathering session. Goodbye!"
                
                # Save the updated state
                self._save_state()
                
                logger.info(f"Moving from section {prev_section}, question {prev_question} to section {self.current_section}, question {self.current_question_index}")

            # Add AI response to history
            self.message_history.add_ai_message(ai_message)
            
            logger.info(f"Message processed successfully. Section: {self.current_section}, Question: {self.current_question_index}")

            # If interview is complete, save responses
            if self.is_interview_complete():
                try:
                    chat_name = await self.get_chat_name()
                    filepath = await self.save_interview_responses(chat_name)
                    logger.info(f"Interview responses saved to {filepath}")
                    
                    user_name = self.user_info.get('name', '')
                    name_part = f" {user_name}" if user_name else ""
                    
                    completion_message = f"""Thank you{name_part} for completing this comprehensive interview! 🎉

I've successfully saved all your valuable responses and insights to:
{filepath}

Based on our discussion, I will now proceed with generating a detailed software requirements document that captures:

- Your project objectives and goals
- Key functional requirements
- Technical specifications
- Project constraints and considerations

The document will serve as a solid foundation for your software development project. You'll be able to review it shortly.

Is there anything else you'd like to add before we proceed with the document generation?"""
                    
                    return completion_message

                except Exception as e:
                    logger.error(f"Failed to save interview responses: {str(e)}", exc_info=True)
                    return """Thank you for completing the interview! However, there was an issue saving your responses. 
                    Please contact support for assistance."""

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

    def get_interview_progress(self) -> Dict:
        """Return interview progress information"""
        return {
            "total_sections": len(self.sections),
            "current_section": self.current_section,
            "completed": self.current_section > len(self.sections)
        }

    async def save_interview_responses(self, chat_name: str) -> str:
        """Save interview responses to markdown files in group's chat directory."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            # Create chat-specific directory structure
            chat_dir = os.path.join(
                settings.CHATBOT_DATA_PATH,
                self.group_name,
                chat_name
            )
            os.makedirs(chat_dir, exist_ok=True)
            
            # Save chat history
            chat_filename = f"chat_history_{timestamp}.md"
            chat_filepath = os.path.join(chat_dir, chat_filename)
            
            # Format and save chat history
            chat_content = f"""# Interview Chat History
## {chat_name}

Date: {timestamp}
Interviewer: {self.username}
Group: {self.group_name}

## Messages

"""
            # Get all messages from history
            messages = self.message_history.messages
            
            # Format messages
            for msg in messages:
                msg_time = getattr(msg, 'created_at', datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                role = msg.type.upper() if hasattr(msg, 'type') else 'UNKNOWN'
                content = msg.content if hasattr(msg, 'content') else str(msg)
                chat_content += f"""### {role} - {msg_time}
{content}

"""
            
            # Save chat history
            with open(chat_filepath, 'w', encoding='utf-8') as f:
                f.write(chat_content)
                
            logger.info(f"Chat history saved to {chat_filepath}")
            
            return chat_filepath
            
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}", exc_info=True)
            raise

    async def get_chat_name(self) -> str:
        """Get a sanitized chat name for the file"""
        try:
            # Try to get user's name from Redis
            user_info_key = f"interview:user_info_{self.session_id}"
            user_info = self.message_history.get(user_info_key)
            
            if user_info:
                import json
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

    def is_interview_complete(self) -> bool:
        """
        Check if the interview is complete by verifying if we've gone through all sections
        and questions.
        
        Returns:
            bool: True if interview is complete, False otherwise
        """
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