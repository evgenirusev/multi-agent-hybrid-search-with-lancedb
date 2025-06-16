import os
import sys
import pytest
from unittest.mock import AsyncMock

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.crews.legal_support_agents.legal_support_agents import (
    LegalSupportAgents
)

# ── Skip the whole module if Azure creds are absent ──────────────────────────
REQUIRED_ENV = ("AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_VERSION", "GPT4_DEPLOYMENT_NAME")

missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
pytestmark = pytest.mark.skipif(
    len(missing) > 0, reason=f"Missing Azure creds: {', '.join(missing)}"
)

# ── Canonical routing test cases ─────────────────────────────────────────────
EMPLOYMENT_QUERIES = [
    "How much is John Doe's salary?",
    "What's John Doe's job title?",
    "What is an employment contract?",
    "How do stock options typically vest?",
    "What happens to my options when I leave the company?"
]

COMPLIANCE_QUERIES = [
    "What GDPR obligations does our company have?",
    "Do we need to register with the ICO for data protection?",
    "What are the data protection requirements for storing employee data?",
    "What compliance checks are needed before onboarding an employee?"
]

EQUITY_QUERIES = [
    "Who are the current shareholders of the company?",
    "Show me the breakdown of share classes.",
    "How many shares are available in the option pool?",
    "What voting rights do preference shares have?",
    "Can you provide the cap table after the seed round?"
]

# ── Re‑usable fixture: one crew instance with stubbed specialist agents ──────
@pytest.fixture(scope="module")
def legal_support():
    """
    Returns LegalSupportAgents whose _handle_* methods are stubbed.
    Only the routing step hits the live LLM.
    """
    c = LegalSupportAgents(debug_enabled=False)

    # Stub the specialist agents so no second LLM call happens
    c._handle_employment_query = AsyncMock(return_value="EMPLOYMENT_HANDLER_OK")
    c._handle_compliance_query = AsyncMock(return_value="COMPLIANCE_HANDLER_OK")
    c._handle_equity_query = AsyncMock(return_value="EQUITY_HANDLER_OK")

    return c

# ── Parametrised tests ──────────────────────────────────────────────────────
@pytest.mark.asyncio
@pytest.mark.parametrize("query", COMPLIANCE_QUERIES)
async def test_routes_to_compliance(legal_support, query):
    # Reset mock call counts before each test
    legal_support._handle_compliance_query.reset_mock()
    legal_support._handle_employment_query.reset_mock()
    legal_support._handle_equity_query.reset_mock()
    
    result = await legal_support.process_query(query)

    legal_support._handle_compliance_query.assert_awaited_once()
    legal_support._handle_employment_query.assert_not_called()
    legal_support._handle_equity_query.assert_not_called()

    assert result == "COMPLIANCE_HANDLER_OK"

@pytest.mark.asyncio
@pytest.mark.parametrize("query", EMPLOYMENT_QUERIES)
async def test_routes_to_employment(legal_support, query):
    # Reset mock call counts before each test
    legal_support._handle_compliance_query.reset_mock()
    legal_support._handle_employment_query.reset_mock()
    legal_support._handle_equity_query.reset_mock()
    
    result = await legal_support.process_query(query)

    legal_support._handle_employment_query.assert_awaited_once()
    legal_support._handle_compliance_query.assert_not_called()
    legal_support._handle_equity_query.assert_not_called()

    assert result == "EMPLOYMENT_HANDLER_OK"

@pytest.mark.asyncio
@pytest.mark.parametrize("query", EQUITY_QUERIES)
async def test_routes_to_equity(legal_support, query):
    # Reset mock call counts before each test
    legal_support._handle_compliance_query.reset_mock()
    legal_support._handle_employment_query.reset_mock()
    legal_support._handle_equity_query.reset_mock()
    
    result = await legal_support.process_query(query)

    legal_support._handle_equity_query.assert_awaited_once()
    legal_support._handle_employment_query.assert_not_called()
    legal_support._handle_compliance_query.assert_not_called()

    assert result == "EQUITY_HANDLER_OK"