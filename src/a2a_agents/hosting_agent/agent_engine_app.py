"""Agent Engine entrypoint for Hosting Agent.

This module is referenced by AgentEngineConfig(entrypoint_module=..., entrypoint_object="agent_engine")
when deploying via the SDK with source_packages.
"""

from vertexai.preview.reasoning_engines import A2aAgent

from a2a_agents.hosting_agent.hosting_agent_card import hosting_agent_card
from a2a_agents.hosting_agent.langgraph_orchestrator_agent_executor import HostingAgentExecutor

agent_engine = A2aAgent(
    agent_card=hosting_agent_card,
    agent_executor_builder=HostingAgentExecutor,
)
