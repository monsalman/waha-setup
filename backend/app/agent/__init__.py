"""Agent plug-in. The control backend calls the agent ONLY when a number is in
agent mode. Replace the stub with a real agent later (see INTERFACE.md)."""
from ..config import config
from .stub import stub_agent

_REGISTRY = {"stub": stub_agent}


def get_agent():
    impl = config.AGENT_IMPL or "stub"
    agent = _REGISTRY.get(impl)
    if not agent:
        raise RuntimeError(f"Unknown AGENT_IMPL={impl!r}. Known: {list(_REGISTRY)}")
    if not hasattr(agent, "reply"):
        raise RuntimeError(f"Agent {impl!r} does not implement async reply(ctx)")
    return agent


async def agent_reply(ctx: dict) -> str | None:
    return await get_agent().reply(ctx)
