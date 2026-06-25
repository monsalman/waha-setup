# Agent interface (contract for the real AI agent)

The control backend calls the agent ONLY when a number is in **agent** mode
(whitelisted). When a number is in **human** mode (taken over), the agent is
never called — staff reply manually instead.

A real agent is any object with an async `reply(ctx)` method returning the text
to send back (or `None`/`""` to stay silent once):

```python
class Agent:
    name: str

    async def reply(self, ctx: dict) -> str | None:
        """
        ctx keys:
          phone     normalized peer phone (digits only)
          chat_id   raw WAHA chatId, e.g. "6281234567890@c.us"
          body      inbound message text
          push_name optional sender push name
          session_id  WAHA message id
          history   list[{"direction": "in"|"out", "body": str}]
        """
```

## How to plug a real agent in
1. Implement it, e.g. in `app/agent/real.py` (LLM call + campus KB / RAG / MCP here).
2. Register it in `app/agent/__init__.py`:
   ```python
   from .real import real_agent
   _REGISTRY = {"stub": stub_agent, "real": real_agent}
   ```
3. Set `AGENT_IMPL=real` in `.env` and restart.

Nothing else in the backend (whitelist, handoff, dashboard) changes.
