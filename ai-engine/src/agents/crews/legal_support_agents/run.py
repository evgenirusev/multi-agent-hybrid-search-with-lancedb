#!/usr/bin/env python3

import os
import json
import argparse
import asyncio
from dotenv import load_dotenv
from agents.crews.legal_support_agents.legal_support_agents import LegalSupportAgents

async def async_main():
    """Run the legal support crew asynchronously."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Run the legal support crew")
    parser.add_argument("--query", type=str, default=None, help="The query to process")
    parser.add_argument("--model", type=str, default="gpt-4", help="The model to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # If model is specified as command line arg, set it in the environment
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
    
    # If no query provided, prompt the user
    if not args.query:
        args.query = input("Please enter your legal question: ")
    
    # Create the crew
    crew = LegalSupportAgents(debug_enabled=args.debug)
    
    # Process the query
    result = await crew.process_query(args.query)
    
    # Print the result
    print("\nResponse:")
    print(result)

def main():
    """Run the async main function."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main() 