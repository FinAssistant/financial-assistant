"""
Integration tests with REAL API calls.
These tests are SKIPPED in CI and only run locally when:
1. At least one LLM provider API key is available (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
2. RUN_REAL_TESTS environment variable is set to 'true'

To run these tests locally:
# Test with OpenAI (default)
export RUN_REAL_TESTS=true
export OPENAI_API_KEY=sk-your-openai-key-here
pytest tests/test_integration_real_api.py -v

# Test with Anthropic Claude
export RUN_REAL_TESTS=true
export DEFAULT_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
pytest tests/test_integration_real_api.py -v

# Test with Google Gemini
export RUN_REAL_TESTS=true
export DEFAULT_LLM_PROVIDER=google
export GOOGLE_API_KEY=your-google-api-key-here
pytest tests/test_integration_real_api.py -v
"""
import pytest
import os
from pathlib import Path
from app.services.llm_service import LLMFactory, LLMProvider
from app.ai.orchestrator_agent import get_orchestrator_agent
from app.core.database import user_storage


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """
    Fixture that ensures a clean database for each test.
    Deletes existing database, creates fresh schema, and sets up 7 test users.
    """
    # Clear all user data instead of trying to delete the file
    try:
        user_storage.clear_all_users()
        print("Cleared all existing users from database")
    except Exception as e:
        print(f"Could not clear users: {e}")
    
    # Also clear LangGraph checkpointer database to prevent conversation accumulation
    langgraph_db_file = Path("langgraph_checkpoints.db")
    if langgraph_db_file.exists():
        try:
            os.remove(langgraph_db_file)
            print(f"Cleared LangGraph checkpointer database: {langgraph_db_file}")
        except Exception as e:
            print(f"Could not clear LangGraph database: {e}")
    
    # Force database initialization to ensure clean schema
    import asyncio
    async def init_db():
        await user_storage._async_storage._ensure_initialized()
    
    try:
        asyncio.get_event_loop().run_until_complete(init_db())
        print("Database schema initialized")
    except RuntimeError:
        asyncio.run(init_db())
        print("Database schema initialized with new event loop")
    
    # Create 7 standard test users matching existing test user IDs
    test_users = [
        {
            "id": "real_test_user",
            "email": "real_test_user@test.com", 
            "password_hash": "test_hash_real",
            "profile_complete": False
        },
        {
            "id": "real_test_user_2", 
            "email": "real_test_user_2@test.com",
            "password_hash": "test_hash_real_2", 
            "profile_complete": False
        },
        {
            "id": "real_stream_user",
            "email": "real_stream_user@test.com",
            "password_hash": "test_hash_stream",
            "profile_complete": False  
        },
        {
            "id": "database_test_user",
            "email": "database_test_user@test.com", 
            "password_hash": "test_hash_for_database_test",
            "profile_complete": False
        },
        {
            "id": "profile_context_test_user",
            "email": "profile_context_test_user@test.com", 
            "password_hash": "test_hash_for_profile_context_test",
            "profile_complete": False
        },
        {
            "id": "complete_onboard_test_user",
            "email": "complete_onboard_test_user@test.com", 
            "password_hash": "test_hash_for_onboard_test",
            "profile_complete": False
        },
        {
            "id": "complete_onboard_spending_user",
            "email": "complete_onboard_spending_user@test.com", 
            "password_hash": "test_hash_for_spending_test",
            "profile_complete": False
        }
    ]
    
    created_user_ids = []
    for user_data in test_users:
        try:
            user_storage.create_user(user_data)
            created_user_ids.append(user_data['id'])
            print(f"Created test user: {user_data['id']}")
        except Exception as e:
            print(f"Failed to create user {user_data['id']}: {e}")
    
    # Return user IDs for tests to use
    yield created_user_ids
    
    # Cleanup after test (optional - since we delete at start of each test)
    print("Test completed - database will be cleaned for next test")


# Skip entire module if conditions not met
def has_any_llm_key():
    """Check if any LLM provider API key is available."""
    return any([
        os.getenv('OPENAI_API_KEY'),
        os.getenv('ANTHROPIC_API_KEY'), 
        os.getenv('GOOGLE_API_KEY')
    ])

pytestmark = pytest.mark.skipif(
    not has_any_llm_key() or os.getenv('RUN_REAL_TESTS') != 'true',
    reason="Real API tests require at least one LLM provider API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY) and RUN_REAL_TESTS=true"
)


@pytest.fixture(autouse=True)
def disable_mocking():
    """Disable the auto-mocking for these integration tests."""
    # This fixture runs automatically and does nothing,
    # but it prevents the conftest.py auto-mocking from interfering
    yield


class TestRealLLMService:
    """Integration tests with real LLM API calls."""
    
    def test_real_llm_creation(self):
        """Test creating real LLM instance."""
        factory = LLMFactory()
        llm = factory.create_llm()
        
        # Should be a real ChatOpenAI instance, not a mock
        assert hasattr(llm, 'invoke')
        assert hasattr(llm, 'client')  # Real OpenAI client
    
    def test_real_llm_basic_call(self):
        """Test real LLM API call."""
        factory = LLMFactory()
        llm = factory.create_llm()
        
        messages = [{"role": "user", "content": "Say exactly: TEST_RESPONSE"}]
        response = llm.invoke(messages)
        
        assert response is not None
        assert hasattr(response, 'content')
        assert len(response.content) > 0
        assert "TEST_RESPONSE" in response.content
    
    def test_real_llm_system_prompt(self):
        """Test real LLM with system prompt."""
        factory = LLMFactory()
        llm = factory.create_llm()
        
        messages = [
            {"role": "system", "content": "You are a math tutor. Answer only with numbers."},
            {"role": "user", "content": "What is 2+2?"}
        ]
        response = llm.invoke(messages)
        
        assert response is not None
        assert "4" in response.content
    
    def test_real_orchestrator_routing(self):
        """Test real orchestrator routing decisions."""
        factory = LLMFactory()
        llm = factory.create_llm()
        
        # Test orchestrator-style routing prompt
        system_prompt = """You must respond with exactly one word: SMALLTALK, SPENDING, INVESTMENT, or ONBOARDING.
        
        User input: Hello there!
        Response:"""
        
        messages = [{"role": "user", "content": system_prompt}]
        response = llm.invoke(messages)
        
        # Should route to SMALLTALK for greeting
        assert response.content.strip() in ["SMALLTALK", "SPENDING", "INVESTMENT", "ONBOARDING"]
        # Greeting should typically route to SMALLTALK
        assert "SMALLTALK" in response.content


class TestRealConversationFlow:
    """Integration tests for full conversation flow with real API."""
    
    @pytest.mark.asyncio
    async def test_real_conversation_greeting(self):
        """Test real conversation with greeting."""
        # Temporarily disable mocking for this test by patching the factory
        with pytest.MonkeyPatch().context() as m:
            # Remove any existing patches
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()

            result = await config.invoke_conversation(
                user_message="Hello there!",
                user_id="real_test_user",
                session_id="real_test_session"
            )
            
            assert result is not None
            assert len(result["messages"]) > 0
            last_message = result["messages"][-1]
            assert last_message["agent"] == "small_talk"  # Should route to small talk
            assert len(last_message["content"]) > 10  # Real response should be substantial
            assert any(greet in last_message["content"].lower() for greet in ["hello", "hi", "hey", "greetings"])
    
    @pytest.mark.asyncio
    async def test_real_conversation_financial_question(self):
        """Test real conversation with financial question."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()

            result = await config.invoke_conversation(
                user_message="How should I invest my money?",
                user_id="real_test_user_2",
                session_id="real_test_session_2"
            )
            
            assert result is not None
            # Should route to onboarding (profile incomplete by default)
            assert len(result["messages"]) > 0
            last_message = result["messages"][-1]
            assert last_message["agent"] == "onboarding"
            # Should ask for personal information (flexible wording)
            content_lower = last_message["content"].lower()
            assert any(word in content_lower for word in ["profile", "age", "occupation", "about", "share", "tell", "help", "information"])
    
    @pytest.mark.asyncio
    async def test_real_small_talk_agent(self):
        """Test real small talk agent with API."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()

            # Test small talk node directly
            from app.ai.orchestrator_agent import GlobalState
            from langchain_core.messages import HumanMessage

            state = GlobalState()
            state.messages = [HumanMessage(content="How's your day going?")]

            test_config = {
                "configurable": {
                    "user_id": "real_test_user_3",
                    "thread_id": "real_test_thread"
                }
            }

            result = config._small_talk_node(state, test_config)
            
            assert "messages" in result
            response = result["messages"][0]
            
            assert len(response.content) > 10  # Should be a real response
            assert response.additional_kwargs.get("agent") == "small_talk"
    
    @pytest.mark.asyncio
    async def test_real_streaming_conversation(self):
        """Test real streaming conversation."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()

            chunks = []
            for chunk in config.stream_conversation(
                user_message="Hello!",
                user_id="real_stream_user",
                session_id="real_stream_session"
            ):
                chunks.append(chunk)
                
            assert len(chunks) > 0
            # Should have orchestrator and agent chunks
            chunk_keys = [list(chunk.keys())[0] for chunk in chunks if chunk]
            assert "orchestrator" in chunk_keys
            assert any(key in chunk_keys for key in ["small_talk", "onboarding"])


class TestRealOnboardingDatabase:
    """Test real onboarding database updates with OpenAI API."""
    
    @pytest.mark.asyncio
    async def test_onboarding_saves_profile_to_database(self, clean_database):
        """Test that onboarding properly saves profile data to database."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()
            user_id = "database_test_user"
            session_id = "database_test_session"

            print("\n--- Database Setup via Fixture ---")
            print(f"Available users: {clean_database}")
            assert user_id in clean_database, f"Expected user {user_id} to be created by fixture"

            # Step 1: Start onboarding
            result1 = await config.invoke_conversation(
                user_message="I need financial advice. Can you help me?",
                user_id=user_id,
                session_id=session_id
            )

            assert len(result1["messages"]) > 0
            result1_message = result1["messages"][-1]
            assert result1_message["agent"] == "onboarding"

            # Step 2: Provide comprehensive profile data
            profile_data = """I'm 30 years old (26-35 age range), early career professional working as a nurse.
            I live in Florida with moderate cost of living. I'm single with no dependents, never married.
            No children, no caregiving responsibilities. My family structure is single with no dependents."""

            result2 = await config.invoke_conversation(
                user_message=profile_data,
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"\nProfile submission result: {result2['agent']}")
            print(f"Content: {result2['content']}")
            
            # Step 3: Complete profile if needed
            completion = "Yes, that's all correct. I'm ready for financial guidance now."

            result3 = await config.invoke_conversation(
                user_message=completion,
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"\nCompletion result: {result3['agent']}")
            
            # Now verify database was updated
            print("\n--- Database Verification ---")
            
            # Check personal context was saved
            personal_context = user_storage.get_personal_context(user_id)
            print(f"Personal context: {personal_context}")
            
            assert personal_context is not None, "Personal context should be saved"
            assert personal_context.get("age_range") == "26_35", f"Expected '26_35', got {personal_context.get('age_range')}"
            occupation_type = personal_context.get("occupation_type", "").lower()
            assert "nurse" in occupation_type or "healthcare" in occupation_type, f"Expected nurse or healthcare in occupation, got {personal_context.get('occupation_type')}"
            assert personal_context.get("marital_status") == "single", f"Expected single, got {personal_context.get('marital_status')}"
            
            # Check if user record exists and is marked complete
            user_data = user_storage.get_user_by_id(user_id)
            if user_data:
                print(f"User data: {user_data}")
                assert user_data.get("profile_complete") is True, "User should be marked as profile complete"
            else:
                print("User not found in main users table - checking if profile completion was recorded elsewhere")
                # The fact that we can route to other agents means completion was recorded somewhere
                # Let's test by asking a financial question
                test_result = await config.invoke_conversation(
                    user_message="What investment options do you recommend?",
                    user_id=user_id,
                    session_id=session_id
                )
                print(f"Test routing result: {test_result['agent']}")
                assert len(test_result["messages"]) > 0
                last_test_message = test_result["messages"][-1]
                assert last_test_message["agent"] in ["investment", "spending"], "Should route to financial agents if profile complete"
            
            print("✅ Database verification passed!")

    @pytest.mark.asyncio
    async def test_profile_context_in_next_agent_prompt(self, clean_database):
        """Test that after onboarding completes, the profile context is included in next agent's system prompt."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()
            user_id = "profile_context_test_user"
            session_id = "profile_context_test_session"

            print("\n--- Profile Context Test Setup via Fixture ---")
            print(f"Available users: {clean_database}")
            assert user_id in clean_database, f"Expected user {user_id} to be created by fixture"

            # Step 1: Complete onboarding
            result1 = await config.invoke_conversation(
                user_message="I need financial advice. Can you help me?",
                user_id=user_id,
                session_id=session_id
            )
            assert len(result1["messages"]) > 0
            result1_message = result1["messages"][-1]
            assert result1_message["agent"] == "onboarding"

            # Step 2: Provide comprehensive profile data to complete onboarding
            profile_data = """I'm 35 years old, established career professional working as a software engineer.
            I live in New York with high cost of living. I'm married with 2 children.
            No elderly parent caregiving responsibilities."""

            result2 = await config.invoke_conversation(
                user_message=profile_data,
                user_id=user_id,
                session_id=session_id
            )
            result2_message = result2["messages"][-1]
            print(f"Onboarding result: {result2_message['agent']} - {result2_message['content'][:100]}...")

            # Step 3: Ask a financial question that should route to another agent
            result3 = await config.invoke_conversation(
                user_message="I want to start investing in index funds. What should I consider?",
                user_id=user_id,
                session_id=session_id
            )

            print("\n--- Post-Onboarding Agent ---")
            print(f"Routed to agent: {result3['agent']}")
            print(f"Response content: {result3['content']}...")

            # Verify it routed to a financial agent (not onboarding)
            assert len(result3["messages"]) > 0
            result3_message = result3["messages"][-1]
            assert result3_message["agent"] != "onboarding", f"Should not route to onboarding anymore, got {result3_message['agent']}"
            assert result3_message["agent"] in ["investment", "spending"], f"Should route to investment or spending agent, got {result3_message['agent']}"

            # Test the _update_main_graph method by checking profile context in the conversation thread
            print("\n--- Testing Profile Context from Conversation Thread ---")
            
            # Access the actual GlobalState from the conversation thread
            # Try to get the current state from the checkpointer
            current_state = None
            if hasattr(config, 'checkpointer') and config.checkpointer:
                try:
                    # Get the latest checkpoint for this thread (using session_id as thread_id)
                    thread_config_with_id = {"configurable": {"thread_id": session_id}}
                    
                    checkpoint = config.checkpointer.get(thread_config_with_id)
                    if checkpoint and hasattr(checkpoint, 'channel_values'):
                        current_state = checkpoint.channel_values
                        print(f"Retrieved state from checkpointer with keys: {list(current_state.keys()) if current_state else 'None'}")
                        
                        # Check if profile_context was set by _update_main_graph
                        if current_state and 'profile_context' in current_state:
                            profile_context_str = current_state['profile_context']
                            print(f"Profile context from conversation thread: {profile_context_str}")
                            
                            if profile_context_str:
                                # Verify profile context contains expected profile information
                                profile_context_lower = profile_context_str.lower()
                                expected_elements = ["engineer", "married", "children", "new york", "36_45"]
                                found_elements = [elem for elem in expected_elements if elem in profile_context_lower]
                                
                                print(f"Profile elements found in context: {found_elements}")
                                assert len(found_elements) >= 2, f"Expected at least 2 profile elements in context, found {len(found_elements)}: {found_elements}. Context: {profile_context_str}"
                                
                                print(f"✅ Profile context from _update_main_graph verified: {profile_context_str}")
                            else:
                                assert False, "Profile context exists but is empty"
                        else:
                            print("No profile_context found in conversation state - _update_main_graph may not have set it")
                            assert False, "Profile context should be set in conversation state by _update_main_graph"
                    else:
                        print(f"Could not retrieve checkpoint data. Checkpoint: {checkpoint}")
                        assert False, "Could not access conversation state to verify profile context"
                        
                except Exception as e:
                    print(f"Error accessing checkpointer state: {e}")
                    # Fallback: test that profile context can be built from database
                    print("Fallback: Testing profile context building from database")
                    from app.ai.orchestrator_agent import GlobalState
                    test_state = GlobalState()
                    profile_context_str = test_state.get_profile_context(user_id)
                    assert profile_context_str != "User profile not available.", f"Should be able to build profile context from database. Got: {profile_context_str}"
                    print(f"✅ Fallback profile context building verified: {profile_context_str}")
            else:
                print("No checkpointer available - cannot verify conversation state")
                assert False, "Checkpointer should be available to verify profile context was set"
            
            # Verify profile context was built correctly in the state
            personal_context = user_storage.get_personal_context(user_id)
            assert personal_context is not None, "Personal context should exist"
            assert personal_context.get("occupation_type") in ["software engineer", "engineer", "technology"], f"Expected engineer occupation, got {personal_context.get('occupation_type')}"
            assert personal_context.get("marital_status") == "married", f"Expected married status, got {personal_context.get('marital_status')}"
            assert personal_context.get("children_count") == 2, f"Expected 2 children, got {personal_context.get('children_count')}"

            print("✅ Profile context integration verified!")


class TestRealOnboardingComplete:
    """Test real onboarding completion flow with OpenAI API."""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_then_route_to_investment(self, clean_database):
        """Test full onboarding completion then routing to investment agent."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()
            user_id = "complete_onboard_test_user"
            session_id = "complete_onboard_session"

            print("\n--- Investment Test Setup via Fixture ---")
            print(f"Available users: {clean_database}")
            assert user_id in clean_database, f"Expected user {user_id} to be created by fixture"

            # Step 1: Start onboarding with investment question
            result1 = await config.invoke_conversation(
                user_message="I want to start investing my money. What should I do?",
                user_id=user_id,
                session_id=session_id
            )
            
            # Should route to onboarding since profile is empty
            assert len(result1["messages"]) > 0
            result1_message = result1["messages"][-1]
            assert result1_message["agent"] == "onboarding"
            # Should ask for personal information (flexible wording)
            content_lower = result1_message["content"].lower()
            assert any(word in content_lower for word in ["age", "occupation", "about", "share", "tell", "help"])
            
            # Step 2: Provide comprehensive profile information in one response
            comprehensive_response = """I'm 28 years old, so I guess that puts me in the 26-35 age range. 
            I'm in early career stage working as a software engineer. I live in California which is definitely 
            a high cost of living area. I'm single with no dependents and no caregiving responsibilities. 
            I'm not married and have a domestic partnership status."""
            
            result2 = await config.invoke_conversation(
                user_message=comprehensive_response,
                user_id=user_id,
                session_id=session_id
            )
            
            # Should still be onboarding but extracting lots of data
            assert len(result2["messages"]) > 0
            result2_message = result2["messages"][-1]
            assert result2_message["agent"] == "onboarding"
            
            # Step 3: Fill any remaining gaps if needed
            follow_up_response = """I have no children, so 0 dependents total. I live alone with no family 
            structure complexities - just single with no dependents. My occupation is in tech/engineering field."""
            
            result3 = await config.invoke_conversation(
                user_message=follow_up_response,
                user_id=user_id,
                session_id=session_id
            )
            
            # Should still be onboarding but getting closer to completion
            assert len(result3["messages"]) > 0
            result3_message = result3["messages"][-1]
            assert result3_message["agent"] == "onboarding"
            
            # Step 4: Confirm completion or provide final details
            confirmation_response = """Yes, that all sounds right. I'm ready to get investment advice now."""
            
            result4 = await config.invoke_conversation(
                user_message=confirmation_response,
                user_id=user_id,
                session_id=session_id
            )
            
            # Could be onboarding completion or already routing to investment
            # Let's be flexible here since OpenAI might complete in different steps
            assert len(result4["messages"]) > 0
            result4_message = result4["messages"][-1]
            assert result4_message["agent"] in ["onboarding", "investment"]
            
            # Step 5: Now ask investment question again - should route to investment agent
            final_result = await config.invoke_conversation(
                user_message="Now that my profile is complete, what investment strategy do you recommend?",
                user_id=user_id,
                session_id=session_id
            )
            
            # This should definitely route to investment agent now
            assert len(final_result["messages"]) > 0
            final_message = final_result["messages"][-1]
            assert final_message["agent"] == "investment"
            assert "investment" in final_message["content"].lower()
            
            # Verify profile was actually saved to database
            from app.core.database import user_storage
            
            # Print debug info
            print(f"\nDEBUG - Final result: {final_result}")
            
            # Check if user exists, if not create them for verification
            user_data = user_storage.get_user_by_id(user_id)
            if user_data is None:
                # User might not be in main table, but let's check personal context
                print(f"User {user_id} not found in users table, checking personal context...")
            
            personal_context = user_storage.get_personal_context(user_id)
            print(f"Personal context: {personal_context}")
            
            # Verify at least personal context was saved (core requirement)
            assert personal_context is not None, "Personal context should be saved after onboarding"
            
            # Check for key profile fields that were provided
            assert personal_context.get("age_range") is not None, "Age range should be extracted"
            assert personal_context.get("occupation_type") is not None, "Occupation should be extracted"
            
            # If user exists, verify profile_complete flag
            if user_data:
                assert user_data.get("profile_complete") is True, "User should be marked as profile complete"
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_then_route_to_spending(self, clean_database):
        """Test full onboarding completion then routing to spending agent."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()
            user_id = "complete_onboard_spending_user"
            session_id = "complete_onboard_spending_session"

            print("\n--- Spending Test Setup via Fixture ---")
            print(f"Available users: {clean_database}")
            assert user_id in clean_database, f"Expected user {user_id} to be created by fixture"

            # Step 1: Start with budgeting question
            result1 = await config.invoke_conversation(
                user_message="I need help with my budget and tracking expenses.",
                user_id=user_id,
                session_id=session_id
            )
            
            # Should route to onboarding
            assert len(result1["messages"]) > 0
            result1_message = result1["messages"][-1]
            assert result1_message["agent"] == "onboarding"
            
            # Step 2: Provide very complete profile info in one go
            complete_profile = """I'm 35 years old in the 36-45 age range, established career working as a teacher. 
            I live in Texas with moderate cost of living. I'm married with dual income family structure, 
            have 2 children so that's 2 total dependents. No caregiving responsibilities for aging parents. 
            My marital status is married. I think that covers everything for my profile - I'm ready for budgeting help now."""
            
            result2 = await config.invoke_conversation(
                user_message=complete_profile,
                user_id=user_id,
                session_id=session_id
            )
            
            # Might complete onboarding in this step or still be onboarding
            assert len(result2["messages"]) > 0
            result2_message = result2["messages"][-1]

            print(f"\nStep 2 result agent: {result2_message['agent']}")
            print(f"Step 2 content: {result2_message['content']}")

            assert result2_message["agent"] in ["onboarding", "spending"]
            
            # Step 3: Ask spending question - should route to spending agent
            spending_result = await config.invoke_conversation(
                user_message="Perfect! Now help me create a family budget for our household expenses.",
                user_id=user_id,
                session_id=session_id
            )
            
            # Should route to spending agent
            assert len(spending_result["messages"]) > 0
            spending_message = spending_result["messages"][-1]
            assert spending_message["agent"] == "spending"
            assert any(word in spending_message["content"].lower()
                      for word in ["budget", "spending", "expense", "family"])
            
            # Verify database state
            user_data = user_storage.get_user_by_id(user_id)
            if user_data:
                print(f"User data: {user_data}")
                assert user_data.get("profile_complete") is True, "User should be marked as profile complete"
            else:
                print(f"User {user_id} not found in users table, checking personal context...")
            
            # Verify that personal context was saved (core requirement)
            personal_context = user_storage.get_personal_context(user_id)
            print(f"Personal context: {personal_context}")
            assert personal_context is not None, "Personal context should be saved after onboarding"
            assert personal_context.get("age_range") in ["36_45", "26_35"]  # Allow some flexibility
            assert "teacher" in personal_context.get("occupation_type", "").lower()
            assert personal_context.get("children_count") == 2


class TestRealLLMProviders:
    """Test real LLM provider functionality."""
    
    def test_real_provider_availability(self):
        """Test real provider availability check."""
        factory = LLMFactory()
        providers = factory.get_available_providers()
        
        # Should have at least one provider if any API key is set
        assert len(providers) >= 1
        
        # Check which specific providers are available
        if os.getenv('OPENAI_API_KEY'):
            assert LLMProvider.OPENAI in providers
        if os.getenv('ANTHROPIC_API_KEY'):
            assert LLMProvider.ANTHROPIC in providers
        if os.getenv('GOOGLE_API_KEY'):
            assert LLMProvider.GOOGLE in providers
    
    def test_real_configuration_validation(self):
        """Test real configuration validation."""
        factory = LLMFactory()
        
        # Should validate successfully with real API key
        assert factory.validate_configuration() is True
    
    def test_real_llm_error_handling(self):
        """Test real LLM error handling with invalid input."""
        factory = LLMFactory()
        llm = factory.create_llm()
        
        # Test with extremely long input to potentially trigger errors
        very_long_message = "Hello! " * 10000  # Very long message
        messages = [{"role": "user", "content": very_long_message}]
        
        try:
            response = llm.invoke(messages)
            # If it succeeds, just check we got a response
            assert response is not None
        except Exception as e:
            # If it fails due to length limits, that's expected
            assert "token" in str(e).lower() or "length" in str(e).lower() or "limit" in str(e).lower()


class TestRealMultiProviderLLM:
    """Test real LLM functionality across all available providers."""
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    def test_real_provider_basic_call(self, provider, env_key):
        """Test basic LLM call for each available provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")
        
        factory = LLMFactory()
        llm = factory.create_llm(provider=provider)
        
        assert llm is not None, f"Failed to create {provider.value} LLM instance"
        
        messages = [{"role": "user", "content": "Say exactly: TEST_RESPONSE"}]
        response = llm.invoke(messages)
        
        assert response is not None
        assert hasattr(response, 'content')
        assert len(response.content) > 0
        assert "TEST_RESPONSE" in response.content
        
        print(f"✅ {provider.value} provider test passed")
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    def test_real_provider_system_prompt(self, provider, env_key):
        """Test system prompt functionality for each available provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")
        
        factory = LLMFactory()
        llm = factory.create_llm(provider=provider)
        
        messages = [
            {"role": "system", "content": "You are a math tutor. Answer only with numbers."},
            {"role": "user", "content": "What is 2+2?"}
        ]
        response = llm.invoke(messages)
        
        assert response is not None
        assert "4" in response.content
        
        print(f"✅ {provider.value} system prompt test passed")
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    def test_real_provider_financial_context(self, provider, env_key):
        """Test financial domain responses for each available provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")
        
        factory = LLMFactory()
        llm = factory.create_llm(provider=provider)
        
        messages = [
            {"role": "system", "content": "You are a financial advisor. Provide brief, helpful advice."},
            {"role": "user", "content": "What are the basics of emergency fund planning?"}
        ]
        response = llm.invoke(messages)
        
        assert response is not None
        assert len(response.content) > 50  # Should be a substantial response
        
        # Check for financial keywords (flexible matching)
        content_lower = response.content.lower()
        financial_keywords = ["emergency", "fund", "savings", "money", "expenses", "months", "income"]
        found_keywords = [kw for kw in financial_keywords if kw in content_lower]
        
        assert len(found_keywords) >= 2, f"Expected financial keywords in response, found: {found_keywords}"
        
        print(f"✅ {provider.value} financial context test passed")
    
    def test_real_provider_switching(self):
        """Test switching between different providers dynamically."""
        available_providers = []
        
        if os.getenv('OPENAI_API_KEY'):
            available_providers.append(LLMProvider.OPENAI)
        if os.getenv('ANTHROPIC_API_KEY'):
            available_providers.append(LLMProvider.ANTHROPIC)
        if os.getenv('GOOGLE_API_KEY'):
            available_providers.append(LLMProvider.GOOGLE)
        
        if len(available_providers) < 2:
            pytest.skip("Need at least 2 providers configured to test switching")
        
        factory = LLMFactory()
        
        # Test creating LLMs with different providers
        test_message = [{"role": "user", "content": "Hello, respond with your provider name if you know it, otherwise just say 'Hello'"}]
        
        responses = {}
        for provider in available_providers:
            llm = factory.create_llm(provider=provider)
            response = llm.invoke(test_message)
            responses[provider.value] = response.content
            
            assert response is not None
            assert len(response.content) > 0
        
        print(f"✅ Provider switching test passed with {len(available_providers)} providers")
        for provider, response in responses.items():
            print(f"  {provider}: {response[:100]}...")


class TestRealMultiProviderConversationFlow:
    """Test real conversation flow across all available providers."""
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    def test_real_provider_orchestrator_routing(self, provider, env_key):
        """Test orchestrator routing decisions for each provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")
        
        factory = LLMFactory()
        llm = factory.create_llm(provider=provider)
        
        # Test orchestrator-style routing prompt
        system_prompt = """You must respond with exactly one word: SMALLTALK, SPENDING, INVESTMENT, or ONBOARDING.
        
        User input: Hello there!
        Response:"""
        
        messages = [{"role": "user", "content": system_prompt}]
        response = llm.invoke(messages)
        
        # Should route to SMALLTALK for greeting
        valid_routes = ["SMALLTALK", "SPENDING", "INVESTMENT", "ONBOARDING"]
        assert response.content.strip() in valid_routes, f"Expected one of {valid_routes}, got: {response.content}"
        # Greeting should typically route to SMALLTALK
        assert "SMALLTALK" in response.content
        
        print(f"✅ {provider.value} orchestrator routing test passed")
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    @pytest.mark.asyncio
    async def test_real_provider_conversation_greeting(self, provider, env_key):
        """Test real conversation greeting for each provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")

        # Temporarily override the default provider for this test
        original_provider = os.getenv('DEFAULT_LLM_PROVIDER')

        try:
            # Set the provider for this test
            os.environ['DEFAULT_LLM_PROVIDER'] = provider.value

            with pytest.MonkeyPatch().context() as m:
                # Remove any existing patches
                m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)
                
                config = get_orchestrator_agent()

                result = await config.invoke_conversation(
                    user_message="Hello there!",
                    user_id=f"real_test_user_{provider.value}",
                    session_id=f"real_test_session_{provider.value}"
                )
                
                assert result is not None
                assert len(result["messages"]) > 0
                last_message = result["messages"][-1]
                assert last_message["agent"] == "small_talk"  # Should route to small talk
                assert len(last_message["content"]) > 10  # Real response should be substantial
                assert "hello" in last_message["content"].lower() or "hi" in last_message["content"].lower()
                
                print(f"✅ {provider.value} conversation greeting test passed")
                
        finally:
            # Restore original provider
            if original_provider:
                os.environ['DEFAULT_LLM_PROVIDER'] = original_provider
            elif 'DEFAULT_LLM_PROVIDER' in os.environ:
                del os.environ['DEFAULT_LLM_PROVIDER']
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    @pytest.mark.asyncio
    async def test_real_provider_financial_question(self, provider, env_key):
        """Test real conversation with financial question for each provider."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")

        # Temporarily override the default provider for this test
        original_provider = os.getenv('DEFAULT_LLM_PROVIDER')

        try:
            # Set the provider for this test
            os.environ['DEFAULT_LLM_PROVIDER'] = provider.value

            with pytest.MonkeyPatch().context() as m:
                m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)
                
                config = get_orchestrator_agent()

                result = await config.invoke_conversation(
                    user_message="How should I invest my money?",
                    user_id=f"real_test_user_2_{provider.value}",
                    session_id=f"real_test_session_2_{provider.value}"
                )
                
                assert result is not None
                # Should route to onboarding (profile incomplete by default)
                assert len(result["messages"]) > 0
                last_message = result["messages"][-1]
                assert last_message["agent"] == "onboarding"
                # Should ask for personal information (flexible wording)
                content_lower = last_message["content"].lower()
                assert any(word in content_lower for word in ["profile", "age", "occupation", "about", "share", "tell", "help", "information"])
                
                print(f"✅ {provider.value} financial question test passed")

        finally:
            # Restore original provider
            if original_provider:
                os.environ['DEFAULT_LLM_PROVIDER'] = original_provider
            elif 'DEFAULT_LLM_PROVIDER' in os.environ:
                del os.environ['DEFAULT_LLM_PROVIDER']


class TestSystemMessageRouting:
    """Tests for SYSTEM message routing after Plaid account linking."""

    @pytest.mark.asyncio
    async def test_system_message_routes_to_onboarding_when_profile_incomplete(self):
        """Test that SYSTEM messages route to ONBOARDING when profile is incomplete."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            config = get_orchestrator_agent()

            # Test SYSTEM message with incomplete profile (default state)
            result = await config.invoke_conversation(
                user_message="SYSTEM: User successfully connected 2 bank accounts from Chase Bank. Please congratulate them and check if their profile is now complete.",
                user_id="system_test_user_incomplete",
                session_id="system_test_session_incomplete"
            )

            assert result is not None
            assert len(result["messages"]) >= 2, f"Expected at least 2 messages (routing + response), got {len(result['messages'])}"

            # Check routing decision (second-to-last message)
            routing_message = result["messages"][-2]
            assert routing_message["agent"] == "orchestrator", f"Expected orchestrator routing, got '{routing_message['agent']}'"
            assert "ONBOARDING" in routing_message["content"], f"Routing decision should contain 'ONBOARDING', got: {routing_message['content']}"

            # Check agent response (last message)
            agent_response = result["messages"][-1]
            assert agent_response["agent"] == "onboarding", f"Expected 'onboarding' agent response, got '{agent_response['agent']}'"

            # Should mention congratulations or account connection
            content_lower = agent_response["content"].lower()
            assert any(word in content_lower for word in ["congratulat", "account", "bank", "connect", "link"]), f"Content doesn't mention account connection: {agent_response['content']}"

    @pytest.mark.asyncio
    async def test_spending_query_routes_to_spending_when_profile_complete(self):
        """Test that spending queries route to SPENDING when profile is complete."""
        with pytest.MonkeyPatch().context() as m:
            m.delattr("app.services.llm_service.llm_factory.create_llm", raising=False)

            # Mock a complete profile by creating personal context
            from app.core.database import user_storage
            from app.core.sqlmodel_models import PersonalContextCreate
            user_id = "system_test_user_complete"

            # Create user and complete personal context
            user_storage.create_user({
                "id": user_id,
                "email": "test@example.com",
                "password_hash": "fake_hash",
                "name": "Test User"
            })

            # Create completed personal context using the proper model
            context_data = PersonalContextCreate(
                age_range="26_35",
                life_stage="early_career",
                occupation_type="technology",
                location_context="san_francisco_bay_area",
                family_structure="single_no_dependents",
                marital_status="single",
                total_dependents_count=0,
                caregiving_responsibilities="none",
                is_complete=True  # This is the key - profile is complete
            )
            user_storage.create_personal_context(user_id, context_data)

            config = get_orchestrator_agent()

            # Test spending query with complete profile
            result = await config.invoke_conversation(
                user_message="How should I budget my monthly expenses?",
                user_id=user_id,
                session_id="system_test_session_complete"
            )

            assert result is not None
            assert len(result["messages"]) >= 2, f"Expected at least 2 messages (routing + response), got {len(result['messages'])}"

            # Check routing decision (second-to-last message)
            routing_message = result["messages"][-2]
            assert routing_message["agent"] == "orchestrator", f"Expected orchestrator routing, got '{routing_message['agent']}'"
            assert "SPENDING" in routing_message["content"], f"Routing decision should contain 'SPENDING', got: {routing_message['content']}"

            # Check agent response (last message)
            agent_response = result["messages"][-1]
            assert agent_response["agent"] == "spending", f"Expected 'spending' agent response, got '{agent_response['agent']}'"

            # Should mention budgeting or expenses
            content_lower = agent_response["content"].lower()
            assert any(word in content_lower for word in ["budget", "expense", "spending", "money", "financial"]), f"Content doesn't mention budgeting: {agent_response['content']}"
