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
COMPLIANCE_QUERIES = [
    "Can the platform help me conduct a data protection health check?",
    "Can the platform help me complete regulatory filings?",
    "Can the platform help me comply with GDPR?",
    "Can the platform help me monitor regulatory changes?",
    "Can the platform help me perform a compliance risk assessment?",
]

EMPLOYMENT_QUERIES = [
    "How much is Sally's salary?",
    "What is an employment contract?",
    "How do stock options typically vest?",
    "What happens to my options when I leave the company?"
]

EQUITY_QUERIES = [
    # Director/secretary/PSC queries
    "How many directors does my company have?",
    "Who is my company's secretary?",
    "How many registered PSCs do I have?",
    "Is the service address missing from any of my shareholders?",
    
    # Data queries
    "How many shareholders do I have?",
    "Do I have any outstanding convertibles?",
    "How large is my option pool?",
    "What is the total issued capital?",
    "How many share classes does the company have?",
    
    # Comparative analysis queries
    "Do I have any shareholders with more than 25% equity?",
    "How much equity do the founders have?",
    "What percentage of the company is held by employees?",
    "Who are the top 3 shareholders?",
    
    # Advisory queries
    "Do you think there is anything with my cap table which would raise concern going into a Series A?",
    "How does my cap table compare to other companies at Pre-Seed?",
    "Should I be considering increasing my option pool in my next funding round?",
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