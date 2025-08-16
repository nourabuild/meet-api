"""Agent Routes
=============
Handles AI agent chat interactions and session management.

Endpoints:
- POST /chat: Send a message to the AI agent and get a response.
- GET /session: Get current user's agent session information.
- DELETE /session: Close current user's agent session.
- GET /stats: Get agent service statistics (active sessions count).
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from app.utils.delegate import CurrentUser, AgentServiceDep
from app.utils.models import AgentRequest, AgentResponse, AgentSessionInfo, Message

router = APIRouter()


@router.post("/chat")
async def chat_with_agent(
    request: AgentRequest,
    current_user: CurrentUser,
    agent_service: AgentServiceDep,
) -> AgentResponse:
    """
    Send a message to the AI agent and receive a response.
    
    The agent has access to your profile information and can help with:
    - Managing meetings and calendar
    - Finding and connecting with users
    - Understanding your social connections
    - General platform assistance
    
    Sessions are automatically managed per user and expire after 1 hour of inactivity.
    """
    try:
        # Send message to agent and get response
        response_message = await agent_service.chat(current_user, request.message)
        
        # Get session info for metadata
        session_info = await agent_service.get_session_info(current_user.id)
        session_metadata = None
        if session_info:
            session_metadata = {
                "session_active": "true",
                "last_activity": str(session_info["last_activity"]),
            }
        
        return AgentResponse(
            message=response_message,
            session_info=session_metadata,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent service error: {str(e)}"
        )


@router.get("/session")
async def get_agent_session(
    current_user: CurrentUser,
    agent_service: AgentServiceDep,
) -> Optional[AgentSessionInfo]:
    """
    Get information about the current user's agent session.
    
    Returns session details if active, or null if no session exists.
    """
    try:
        session_info = await agent_service.get_session_info(current_user.id)
        
        if session_info:
            return AgentSessionInfo(**session_info)
        
        return None
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session info: {str(e)}"
        )


@router.delete("/session")
async def close_agent_session(
    current_user: CurrentUser,
    agent_service: AgentServiceDep,
) -> Message:
    """
    Close the current user's agent session.
    
    This will terminate the active session and free up resources.
    The next chat message will automatically create a new session.
    """
    try:
        success = await agent_service.close_session(current_user.id)
        
        if success:
            return Message(message="Agent session closed successfully")
        else:
            return Message(message="No active agent session found")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing session: {str(e)}"
        )


@router.get("/stats")
async def get_agent_stats(
    current_user: CurrentUser,  # noqa: ARG001
    agent_service: AgentServiceDep,
) -> dict[str, int]:
    """
    Get agent service statistics.
    
    Returns the number of currently active sessions.
    Useful for monitoring and administrative purposes.
    """
    try:
        active_sessions = await agent_service.get_active_session_count()
        
        return {
            "active_sessions": active_sessions,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent stats: {str(e)}"
        )