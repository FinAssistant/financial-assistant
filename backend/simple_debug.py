#!/usr/bin/env python3
"""Simple LangGraph checkpoint reader using AsyncSqliteSaver"""

import asyncio
import json
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def dump_checkpoints():
    """Read checkpoints using AsyncSqliteSaver"""
    import os

    db_path = os.path.abspath("data/langgraph_checkpoints.db")
    print(f"Connecting to: {db_path}")

    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        print("=== All Checkpoints ===")

        count = 0
        async for checkpoint in checkpointer.alist(None, limit=5):
            count += 1
            print(f"\n--- Checkpoint {count} ---")
            print(
                f"Thread ID: {checkpoint.config.get('configurable', {}).get('thread_id', 'unknown')}"
            )
            print(f"Checkpoint ID: {checkpoint.checkpoint.get('id', 'unknown')}")
            # Clean up the messages for better readability
            channel_values = checkpoint.checkpoint.get("channel_values", {})
            if "messages" in channel_values:
                cleaned_messages = []
                for msg in channel_values["messages"]:
                    msg_str = str(msg)

                    # Extract content
                    content = ""
                    if "content='" in msg_str:
                        start = msg_str.find("content='") + 9
                        end = msg_str.find("'", start)
                        content = msg_str[start:end]
                    elif 'content="' in msg_str:
                        start = msg_str.find('content="') + 9
                        end = msg_str.find('"', start)
                        content = msg_str[start:end]

                    # Determine agent/type
                    if "additional_kwargs={}" in msg_str:
                        # Human message
                        cleaned_messages.append(f"[Human] {content}")
                    elif "'agent': '" in msg_str:
                        # AI message with agent info
                        agent_start = msg_str.find("'agent': '") + 10
                        agent_end = msg_str.find("'", agent_start)
                        agent = msg_str[agent_start:agent_end].title()
                        cleaned_messages.append(f"[{agent}] {content}")
                    elif "additional_kwargs" in msg_str and content:
                        # AI message without agent (probably orchestrator)
                        cleaned_messages.append(f"[Orchestrator] {content}")
                    else:
                        # Fallback - show truncated raw message
                        cleaned_messages.append(f"[Unknown] {msg_str[:100]}...")

            print(f"Messages:")
            for i, msg in enumerate(cleaned_messages):
                print(f"  {i}. {msg}")

            # Show other state information
            print(f"\nGraph State:")
            for key, value in channel_values.items():
                if key != "messages":
                    print(f"  {key}: {json.dumps(value, indent=4, default=str)}")

            print(f"\nMetadata: {checkpoint.metadata}")
            print("-" * 40)


if __name__ == "__main__":
    asyncio.run(dump_checkpoints())
