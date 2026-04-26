"""Introspection SDK instrumentation for LangChain/LangGraph model calls."""

from __future__ import annotations

import atexit
import os
from functools import lru_cache
from typing import Any

SERVICE_NAME = "executive-ai-assistant"


@lru_cache(maxsize=1)
def _callback_handler():
    from introspection_sdk import IntrospectionCallbackHandler

    handler = IntrospectionCallbackHandler(service_name=SERVICE_NAME)
    atexit.register(handler.shutdown)
    return handler


def get_introspection_config() -> dict[str, list[Any]]:
    """Return LangChain config that enables tracing when credentials exist."""
    if not os.getenv("INTROSPECTION_TOKEN"):
        return {}

    return {"callbacks": [_callback_handler()]}
