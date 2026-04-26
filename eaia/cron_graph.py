from typing import TypedDict
from eaia.conversation import conversation_id_for_email
from eaia.gmail import fetch_group_emails
from langgraph_sdk import get_client
import httpx
from langgraph.graph import StateGraph, START, END
from eaia.main.config import get_config
from eaia.instrumentation import get_introspection_config

client = get_client()


class JobKickoff(TypedDict):
    minutes_since: int


async def main(state: JobKickoff, config):
    minutes_since: int = state["minutes_since"]
    email = get_config(config)["email"]

    async for email in fetch_group_emails(email, minutes_since=minutes_since):
        thread_id = conversation_id_for_email(email)
        try:
            thread_info = await client.threads.get(thread_id)
        except httpx.HTTPStatusError as e:
            if "user_respond" in email:
                continue
            if e.response.status_code == 404:
                thread_info = await client.threads.create(thread_id=thread_id)
            else:
                raise e
        if "user_respond" in email:
            await client.threads.update_state(thread_id, None, as_node="__end__")
            continue
        recent_email = thread_info["metadata"].get("email_id")
        if recent_email == email["id"]:
            break
        await client.threads.update(
            thread_id,
            metadata={"email_id": email["id"], "gmail_thread_id": email["thread_id"]},
        )

        await client.runs.create(
            thread_id,
            "main",
            input={"email": email},
            multitask_strategy="rollback",
        )


graph = StateGraph(JobKickoff)
graph.add_node(main)
graph.add_edge(START, "main")
graph.add_edge("main", END)
graph = graph.compile().with_config(get_introspection_config())
