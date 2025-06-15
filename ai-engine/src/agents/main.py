#!/usr/bin/env python
import asyncio
import argparse
from agents.crews.legal_support_agents import LegalSupportAgents

async def run_legal_support_agents(query, debug=False):
    # Run the Legal Support Crew with the provided query
    crew = LegalSupportAgents(debug_enabled=debug)
    result = await crew.process_query(query)
    print("\n----- Legal Support Response -----")
    print(result)
    return result

def run():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Legal Support System')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging for API requests')
    parser.add_argument('query', nargs='*', help='The query to process')
    
    args = parser.parse_args()
    
    if args.query:
        # Use the arguments as the query
        query = ' '.join(args.query)
        asyncio.run(run_legal_support_agents(query, debug=args.debug))
    else:
        # No query provided, prompt the user
        query = input("Enter your legal question: ")
        asyncio.run(run_legal_support_agents(query, debug=args.debug))

if __name__ == "__main__":
    run()