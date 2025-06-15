# Agent Support Crew Tests

This directory contains tests for the Agent Support Crew, focused on the orchestrator agent that routes queries to specialized agents.

## Test Files

- `test_orchestrator_routing_live.py` - Pytest-based integration tests for routing with real LLM calls (recommended)
- `test_orchestrator_query.py` - Interactive testing tool for trying individual queries
- `conftest.py` - Pytest configuration file that helps with module imports

## Testing Approach

The pytest-based approach in `test_orchestrator_routing_live.py` provides the best balance:
- Makes actual LLM API calls for the routing decision
- Stubs the specialist agent handlers to minimize token usage
- Uses pytest fixtures and parametrization for cleaner test code
- More precise assertions about handler invocation

## Installation and Running Tests

### 1. Install test dependencies

```bash
# Install all required packages
pip install pytest pytest-asyncio==0.26.0 pytest-cov python-dotenv
```

Or using the requirements file:

```bash
# Install from the development requirements file (includes test dependencies)
pip install -r requirements-dev.txt
```

### 2. Run the tests

```bash
# Run the pytest-based tests
pytest tests/test_orchestrator_routing_live.py -v

# Run a specific test function
pytest tests/test_orchestrator_routing_live.py::test_routes_to_agent -v

# Run with more detailed output
pytest tests/test_orchestrator_routing_live.py -vv

# Run with output showing test progress
pytest tests/test_orchestrator_routing_live.py -v --no-header --no-summary -s
```

## Troubleshooting

### Module Import Issues

If you encounter import errors like `ModuleNotFoundError: No module named 'src'`, it means pytest can't find your module. The `conftest.py` file should fix this, but you can also:

1. Run pytest from the project root directory
2. Set your PYTHONPATH environment variable:
   ```bash
   export PYTHONPATH=$PYTHONPATH:/path/to/your/project
   ```

### Fixture Scope Issues

If you encounter errors like `ScopeMismatch: You tried to access the function scoped fixture monkeypatch with a module scoped request object`, it means you're trying to use a function-scoped fixture in a module-scoped fixture. Make sure your fixtures have compatible scopes.

### Missing pytest-asyncio

If you see warnings about unknown pytest.mark.asyncio, you need to install and configure pytest-asyncio:

```bash
pip install pytest-asyncio==0.26.0
```

The `conftest.py` file should already include the necessary configuration.

### Environment Variables

Make sure all required environment variables are set. You can create a `.env` file in the project root with your Azure OpenAI credentials:

```
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_VERSION=2023-05-15
GPT4_DEPLOYMENT_NAME=your-deployment-name
```

## Interactive Query Testing

The interactive query tester in `test_orchestrator_query.py` allows for manual testing of routing decisions:

```bash
# Interactive mode
python -m tests.test_orchestrator_query --interactive

# Test a specific query
python -m tests.test_orchestrator_query "Can the platform help with cap tables?"

# Enable debug mode to see the full prompts
python -m tests.test_orchestrator_query --debug "What is an employment contract?"
```

## Required Environment Variables

The tests make actual API calls to the Azure OpenAI service to test routing decisions with real LLM responses. These tests:

- Require valid Azure OpenAI credentials in environment variables
- Incur actual API costs for each test run
- Provide realistic testing of LLM behavior
- Test both clear-cut and ambiguous routing scenarios

To run these tests, ensure the following environment variables are set:
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_VERSION`
- `GPT4_DEPLOYMENT_NAME`

## Adding New Test Cases

When adding new test cases, consider:

1. For routine routing decisions, add new queries to the `AGENT_QUERIES` or `EMPLOYMENT_QUERIES` lists.
2. For ambiguous or edge cases, add new tuples to the `AMBIGUOUS_QUERIES` list.
3. For more complex scenarios, create new parametrized test functions.

Example of adding a new test case:

```python
# Add to AMBIGUOUS_QUERIES:
AMBIGUOUS_QUERIES = [
    # Existing cases
    ("How do options work in documents?", AgentName.AGENT),
    
    # New test case
    ("Tell me about equity documentation in my startup", AgentName.EMPLOYMENT),
]
```

/Users/evgenirusev/anaconda3/bin/python -m pytest tests/test_orchestrator_routing_live.py -v