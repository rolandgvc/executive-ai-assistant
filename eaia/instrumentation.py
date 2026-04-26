"""Introspection SDK instrumentation for LangChain/LangGraph model calls."""

from __future__ import annotations

from introspection_sdk import IntrospectionCallbackHandler, IntrospectionClient

SERVICE_NAME = "executive-ai-assistant"

client = IntrospectionClient(service_name=SERVICE_NAME)
handler = IntrospectionCallbackHandler(service_name=SERVICE_NAME)

_configured = False


def _with_handler(callbacks):
    if callbacks is None:
        return [handler]
    if hasattr(callbacks, "handlers"):
        if not any(cb is handler for cb in callbacks.handlers):
            callbacks.add_handler(handler, inherit=True)
        return callbacks

    callbacks = list(callbacks)
    if not any(cb is handler for cb in callbacks):
        callbacks.append(handler)
    return callbacks


def configure() -> None:
    global _configured
    if _configured:
        return

    from langchain_core.callbacks.manager import CallbackManager

    original_configure = CallbackManager.configure

    def configure_with_introspection(*args, **kwargs):
        inheritable_callbacks = kwargs.get("inheritable_callbacks")
        if inheritable_callbacks is None and args:
            inheritable_callbacks = args[0]

        callbacks = _with_handler(inheritable_callbacks)

        if args:
            args = (callbacks, *args[1:])
        else:
            kwargs["inheritable_callbacks"] = callbacks

        return original_configure(*args, **kwargs)

    CallbackManager.configure = configure_with_introspection
    _configured = True


configure()
