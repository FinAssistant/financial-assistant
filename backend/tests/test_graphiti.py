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

async def add_episode(conversation: str, group_id: str) -> tuple:
    # Add an episode
    add_episode_tool = next((t for t in graphiti_tools if t.name == "add_memory"), None)
    if not add_episode_tool:
        raise Exception("Add episode tool not found")

    try:
        # generate random UUID
        uuid = uuid4()
        print(f"Storing memory for {group_id}: {conversation}")
        
        import time
        creation_start = time.time()
        response = await add_episode_tool.ainvoke({
            "name": "Customer Conversation",
            "episode_body": conversation,
            "source": "message",
            "source_description": f"integration test {uuid}",
            "group_id": group_id,
        })
        creation_end = time.time()
        creation_time = creation_end - creation_start
        
        print(f"✅ Stored memory for {group_id} in {creation_time:.2f}s: {response}")
        return uuid, creation_start
    except Exception as e:
        print(f"❌ Error storing episode for {group_id}: {e}")
        return None, None

async def search_memory_nodes(query: str, group_id: str) -> int:
    """Search memory nodes and return count of found nodes"""
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
        print(f"Search results for '{query}' in {group_id}: {results}")

        result_dict = json.loads(results)
        node_count = len(result_dict["nodes"])
        if node_count == 0:
            print(f"❌ Missing memories for '{query}' in {group_id}")
        else:
            print(f"✅ Found {node_count} memories for '{query}' in {group_id}")
        return node_count
    except Exception as e:
        print(f"Error searching memory nodes for '{query}' in {group_id}: {e}")
        return 0

async def wait_for_episode(group_id: str, episode_uuid: str, creation_start_time: float, timeout: int = 300) -> tuple:
    """Wait for an episode to be available in Graphiti, returns (found, ready_time)"""
    get_episodes_tool = next((t for t in graphiti_tools if t.name == "get_episodes"), None)
    if not get_episodes_tool:
        raise Exception("Get episodes tool not found")

    import time
    wait_start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - wait_start_time) < timeout:
        try:
            episodes = await get_episodes_tool.ainvoke({
                "group_id": group_id
            })
            
            ep_dict = None
            # if episodes is a list
            if isinstance(episodes, list):
                for ep in episodes:
                    ep_dict = json.loads(ep)
                    if f"{episode_uuid}" in ep_dict["source_description"]:
                        ready_time = time.time()
                        time_to_ready = ready_time - creation_start_time
                        print(f"✅ Episode {episode_uuid} found after {time_to_ready:.2f}s")
                        return True, time_to_ready

            # if it's a string and once parsed has a source_description field
            if isinstance(episodes, str):
                d = json.loads(episodes)
                if "source_description" in d and f"{episode_uuid}" in d["source_description"]:
                    ready_time = time.time()
                    time_to_ready = ready_time - creation_start_time
                    print(f"✅ Episode {episode_uuid} found after {time_to_ready:.2f}s")
                    return True, time_to_ready

            elapsed = asyncio.get_event_loop().time() - wait_start_time
            print(f"⏳ Episode {episode_uuid} not found yet (waited {elapsed:.1f}s)...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error retrieving episodes for {group_id}: {e}")
            await asyncio.sleep(10)
    
    print(f"❌ Timeout waiting for episode {episode_uuid}")
    return False, timeout

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
    
    group_id = "graphiti_poc"
    
    # Define multiple financial scenarios as episodes
    episodes_data = [
        "I want to save $50,000 for a house down payment within 2 years. My current savings goal is $2,000 per month.",
        "I'm planning for retirement and need to contribute $500 monthly to my 401k. I'm 35 years old and want to retire at 65.",
        "I have $15,000 in credit card debt at 18% interest. I want to pay it off as quickly as possible by allocating $800 per month.",
        "I'm considering investing in index funds. I have $10,000 to start and plan to invest $300 monthly for long-term growth.",
        "I need an emergency fund of $20,000. Currently I have $5,000 and want to save an additional $500 monthly until I reach my goal."
    ]
    
    # Create all episodes and track timing
    episode_data = []  # Store (uuid, creation_start_time) tuples
    print(f"\n=== Creating {len(episodes_data)} episodes ===")
    for i, conversation in enumerate(episodes_data, 1):
        print(f"\nCreating episode {i}/{len(episodes_data)}")
        result = await add_episode(conversation, group_id)
        if result[0] and result[1]:  # episode_uuid and creation_start
            episode_data.append(result)
    
    # Wait for all episodes to be available and track timing
    print(f"\n=== Waiting for all {len(episode_data)} episodes to be available ===")
    all_episodes_ready = True
    timing_results = []
    
    for episode_uuid, creation_start in episode_data:
        found, time_to_ready = await wait_for_episode(group_id, str(episode_uuid), creation_start)
        timing_results.append((episode_uuid, time_to_ready, found))
        if not found:
            all_episodes_ready = False
            print(f"❌ Episode {episode_uuid} not found within timeout")
    
    if not all_episodes_ready:
        print("❌ Not all episodes were created successfully")
        return False
    
    # Show timing summary
    print(f"\n=== Episode Creation & Readiness Timing Summary ===")
    total_ready_time = sum(time_to_ready for _, time_to_ready, found in timing_results if found)
    successful_episodes = sum(1 for _, _, found in timing_results if found)
    
    if successful_episodes > 0:
        avg_ready_time = total_ready_time / successful_episodes
        min_ready_time = min(time_to_ready for _, time_to_ready, found in timing_results if found)
        max_ready_time = max(time_to_ready for _, time_to_ready, found in timing_results if found)
        
        print(f"✅ All {successful_episodes} episodes created successfully")
        print(f"📊 Average time to ready: {avg_ready_time:.2f}s")
        print(f"📊 Fastest episode ready: {min_ready_time:.2f}s")
        print(f"📊 Slowest episode ready: {max_ready_time:.2f}s")
        print(f"📊 Total time for all episodes: {total_ready_time:.2f}s")
    else:
        print("❌ No episodes were successfully created")
    
    # Test different queries and assert results
    queries_and_expected = [
        ("house", "Should find house down payment episode"),
        ("retirement", "Should find retirement planning episode"),
        ("debt", "Should find credit card debt episode"),
        ("investment", "Should find index fund investment episode"),
        ("emergency", "Should find emergency fund episode"),
        ("savings", "Should find multiple episodes about saving"),
        ("monthly", "Should find episodes with monthly contributions"),
        ("$500", "Should find episodes mentioning $500 amounts"),
    ]
    
    print(f"\n=== Testing {len(queries_and_expected)} different queries ===")
    test_results = []
    for query, description in queries_and_expected:
        print(f"\nTesting query: '{query}' - {description}")
        node_count = await search_memory_nodes(query, group_id)
        test_results.append((query, node_count, node_count > 0))
        
        # Assert that we get results for each query
        assert node_count > 0, f"Query '{query}' should return results but found {node_count} nodes"
    
    # Summary of test results
    print(f"\n=== Test Summary ===")
    print(f"Total episodes created: {len(episode_data)}")
    print(f"Total queries tested: {len(test_results)}")
    
    successful_queries = sum(1 for _, _, success in test_results if success)
    print(f"Successful queries: {successful_queries}/{len(test_results)}")
    
    for query, count, success in test_results:
        status = "✅" if success else "❌"
        print(f"{status} '{query}': {count} nodes found")
    
    print(f"\n🎉 All tests passed! Graphiti successfully stored and retrieved financial context.")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)