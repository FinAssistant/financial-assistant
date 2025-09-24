test_data = [
    # --- Example A (Julia, progressive onboarding) ---
    {
        "name": "Example A - Julia",
        "steps": [
            {
                "input": "Hi there, I’m Julia, 28 years old and working as a nurse in Miami.",
                "expected": {
                    "extracted_data": {
                        "age_range": "26_35",
                        "occupation_type": "healthcare",
                        "location_context": "Florida, moderate cost of living",
                        "life_stage": "early_career"
                    },
                    "completion_status": "incomplete",
                    "user_response": "Thanks for sharing some details! Could you also tell me about your family situation and financial goals so I can complete your profile?"
                }
            },
            {
                "input": "I live with my partner, and we don’t have kids yet. I’m trying to build up savings for a down payment on a condo.",
                "expected": {
                    "extracted_data": {
                        "age_range": "26_35",
                        "occupation_type": "healthcare",
                        "location_context": "Florida, moderate cost of living",
                        "life_stage": "early_career",
                        "family_structure": "domestic_partnership_no_dependents",
                        "marital_status": "domestic_partnership",
                        "total_dependents_count": 0,
                        "children_count": 0,
                        "caregiving_responsibilities": "none"
                    },
                    "completion_status": "complete",
                    "user_response": "Great, your profile is now complete! With your career and goal of saving for a condo, I can help you build a savings plan tailored to your situation."
                }
            }
        ]
    },

    # --- Example B (David, full info in one go) ---
    {
        "name": "Example B - David",
        "steps": [
            {
                "input": "Hello, I’m David, 47, a high school teacher in Ohio. I’m married with two kids in middle school, and my wife also works full-time. We’re trying to save for their college tuition.",
                "expected": {
                    "extracted_data": {
                        "age_range": "46_55",
                        "occupation_type": "teacher",
                        "location_context": "Ohio, moderate cost of living",
                        "life_stage": "family_building",
                        "family_structure": "married_dual_income",
                        "marital_status": "married",
                        "total_dependents_count": 2,
                        "children_count": 2,
                        "caregiving_responsibilities": "none"
                    },
                    "completion_status": "complete",
                    "user_response": "Thanks for the detailed introduction! With two kids and college savings as a goal, I can help you build a plan that balances your current expenses with your long-term goals."
                }
            }
        ]
    },

    # --- Example C (Priya, progressive onboarding) ---
    {
        "name": "Example C - Priya",
        "steps": [
            {
                "input": "Good afternoon! I’m Priya, 34, a software product manager based in Seattle.",
                "expected": {
                    "extracted_data": {
                        "age_range": "26_35",
                        "occupation_type": "engineer",
                        "location_context": "Washington, high cost of living",
                        "life_stage": "established_career"
                    },
                    "completion_status": "incomplete",
                    "user_response": "Thanks for introducing yourself! Could you tell me about your family situation and dependents so I can complete your profile?"
                }
            },
            {
                "input": "I’m married, and we just had our first baby last year. I want to figure out how to balance childcare costs with building an emergency fund.",
                "expected": {
                    "extracted_data": {
                        "age_range": "26_35",
                        "occupation_type": "engineer",
                        "location_context": "Washington, high cost of living",
                        "life_stage": "family_building",
                        "family_structure": "married_dual_income",
                        "marital_status": "married",
                        "total_dependents_count": 1,
                        "children_count": 1,
                        "caregiving_responsibilities": "none"
                    },
                    "completion_status": "complete",
                    "user_response": "Thanks for sharing! With a new baby and childcare expenses, building an emergency fund is a smart move. I can help you plan for both short-term stability and long-term growth."
                }
            }
        ]
    },

    # --- Example D (Carlos, update after mom passes) ---
    {
        "name": "Example D - Carlos",
        "steps": [
            {
                "input": "Hey, I’m Carlos, 61, retired military and living in Arizona. I’m widowed and caring for my elderly mother. I’m looking for guidance on managing expenses while living on a fixed pension.",
                "expected": {
                    "extracted_data": {
                        "age_range": "56_65",
                        "occupation_type": "retired_military",
                        "location_context": "Arizona, moderate cost of living",
                        "life_stage": "retirement",
                        "family_structure": "widowed_with_dependents",
                        "marital_status": "widowed",
                        "total_dependents_count": 1,
                        "children_count": 0,
                        "caregiving_responsibilities": "aging_parents"
                    },
                    "completion_status": "complete",
                    "user_response": "Thank you for sharing your situation. Living on a fixed pension while also caring for a parent can be challenging — I can help you structure your budget to keep it manageable."
                }
            },
            {
                "input": "My mom has recently passed away, so I no longer have caregiving responsibilities.",
                "expected": {
                    "extracted_data": {
                        "age_range": "56_65",
                        "occupation_type": "retired_military",
                        "location_context": "Arizona, moderate cost of living",
                        "life_stage": "retirement",
                        "family_structure": "widowed_no_dependents",
                        "marital_status": "widowed",
                        "total_dependents_count": 0,
                        "children_count": 0,
                        "caregiving_responsibilities": "none"
                    },
                    "completion_status": "complete",
                    "user_response": "I’m very sorry for your loss. I’ve updated your profile to reflect that you no longer have caregiving responsibilities. Let’s review your financial plan to make sure it supports your needs in retirement."
                }
            }
        ]
    }
]


"""
Integration tests with REAL API calls using the actual OnboardingAgent.
These tests are SKIPPED in CI and only run locally when:
1. At least one LLM provider API key is available (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
2. RUN_REAL_TESTS environment variable is set to 'true'

Mocks only database operations to control test state while using the real agent logic.

To run these tests locally:
# Test with OpenAI (default)
export RUN_REAL_TESTS=true
export OPENAI_API_KEY=sk-your-openai-key-here
pytest tests/test_onboarding_agent_real.py -v

# Test with Anthropic Claude
export RUN_REAL_TESTS=true
export DEFAULT_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
pytest tests/test_onboarding_agent_real.py -v
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from app.ai.onboarding import OnboardingAgent, OnboardingState
from app.services.llm_service import llm_factory
from langchain_core.messages import HumanMessage, AIMessage


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
def mock_llm_factory():
    """Override the conftest.py mock to disable it for real tests."""
    # This fixture has the same name as conftest.py, so it overrides it
    # Don't patch anything - just yield to let real LLM calls happen
    yield None


class TestRealOnboardingAgent:
    """Integration tests for OnboardingAgent with real LLM API calls and mocked database."""

    @pytest.mark.parametrize("example", test_data)
    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.get_graphiti_client')
    async def test_real_agent_with_examples(self, mock_graphiti, mock_storage, example):
        """Test real onboarding agent with predefined examples."""

        # Mock database to return controlled state
        mock_storage.get_user_by_id.return_value = {"id": "test_user"}
        mock_storage.get_personal_context.return_value = {}
        mock_storage.create_or_update_personal_context.return_value = None
        mock_storage.update_user.return_value = None

        # Mock Graphiti
        mock_graphiti_client = AsyncMock()
        mock_graphiti.return_value = mock_graphiti_client

        print(f"\n🧪 Testing: {example['name']}")

        agent = OnboardingAgent()
        collected_data = {}

        for step_num, step in enumerate(example['steps'], 1):
            print(f"\n--- Step {step_num} ---")
            print(f"Input: {step['input']}")

            # Create state with current collected data
            state = OnboardingState(
                messages=[HumanMessage(content=step['input'])],
                collected_data=collected_data,
                current_step="continue" if collected_data else "welcome"
            )

            config = {
                "configurable": {
                    "user_id": "test_user",
                    "thread_id": "test_thread"
                }
            }

            # Update mock to return current collected data
            mock_storage.get_personal_context.return_value = collected_data

            # Call the real agent's LLM method
            result = await agent._call_llm(state, config)

            print(f"✅ LLM Response received")
            print(f"Data extraction completed: {len(result.get('collected_data', {}))} fields")

            # Verify response structure
            assert "messages" in result, "Result should contain messages"
            assert "collected_data" in result, "Result should contain collected_data"
            assert "needs_database_update" in result, "Result should contain needs_database_update"

            # Verify AI message was created
            ai_messages = result["messages"]
            assert len(ai_messages) == 1, "Should have exactly one AI message"
            ai_message = ai_messages[0]
            assert isinstance(ai_message, AIMessage), "Should be an AIMessage"
            assert len(ai_message.content) > 0, "AI message should have content"
            assert ai_message.additional_kwargs.get("agent") == "onboarding", "Should be tagged as onboarding agent"

            # Update collected data for next iteration
            collected_data = result["collected_data"]
            print(f"Collected data: {collected_data}")

            # Verify key extractions match expected data (with flexibility for LLM variations)
            expected = step['expected']['extracted_data']

            # Test age_range extraction
            if 'age_range' in expected:
                actual_age = collected_data.get("age_range")
                expected_age = expected['age_range']
                assert actual_age == expected_age, f"Expected age_range '{expected_age}', got '{actual_age}'"
                print(f"✓ Age range: {actual_age}")

            # Test occupation extraction with flexibility
            if 'occupation_type' in expected:
                actual_occ = collected_data.get("occupation_type", "")
                expected_occ = expected['occupation_type']

                # Define flexible matching for occupation types
                occupation_matches = {
                    "healthcare": ["healthcare", "nurse", "medical", "nursing"],
                    "engineer": ["engineer", "technology", "tech", "software", "product manager"],
                    "teacher": ["teacher", "education", "educator", "teaching"],
                    "retired_military": ["retired", "military", "veteran", "army", "navy", "air force"]
                }

                if expected_occ in occupation_matches:
                    assert any(term in actual_occ.lower() for term in occupation_matches[expected_occ]), \
                        f"Expected occupation related to '{expected_occ}', got '{actual_occ}'"
                else:
                    assert actual_occ == expected_occ, f"Expected occupation_type '{expected_occ}', got '{actual_occ}'"
                print(f"✓ Occupation: {actual_occ}")

            # Test marital status extraction
            if 'marital_status' in expected:
                actual_marital = collected_data.get("marital_status")
                expected_marital = expected['marital_status']
                assert actual_marital == expected_marital, f"Expected marital_status '{expected_marital}', got '{actual_marital}'"
                print(f"✓ Marital status: {actual_marital}")

            # Test location extraction (flexible)
            if 'location_context' in expected:
                actual_location = collected_data.get("location_context", "")
                expected_location = expected['location_context']
                # Extract state/region from expected location
                if "Florida" in expected_location:
                    assert any(term in actual_location.lower() for term in ["florida", "miami"]), f"Expected Florida/Miami in location, got '{actual_location}'"
                elif "Ohio" in expected_location:
                    assert "ohio" in actual_location.lower(), f"Expected Ohio in location, got '{actual_location}'"
                elif "Washington" in expected_location or "Seattle" in step['input']:
                    assert any(term in actual_location.lower() for term in ["washington", "seattle"]), f"Expected Washington/Seattle in location, got '{actual_location}'"
                elif "Arizona" in expected_location:
                    assert "arizona" in actual_location.lower(), f"Expected Arizona in location, got '{actual_location}'"
                print(f"✓ Location: {actual_location}")

            # Test data collection progress
            expected_status = step['expected']['completion_status']
            field_count = len([v for v in collected_data.values() if v is not None])
            print(f"Field count: {field_count}/9")

            if expected_status == "complete":
                # For complete status, we expect significant data collection
                # Note: _call_llm doesn't determine completion status anymore
                print(f"✓ Expected complete status - collected {field_count} fields")
                assert field_count >= 4, f"Expected at least 4 fields for 'complete' test case, got {field_count}"
            else:
                print(f"✓ Expected incomplete status - collected {field_count} fields")

            print(f"✅ Step {step_num} validation passed")

        print(f"✅ {example['name']} completed successfully!")

    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.get_graphiti_client')
    async def test_real_agent_database_integration(self, mock_graphiti, mock_storage):
        """Test that the real agent calls database methods correctly."""

        # Setup mocks
        mock_storage.get_user_by_id.return_value = {"id": "test_user"}
        mock_storage.get_personal_context.return_value = {"age_range": "26_35"}
        mock_storage.create_or_update_personal_context.return_value = None
        mock_storage.update_user.return_value = None
        mock_graphiti_client = AsyncMock()
        mock_graphiti.return_value = mock_graphiti_client

        print("\n🧪 Testing database integration")

        agent = OnboardingAgent()

        # Test _read_db
        state = OnboardingState()
        config = {"configurable": {"user_id": "test_user"}}

        db_result = agent._read_db(state, config)

        # Verify database was called
        mock_storage.get_user_by_id.assert_called_with("test_user")
        mock_storage.get_personal_context.assert_called_with("test_user")

        # Verify result
        assert db_result["collected_data"] == {"age_range": "26_35"}
        assert db_result["current_step"] == "continue"
        print("✓ Database read works correctly")

        # Test _update_db
        update_state = OnboardingState(
            collected_data={"age_range": "26_35", "occupation_type": "engineer"},
            needs_database_update=True,
            onboarding_complete=True
        )

        update_result = agent._update_db(update_state, config)

        # Verify database update calls (expecting two calls: profile data + completion status)
        from unittest.mock import call
        expected_calls = [
            call("test_user", {"age_range": "26_35", "occupation_type": "engineer"}),
            call("test_user", {"is_complete": True})
        ]
        mock_storage.create_or_update_personal_context.assert_has_calls(expected_calls)
        mock_storage.update_user.assert_called_with(
            "test_user",
            {"profile_complete": True}
        )

        assert update_result == {"needs_database_update": False}
        print("✓ Database update works correctly")

        print("✅ Database integration test passed")

    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.get_graphiti_client')
    async def test_real_agent_memory_storage(self, mock_graphiti, mock_storage):
        """Test that the real agent stores conversation memory."""

        mock_storage.get_user_by_id.return_value = {"id": "test_user"}
        mock_graphiti_client = AsyncMock()
        mock_graphiti.return_value = mock_graphiti_client

        print("\n🧪 Testing memory storage")

        agent = OnboardingAgent()

        # Create state with conversation
        state = OnboardingState(
            messages=[
                HumanMessage(content="I'm 30 and work as an engineer"),
                AIMessage(content="Thanks for sharing! Tell me about your family situation.")
            ]
        )

        config = {"configurable": {"user_id": "test_user"}}

        # Test memory storage
        await agent._store_memory(state, config)

        # Verify Graphiti was called
        mock_graphiti_client.add_episode.assert_called_once_with(
            user_id="test_user",
            content="I'm 30 and work as an engineer",
            context={"assistant_response": "Thanks for sharing! Tell me about your family situation."},
            name="Onboarding Conversation",
            source_description="onboarding_agent"
        )

        print("✓ Memory storage called correctly")
        print("✅ Memory storage test passed")

    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.get_graphiti_client')
    async def test_real_agent_consistency(self, mock_graphiti, mock_storage):
        """Test that the real agent produces consistent results."""

        # Setup mocks
        mock_storage.get_user_by_id.return_value = {"id": "test_user"}
        mock_storage.get_personal_context.return_value = {}
        mock_graphiti_client = AsyncMock()
        mock_graphiti.return_value = mock_graphiti_client

        print("\n🧪 Testing consistency across multiple calls")

        agent = OnboardingAgent()

        # Test the same input multiple times
        test_input = "I'm 30 years old, work as a software engineer in San Francisco, and I'm single with no kids."

        results = []
        for i in range(3):
            state = OnboardingState(
                messages=[HumanMessage(content=test_input)],
                collected_data={},
                current_step="welcome"
            )

            config = {"configurable": {"user_id": f"test_user_{i}", "thread_id": f"test_thread_{i}"}}

            result = await agent._call_llm(state, config)
            results.append(result)

            # Basic validation
            assert "collected_data" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

        # Check consistency in key extractions
        age_ranges = [r["collected_data"].get("age_range") for r in results]
        occupations = [r["collected_data"].get("occupation_type", "") for r in results]
        marital_statuses = [r["collected_data"].get("marital_status") for r in results]

        print(f"Age ranges: {age_ranges}")
        print(f"Occupations: {occupations}")
        print(f"Marital statuses: {marital_statuses}")

        # Age should be consistently 26_35 for "30 years old"
        age_set = set(age for age in age_ranges if age is not None)
        assert len(age_set) <= 1, f"Age range should be consistent, got: {age_set}"
        if age_set:
            assert "26_35" in age_set, f"Expected 26_35 for 30 years old, got: {age_set}"

        # Occupation should be consistently related to engineering/tech
        for occupation in occupations:
            if occupation:  # Allow None values
                assert any(term in occupation.lower() for term in ["engineer", "tech", "software"]), \
                    f"Occupation should be engineering-related, got: {occupation}"

        # Marital status should be consistently single
        marital_set = set(status for status in marital_statuses if status is not None)
        if marital_set:
            assert "single" in marital_set, f"Expected single marital status, got: {marital_set}"

        print("✅ Consistency test passed")

    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.get_graphiti_client')
    async def test_real_agent_life_changes(self, mock_graphiti, mock_storage):
        """Test that the real agent handles life changes correctly."""

        # Setup mocks
        mock_storage.get_user_by_id.return_value = {"id": "test_user"}
        mock_storage.get_personal_context.return_value = {}
        mock_graphiti_client = AsyncMock()
        mock_graphiti.return_value = mock_graphiti_client

        print("\n🧪 Testing life change scenarios")

        agent = OnboardingAgent()

        # Test job loss scenario
        state = OnboardingState(
            messages=[HumanMessage(content="I just lost my job last month and my spouse is now the only income earner.")],
            collected_data={"age_range": "36_45", "occupation_type": "engineer", "marital_status": "married"},
            current_step="continue"
        )

        config = {"configurable": {"user_id": "test_user", "thread_id": "test_thread"}}

        # Mock to return existing data
        mock_storage.get_personal_context.return_value = {
            "age_range": "36_45",
            "occupation_type": "engineer",
            "marital_status": "married"
        }

        result = await agent._call_llm(state, config)

        # Verify life change was detected
        collected_data = result["collected_data"]
        print(f"Updated data after job loss: {collected_data}")

        # Should detect unemployment and family structure change
        occupation = collected_data.get("occupation_type", "")
        life_stage = collected_data.get("life_stage", "")
        family_structure = collected_data.get("family_structure", "")

        # Check for unemployment indicators
        assert any(term in occupation.lower() for term in ["unemployed", "between", "job"]) or \
               any(term in life_stage.lower() for term in ["unemployed", "between", "job"]), \
               f"Should detect unemployment in occupation '{occupation}' or life_stage '{life_stage}'"

        # Check for family income change
        if family_structure:
            assert "single_income" in family_structure or "no_income" in family_structure, \
                f"Should detect family income change, got family_structure: '{family_structure}'"

        print("✓ Life change detection works")
        print("✅ Life change test passed")
