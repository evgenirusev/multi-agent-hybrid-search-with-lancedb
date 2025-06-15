#!/bin/bash

# Print Python version and path to ensure we're using the right one
echo "Python version:"
python --version
echo "Python path:"
which python

# Install pytest-asyncio using the same Python that will run the tests
python -m pip install pytest-asyncio

# Run the tests
python -m pytest tests/test_orchestrator_routing_live.py -v 