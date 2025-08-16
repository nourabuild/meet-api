"""Agent Service
==============
Provides a singleton AI agent that can open/close sessions per user and interact
with existing APIs for meeting, calendar, user, and follow operations.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional
from weakref import WeakValueDictionary

# Import agents components - these will be available when openai-agents is properly installed
try:
    from agents import (
        Agent,
        AsyncOpenAI,
        OpenAIChatCompletionsModel,
        Runner,
        function_tool,
        set_tracing_disabled,
    )
    # Disable tracing for cleaner output
    set_tracing_disabled(True)
    AGENTS_AVAILABLE = True
except ImportError:
    # Fallback when agents package is not available
    AGENTS_AVAILABLE = False
    Agent = None
    AsyncOpenAI = None
    OpenAIChatCompletionsModel = None
    Runner = None
    function_tool = None
    set_tracing_disabled = None

from app.services.user.user_service import UserService
from app.services.meeting.meeting_service import MeetingService
from app.services.calendar.calendar_service import CalendarService
from app.services.follow.follow_service import FollowService
from app.utils.models import User

logger = logging.getLogger(__name__)


class AgentSession:
    """Represents an active agent session for a specific user."""
    
    def __init__(self, user_id: uuid.UUID, user: User, services: Dict[str, Any]):
        self.user_id = user_id
        self.user = user
        self.services = services
        self.runner: Optional[Runner] = None
        self.created_at = asyncio.get_event_loop().time()
        self.last_activity = self.created_at
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = asyncio.get_event_loop().time()
    
    def is_expired(self, timeout: float = 3600) -> bool:
        """Check if session has expired (default 1 hour)."""
        current_time = asyncio.get_event_loop().time()
        return (current_time - self.last_activity) > timeout
    
    async def close(self) -> None:
        """Close the agent session and clean up resources."""
        if self.runner:
            # Close the runner if it has cleanup methods
            logger.info(f"Closing agent session for user {self.user_id}")
        self.runner = None


class AgentService:
    """
    Singleton AI agent service that manages user sessions and provides
    AI-powered assistance with access to existing API functionality.
    """
    
    _instance: Optional['AgentService'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        user_service: UserService,
        meeting_service: MeetingService,
        calendar_service: CalendarService,
        follow_service: FollowService,
    ):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        # Initialize basic attributes
        self.user_service = user_service
        self.meeting_service = meeting_service
        self.calendar_service = calendar_service
        self.follow_service = follow_service
        self.active_sessions: WeakValueDictionary[uuid.UUID, AgentSession] = WeakValueDictionary()
        
        if not AGENTS_AVAILABLE:
            logger.warning("OpenAI Agents SDK not available. Agent functionality disabled.")
            self.openai_client = None
            self.agent = None
            self._initialized = True
            return
        
        # Initialize OpenAI client for Ollama
        self.openai_client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",  # Ollama endpoint
            api_key="ollama"  # Ollama doesn't require a real API key
        )
        
        # Create the agent with tools
        self.agent = self._create_agent()
        
        self._initialized = True
        logger.info("AgentService singleton initialized")
    
    def _create_agent(self) -> Agent:
        """Create the AI agent with tools for API interactions."""
        
        @function_tool
        async def get_user_profile(user_id: str) -> str:
            """Get user profile information by user ID."""
            try:
                user_uuid = uuid.UUID(user_id)
                user = self.user_service.get_user_by_id(user_uuid)
                if user:
                    return f"User: {user.full_name} (@{user.account}), Email: {user.email}"
                return "User not found"
            except Exception as e:
                return f"Error retrieving user: {str(e)}"
        
        @function_tool
        async def search_users(query: str, limit: int = 10) -> str:
            """Search for users by name, account, or email."""
            try:
                users_result = self.user_service.search_users(query, skip=0, limit=limit)
                if users_result.count > 0:
                    user_list = []
                    for user in users_result.data:
                        user_list.append(f"- {user.full_name} (@{user.account})")
                    return f"Found {users_result.count} users:\n" + "\n".join(user_list)
                return "No users found matching the search query"
            except Exception as e:
                return f"Error searching users: {str(e)}"
        
        @function_tool
        async def get_my_meetings(user_id: str, limit: int = 10) -> str:
            """Get current user's meetings."""
            try:
                user_uuid = uuid.UUID(user_id)
                meetings = self.meeting_service.get_user_meetings(user_uuid, skip=0, limit=limit)
                if meetings.count > 0:
                    meeting_list = []
                    for meeting in meetings.data:
                        meeting_list.append(
                            f"- {meeting.title} ({meeting.status}) - {meeting.start_time}"
                        )
                    return f"Your {meetings.count} meetings:\n" + "\n".join(meeting_list)
                return "No meetings found"
            except Exception as e:
                return f"Error retrieving meetings: {str(e)}"
        
        @function_tool
        async def get_follow_stats(user_id: str) -> str:
            """Get user's follow statistics."""
            try:
                user_uuid = uuid.UUID(user_id)
                stats = self.follow_service.get_follow_stats(user_uuid)
                return f"Follow stats - Following: {stats.following_count}, Followers: {stats.followers_count}"
            except Exception as e:
                return f"Error retrieving follow stats: {str(e)}"
        
        # Create the agent with clear role and instructions
        agent = Agent(
            model=OpenAIChatCompletionsModel(
                model="llama3.1:latest",  # or your preferred model
                api_client=self.openai_client
            ),
            instructions="""
            You are a helpful AI assistant for a meeting and calendar management platform.
            
            Your role is to help users with:
            - Managing their meetings and calendar
            - Finding and connecting with other users
            - Understanding their social connections (followers/following)
            - General assistance with platform features
            
            Key guidelines:
            - Be friendly, professional, and helpful
            - Use the available tools to provide accurate, up-to-date information
            - Always respect user privacy and data
            - Provide clear, actionable responses
            - If you cannot help with something, explain why and suggest alternatives
            
            You have access to tools that can:
            - Search for users
            - Get user profiles
            - Retrieve meeting information
            - Check follow statistics
            
            Always use tools when you need current data from the platform.
            """,
            tools=[get_user_profile, search_users, get_my_meetings, get_follow_stats],
        )
        
        return agent
    
    async def get_or_create_session(self, user: User) -> AgentSession:
        """Get existing session or create new one for user."""
        if not AGENTS_AVAILABLE:
            raise RuntimeError("OpenAI Agents SDK not available")
        
        async with self._lock:
            # Clean up expired sessions first
            await self._cleanup_expired_sessions()
            
            # Check for existing session
            if user.id in self.active_sessions:
                session = self.active_sessions[user.id]
                session.update_activity()
                return session
            
            # Create new session
            services = {
                'user': self.user_service,
                'meeting': self.meeting_service,
                'calendar': self.calendar_service,
                'follow': self.follow_service,
            }
            
            session = AgentSession(user.id, user, services)
            
            # Create runner for this session
            session.runner = Runner(agent=self.agent)
            
            self.active_sessions[user.id] = session
            logger.info(f"Created new agent session for user {user.id}")
            
            return session
    
    async def close_session(self, user_id: uuid.UUID) -> bool:
        """Close a specific user session."""
        async with self._lock:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                await session.close()
                del self.active_sessions[user_id]
                logger.info(f"Closed agent session for user {user_id}")
                return True
            return False
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        expired_sessions = []
        for user_id, session in self.active_sessions.items():
            if session.is_expired():
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            await self.close_session(user_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def chat(self, user: User, message: str) -> str:
        """
        Send a message to the agent and get a response.
        Automatically manages user sessions.
        """
        if not AGENTS_AVAILABLE:
            return "I apologize, but the AI agent feature is currently unavailable. The OpenAI Agents SDK needs to be installed and configured."
        
        try:
            # Get or create session for user
            session = await self.get_or_create_session(user)
            
            # Update activity
            session.update_activity()
            
            # Add user context to the message for tools
            contextual_message = f"[User ID: {user.id}] {message}"
            
            # Send message to agent
            response = await session.runner.run(contextual_message)
            
            # Extract the final message from response
            if hasattr(response, 'messages') and response.messages:
                return response.messages[-1].content
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error in agent chat for user {user.id}: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    async def get_active_session_count(self) -> int:
        """Get count of currently active sessions."""
        if not AGENTS_AVAILABLE:
            return 0
        await self._cleanup_expired_sessions()
        return len(self.active_sessions)
    
    async def get_session_info(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get information about a user's session."""
        if not AGENTS_AVAILABLE:
            return None
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            return {
                'user_id': str(session.user_id),
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_expired': session.is_expired(),
            }
        return None