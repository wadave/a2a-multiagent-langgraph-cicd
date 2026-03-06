"""Agent Engine entrypoint for Weather Agent.

This module is referenced by AgentEngineConfig(entrypoint_module=..., entrypoint_object="agent_engine")
when deploying via the SDK with source_packages.
"""

from vertexai.preview.reasoning_engines import A2aAgent

from a2a_agents.weather_agent.agent_executor import WeatherAgentExecutor
from a2a_agents.weather_agent.weather_agent_card import weather_agent_card

agent_engine = A2aAgent(
    agent_card=weather_agent_card,
    agent_executor_builder=WeatherAgentExecutor,
)
