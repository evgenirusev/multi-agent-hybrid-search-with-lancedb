import sys
import subprocess
import importlib.util

# Print information about the current Python environment
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Try to import pytest_asyncio to check if it's already installed
if importlib.util.find_spec("pytest_asyncio") is None:
    print("pytest_asyncio is not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest-asyncio"])
    print("Installation complete.")
else:
    print("pytest_asyncio is already installed.")
    
# Verify the installation
if importlib.util.find_spec("pytest_asyncio") is not None:
    print("Verification successful: pytest_asyncio is installed.")
else:
    print("Verification failed: pytest_asyncio is still not installed.")

# Show where the package is installed
try:
    import pytest_asyncio
    print(f"pytest_asyncio location: {pytest_asyncio.__file__}")
except ImportError:
    print("Failed to import pytest_asyncio") 