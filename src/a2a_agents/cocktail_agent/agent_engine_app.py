"""Agent Engine entrypoint for Cocktail Agent.

This module is referenced by AgentEngineConfig(entrypoint_module=..., entrypoint_object="agent_engine")
when deploying via the SDK with source_packages.
"""

from vertexai.preview.reasoning_engines import A2aAgent

from a2a_agents.cocktail_agent.agent_executor import CocktailAgentExecutor
from a2a_agents.cocktail_agent.cocktail_agent_card import cocktail_agent_card

agent_engine = A2aAgent(
    agent_card=cocktail_agent_card,
    agent_executor_builder=CocktailAgentExecutor,
)
