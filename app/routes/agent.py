import logging
import openai
import random
from typing import List, Any
from agents import (
    Agent, FunctionTool, Runner, function_tool, set_default_openai_api, 
    set_default_openai_client, set_tracing_disabled,
    TResponseInputItem, MessageOutputItem, ToolCallItem, 
    ToolCallOutputItem, ItemHelpers, ModelSettings, OpenAIChatCompletionsModel, OpenAIResponsesModel
)

import json
from openai.types.responses.easy_input_message_param import EasyInputMessageParam
from fastapi import APIRouter
from pydantic import BaseModel
from openai import AsyncOpenAI

router = APIRouter()

# ============================================================
# API SETUP & CONFIGURATION
# ============================================================

client = AsyncOpenAI(
    # base_url="http://localhost:11434/v1",
    base_url="http://localhost:3000/v1",
    api_key="ollama"
)

gpt_oss = OpenAIResponsesModel(
    model="gpt-oss:20b",
    openai_client=client,
)

WEATHER_CONDITIONS = ["sunny", "partly cloudy", "cloudy", "light rain", "clear"]
TEMPERATURE_RANGE = [65, 68, 70, 72, 75, 78, 80, 82, 85]

class ROLES:
    user = "user"
    assistant = "assistant"
    system = "system"
    developer = "developer"

set_tracing_disabled(True)
set_default_openai_client(client)
set_default_openai_api("responses")

# ============================================================
# CONTEXT MODEL
# ============================================================
class WeatherAgentContext(BaseModel):
    weather_requested: bool = False

# ============================================================
# WEATHER TOOL DEFINITION
# ============================================================
@function_tool(
        strict_mode=True, 
        is_enabled=True,
)
async def get_weather(location: str) -> str:
    """Get the current weather in a given location"""
    temp = random.choice(TEMPERATURE_RANGE)
    condition = random.choice(WEATHER_CONDITIONS)
    return f"The current weather in {location} is {condition} with a temperature of {temp}°F."

# ============================================================
# WEATHER AGENT
# ============================================================
weather_agent = Agent[WeatherAgentContext](
    name="Weather Assistant",
    instructions=(
        "You are a helpful weather assistant. "
        "Use the get_weather tool to provide current weather information "
        "when users ask about weather conditions in any location. "
    ),
    tools=[get_weather],
    model=gpt_oss,
    model_settings=ModelSettings(
        tool_choice="auto",
        reasoning=None,  # Disable reasoning
    ),
)

for tool in weather_agent.tools:
    if isinstance(tool, FunctionTool):
        print(tool.name)
        print(tool.description)
        print(json.dumps(tool.params_json_schema, indent=2))
        print()


async def test_weather():
    query = "What's the weather like in San Francisco?"
    current_agent: Agent[WeatherAgentContext] = weather_agent
    context = WeatherAgentContext()
    
    result = await Runner.run(
        starting_agent=current_agent,
        input=query,
        context=context,
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Final output: {result.final_output}")
    return result


# ============================================================
# API ENDPOINT
# ============================================================
# @router.post("/chat")
# async def process_weather_query(query: str = None):
#     if not query:
#         query = "What's the weather like in San Francisco?"

#     current_agent: Agent[WeatherAgentContext] = weather_agent

#     # input_messages: TResponseInputItem = [
#     #     {"role": ROLES.user, "content": query}
#     # ]

#     # input_messages = query
    

#     context = WeatherAgentContext()

#     try:
#         result = await Runner.run(
#             starting_agent=current_agent,
#             input=query,
#             context=context,
#         )
            
#         return {
#             "success": True,
#             "response": result.final_output,  # final text output
#             "weather_requested": context.weather_requested,
#         }
#     except openai.BadRequestError:
#         pass

    # --------
    
    # try:
    #     result = await Runner.run(
    #         current_agent,
    #         query, 
    #         context=context,
    #     )
        
    #     return {
    #         "success": True,
    #         "response": result.final_output,  # final text output
    #         "weather_requested": context.weather_requested,
    #     }
    # except openai.BadRequestError as e:
    #     return {
    #         "success": False,
    #         "error": f"OpenAI API error: {str(e)}"
    #     }
    # except Exception as e:
    #     return {
    #         "success": False,
    #         "error": f"Unexpected error: {str(e)}"
    #     }


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def _log_agent_activity(items: List[Any]) -> None:
    """Log agent processing steps for debugging."""
    for item in items:
        agent_name = item.agent.name
        
        if isinstance(item, MessageOutputItem):
            print(f"{agent_name}: {ItemHelpers.text_message_output(item)}")
        elif isinstance(item, ToolCallOutputItem):
            print(f"{agent_name}: Retrieved weather data: {item.output}")
        elif isinstance(item, ToolCallItem):
            print(f"{agent_name}: Fetching weather information...")
        # Add other item types as needed


# class DebugAsyncOpenAI(AsyncOpenAI):
#     async def responses_create(self, **kwargs):
#         print("=== DEBUGGING: Raw OpenAI API Call ===")
#         print(f"Full kwargs: {json.dumps(kwargs, indent=2, default=str)}")
#         print("=== END DEBUG ===")
#         return await super().responses.create(**kwargs)
    
#     @property
#     def responses(self):
#         original_responses = super().responses
        
#         class DebugResponses:
#             def __init__(self, responses):
#                 self._responses = responses
            
#             async def create(self, *args, **kwargs):
#                 print("=== DEBUGGING: Raw OpenAI API Call ===")
#                 print(f"Args: {args}")
#                 print(f"Full kwargs: {json.dumps(kwargs, indent=2, default=str)}")
#                 print("=== END DEBUG ===")
#                 return await self._responses.create(*args, **kwargs)
    
#         return DebugResponses(original_responses)



# import json
# import random
# from typing import List, Any, Optional
# from agents import Agent, set_default_openai_api, set_default_openai_client, set_tracing_disabled
# from fastapi import APIRouter
# from pydantic import BaseModel
# from openai import AsyncOpenAI


# router = APIRouter()


# # ============================================================
# # API SETUP & CONFIGURATION
# # ============================================================

# openai_client = AsyncOpenAI(
#     api_key="ollama",
#     base_url="http://localhost:3000/v1",
# )

# # Weather-related configuration
# WEATHER_CONDITIONS = ["sunny", "partly cloudy", "cloudy", "light rain", "clear"]
# TEMPERATURE_RANGE = [65, 68, 70, 72, 75, 78, 80, 82, 85]

# set_tracing_disabled(True)
# set_default_openai_client(openai_client)
# set_default_openai_api("responses")

# # ============================================================
# # CONTEXT MODEL
# # ============================================================

# class WeatherAgentContext(BaseModel):
#     """Tracks whether weather information has been requested in this session."""
#     weather_requested: bool = False


# # ============================================================
# # WEATHER TOOL DEFINITION - DIRECT FORMAT
# # ============================================================

# tools = [
#     {
#         "type": "function",
#         "name": "get_weather",
#         "description": "Get the current weather in a given location",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "location": {
#                     "type": "string",
#                     "description": "The city and state, e.g. San Francisco, CA"
#                 }
#             },
#             "required": ["location"],
#             "additionalProperties": False,
#         },
#         "strict": True,
#     },
# ]


# # ============================================================
# # WEATHER FUNCTION
# # ============================================================

# async def get_weather(location: str) -> str:
#     """
#     Retrieve current weather for a location.
#     Note: Currently returns simulated data.
#     """
#     temp = random.choice(TEMPERATURE_RANGE)
#     condition = random.choice(WEATHER_CONDITIONS)
    
#     return f"The current weather in {location} is {condition} with a temperature of {temp}°F."

# # ============================================================
# # AGENT
# # ============================================================


# weather_agent = Agent[WeatherAgentContext](
#     name="Weather Assistant",
#     instructions=(
#         "You are a helpful weather assistant. "
#         "Use the get_weather tool to provide current weather information "
#         "when users ask about weather conditions in any location."
#     ),
#     tools=tools,
#     model="gpt-oss:20b",
# )

# # ============================================================
# # API ENDPOINTS
# # ============================================================

# @router.post("/chat")
# async def process_weather_query(query: str = None):
#     """Process a weather query using the Responses API directly"""
#     current_agent = Agent
    
    
#     if not query:
#         query = "What's the weather like in San Francisco?"
    
#     context = WeatherAgentContext()
    
#     response = await openai_client.responses.create(
#         model="gpt-oss:20b",
#         instructions=(
#             "You are a helpful weather assistant. "
#             "Use the get_weather tool to provide current weather information "
#             "when users ask about weather conditions in any location."
#         ),
#         input=[
#             {
#                 "role": "user",
#                 "content": query,
#             }
#         ],
#         tools=tools,
#         tool_choice="auto",
#     )
    
#     # Check if there's a function call in the output
#     for item in response.output:
#         if item.type == "function_call" and item.name == "get_weather":
#             # Parse the arguments and call the function
#             args = json.loads(item.arguments)
#             location = args.get("location", "Unknown")
#             weather_info = await get_weather(location)
#             context.weather_requested = True
            
#             return {
#                 "success": True,
#                 "response": weather_info,
#                 "weather_requested": context.weather_requested,
#                 "raw_response": response,
#             }
    
#     return {
#         "success": True,
#         "response": response,
#         "weather_requested": context.weather_requested,
#     }

# # ============================================================
# # SERVICE REGISTRY - Thread-safe service storage
# # ============================================================

# class ServiceRegistry:
#     """
#     Registry to hold service dependencies for the current request.
#     This avoids storing services in the agent context.
#     """

#     @classmethod
#     def set_services(cls, meeting_service, current_user):
#         """Set services for the current request."""
#         cls._meeting_service = meeting_service
#         cls._current_user = current_user
    
#     @classmethod
#     def get_meeting_service(cls):
#         """Get the meeting service for the current request."""
#         if cls._meeting_service is None:
#             raise RuntimeError("Meeting service not initialized")
#         return cls._meeting_service
    
#     @classmethod
#     def get_current_user(cls):
#         """Get the current user for the current request."""
#         if cls._current_user is None:
#             raise RuntimeError("Current user not initialized")
#         return cls._current_user
    
#     @classmethod
#     def clear(cls):
#         """Clear services after request completion."""
#         cls._meeting_service = None
#         cls._current_user = None

# # ============================================================
# # AGENT CONTEXT - Clean, minimal state tracking
# # ============================================================

# class MeetingAgentContext(BaseModel):
#     """Tracks conversation state without service dependencies."""
#     meeting_requested: bool = False
#     user_id: str = ""

# # ============================================================
# # CORE MEETING FUNCTIONALITY - Uses Service Registry
# # ============================================================

# @function_tool
# async def get_meeting(
#     context: RunContextWrapper[MeetingAgentContext],
# ) -> list[MeetingPublic]:
#     """Get all meetings for the authenticated user"""
#     try:
#         # Get services from registry instead of context
#         meeting_service = ServiceRegistry.get_meeting_service()
#         current_user = ServiceRegistry.get_current_user()
        
#         meetings, _ = meeting_service.get_user_meetings(
#             user_id=str(current_user.id),
#             skip=0,
#             limit=100,
#             include_as_participant=True,
#         )
        
#         # Mark that meeting was requested
#         context.context.meeting_requested = True
#         print(f"Meetings retrieved: {len(meetings)}")
#         return meetings
        
#     except Exception as e:
#         raise Exception(f"Failed to retrieve meetings: {str(e)}")

# # ============================================================
# # LIFECYCLE HOOKS - Track agent activity
# # ============================================================

# class MeetingAgentHooks(AgentHooks):
#     """Monitors agent lifecycle events."""
    
#     async def on_tool_end(
#         self,
#         context: RunContextWrapper[MeetingAgentContext],
#         agent: Agent,
#         tool,
#         result: str
#     ) -> None:
#         """Track successful tool execution."""
#         # Meeting requested flag is set inside the tool itself
#         pass
    
#     # Optional: Implement other hooks as needed
#     async def on_start(self, context, agent) -> None:
#         pass
    
#     async def on_end(self, context, agent, output) -> None:
#         pass
    
#     async def on_tool_start(self, context, agent, tool) -> None:
#         pass

# # ============================================================
# # AGENT DEFINITIONS
# # ============================================================

# summary_agent = Agent[MeetingAgentContext](
#     name="Summary Agent",
#     handoff_description="A helpful agent that summarizes meeting information.",
#     instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
#     You are a Summary agent. You receive meeting data from the Meeting agent and create a helpful summary.
#     Use the following routine to support the user.

#     # Routine
#     1. Summarize the meeting information that was retrieved by the Meeting agent.
#     2. Provide insights and key details about the meetings in a user-friendly format.
#     3. Answer the user's original question based on the meeting data.
#     4. Transfer back to the Triage Agent to handle any follow-up questions.
#     """,
#     model="gpt-oss:20b",
#     hooks=MeetingAgentHooks(),
# )

# meeting_agent = Agent[MeetingAgentContext](
#     name="Meeting Agent",
#     handoff_description="A helpful meeting agent that retrieves meeting information.",
#     instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
#     You are a Meeting agent. If you are speaking to a user, you probably were transferred to from the triage agent.
#     Use the following routine to support the user.

#     # Routine
#     1. Get the details of the meeting, using the meeting ID.
#     2. Then, you handle whether the meeting is found or not. If found, present the details to the user.
#     3. Finally, transfer to the Summary Agent to create a summary of the meeting and your decision.""",
#     tools=[get_meeting],
#     handoffs=[summary_agent],
#     model="gpt-oss:20b",
#     hooks=MeetingAgentHooks(),
# )

# triage_agent = Agent[MeetingAgentContext](
#     name="Triage Agent",
#     handoff_description="A triage agent that can delegate a user's request to the appropriate agent.",
#     instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
#     You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents.""",
#     handoffs=[meeting_agent],
#     model="gpt-oss:20b",
#     hooks=MeetingAgentHooks(),
# )

# # Set up strict linear handoff chain: triage -> meeting -> summary -> triage
# summary_agent.handoffs = [triage_agent]

# # ============================================================
# # API ENDPOINTS
# # ============================================================

# @router.post("/chat")
# async def process_meeting_query(
#     current_user: CurrentUser,
#     meeting_service: MeetingServiceDep,
#     query: str = None
# ):
#     """
#     Process a meeting-related query.
#     Services are stored in the registry, not in context.
#     """
    
#     # Set services in registry for this request
#     ServiceRegistry.set_services(meeting_service, current_user)
    
#     if not query:
#         query = "Get all meetings with status 'approved'"
    
#     input_messages: TResponseInputItem = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "input_text", "text": query}
#             ],
#             "type": "message",
#         }
#     ]

#     # Create minimal context (no service dependencies)
#     context = MeetingAgentContext(
#         user_id=str(current_user.id),
#     )
    
#     # Run the agent
#     current_agent: Agent[MeetingAgentContext] = triage_agent


#     await openai_client.responses.create(
#         model="gpt-oss:20b",
#         messages=input_messages,
#         response_format="json",
#     )

#     result = await Runner.run(
#         current_agent, 
#         input_messages, 
#         context=context
#     )

#     _log_agent_activity_default(result.new_items)
    
#     return {
#         "success": True,
#         "response": result.final_output,
#         "meeting_requested": context.meeting_requested,
#     }

# # ============================================================
# # UTILITY FUNCTIONS
# # ============================================================

# def _log_agent_activity_default(items: List[Any]) -> None:
#     """Log agent processing steps for debugging."""
#     for item in items:
#         agent_name = item.agent.name
        
#         if isinstance(item, MessageOutputItem):
#             print(f"{agent_name}: {ItemHelpers.text_message_output(item)}")
#         elif isinstance(item, ToolCallOutputItem):
#             print(f"{agent_name}: Retrieved data: {item.output}")
#         elif isinstance(item, ToolCallItem):
#             print(f"{agent_name}: Fetching information...")
#         # Add other item types as needed
     
