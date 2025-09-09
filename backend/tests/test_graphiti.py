#!/usr/bin/env python3
"""
POC to test Graphit
"""

import asyncio
import json
from uuid import uuid4
from langchain_mcp_adapters.client import MultiServerMCPClient

# Global variable to store tools
graphiti_tools = None

async def initialize_mcp_tools(mcp_client):
    """Initialize MCP tools from Graphiti server"""
    global graphiti_tools
    try:
        graphiti_tools = await mcp_client.get_tools()
        print(f"Connected to Graphiti MCP server. Available tools:\n {[tool.name for tool in graphiti_tools]}")
    except Exception as e:
        print(f"Failed to connect to Graphiti MCP server: {e}")
        graphiti_tools = []

async def add_episode(conversation: str, group_id: str) -> dict:
    # Add an episode
    add_episode_tool = next((t for t in graphiti_tools if t.name == "add_memory"), None)
    if not add_episode_tool:
        raise Exception("Add episode tool not found")

    try:
        # generate random UUID
        uuid = uuid4()
        print(f"Storing memory for {group_id}: {conversation}")
        response = await add_episode_tool.ainvoke({
            "name": "Customer Conversation",
            "episode_body": conversation,
            "source": "message",
            "source_description": f"integration test {uuid}",
            "group_id": group_id,
        })
        print(f"✅ Stored memory for {group_id}: {response}")
        return uuid
    except Exception as e:
        print(f"❌ Error storing episode for {group_id}: {e}")

async def search_memory_nodes(query: str, group_id: str):
    search_nodes_tool = next((t for t in graphiti_tools if t.name == "search_memory_nodes"), None)
    if not search_nodes_tool:
        raise Exception("Search memory nodes tool not found")

    try:
        results = await search_nodes_tool.ainvoke({
                "query": query,
                "group_ids": [group_id],
                "max_nodes": 10,
                "center_node_uuid": None,
            })
        print(f"Search results for {group_id}: {results}")

        result_dict = json.loads(results)
        if len(result_dict["nodes"]) == 0:
            print(f"❌ Missing memories for {group_id}")
        else:
            print(f"✅ Found memories for {group_id}: {len(result_dict['nodes'])}")
    except Exception as e:
        print(f"Error searching memory nodes for {group_id}: {e}")

async def main():
    try:
        client = MultiServerMCPClient({
            "graphiti": {
                "transport": "sse",
                "url": "http://localhost:8080/sse"
            }
        })
        print("✅ MultiServerMCPClient initialized for Graphiti")
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        return False
    
    await initialize_mcp_tools(client)
    
    group_id = "graphiti_poc_1"
    
    conversation = "I want to save $50,000 for a house down payment within 2 years. My current savings goal is $2,000 per month."
    add_Response_uuid = await add_episode(conversation, group_id)

    # use the get_episodes tool to check that the latest episode has been added
    get_episodes_tool = next((t for t in graphiti_tools if t.name == "get_episodes"), None)
    if not get_episodes_tool:
        raise Exception("Get episodes tool not found")

    try:
        # loop until we find an episode with the same uuid as the add_response
        while True:
            episodes = await get_episodes_tool.ainvoke({
                "group_id": group_id
            })
            print(f"Retrieved episodes for {group_id}: {episodes}")

            ep_dict = None
            # if episodes is a list
            if isinstance(episodes, list):
                for ep in episodes:
                    ep_dict = json.loads(ep)
                    print(f"Episode: {ep_dict['name']} (source_description: {ep_dict['source_description']})")

            # if it's a string and once parse has a source_description field
            if isinstance(episodes, str):
                d = json.loads(episodes)
                if "source_description" in d:
                    ep_dict = d

            if ep_dict is not None and f"{add_Response_uuid}" in ep_dict["source_description"]:
                print(f"✅ Episode found: {add_Response_uuid}")
                break

            print(f"⏳ Episode (uuid: {add_Response_uuid}) not found yet, waiting...")
            await asyncio.sleep(10)
    except Exception as e:
        print(f"Error retrieving episodes for {group_id}: {e}")

    await search_memory_nodes("house", group_id)

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)