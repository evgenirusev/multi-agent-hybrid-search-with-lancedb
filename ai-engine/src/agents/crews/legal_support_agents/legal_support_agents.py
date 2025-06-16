import os
import yaml
import logging
import sys
import json
from pathlib import Path
from typing import Type, Optional, Dict, Any
from dotenv import load_dotenv
from enum import Enum

from openai import AsyncAzureOpenAI
import instructor
from pydantic import BaseModel, Field

from src.agents.rag.document_store import document_store, initialize_document_store

# Configure minimal logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('legal_support_agents')

class AgentName(str, Enum):
    EMPLOYMENT = "Employment Expert"
    COMPLIANCE = "Compliance Specialist"
    EQUITY = "Equity Management Expert"

class RoutingDecision(BaseModel):
    agent_name: AgentName

class Answer(BaseModel):
    content: str

class LegalSupportAgents:
    BASE_DIR = Path(__file__).parent
    
    def __init__(self, debug_enabled: bool = False):
        """
        Initialize the LegalSupportAgents with configs and an async LLM client.
        
        Args:
            debug_enabled: Enable detailed request inspection logging
        """
        load_dotenv()
        
        # Store debug configuration
        self.debug_enabled = debug_enabled
        
        # Load Azure OpenAI configuration from environment variables
        self.azure_api_key = os.getenv("AZURE_OPENAI_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_version = os.getenv("AZURE_OPENAI_VERSION")
        self.azure_deployment = os.getenv("GPT4_DEPLOYMENT_NAME")

        # Paths to configuration files
        self.agents_config_path = os.path.join(self.BASE_DIR, "config", "agents.yaml")
        self.tasks_config_path = os.path.join(self.BASE_DIR, "config", "tasks.yaml")
        
        # Load YAML configuration files
        try:
            with open(self.agents_config_path, 'r') as f:
                self.agents_config = yaml.safe_load(f)
            with open(self.tasks_config_path, 'r') as f:
                self.tasks_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file not found: {e.filename}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}") from e
        
        # Set up AsyncAzureOpenAI client and patch with Instructor
        client = AsyncAzureOpenAI(
            api_key=self.azure_api_key,
            api_version=self.azure_api_version,
            azure_endpoint=self.azure_endpoint
        )
        # Patch the client with instructor
        self.client = instructor.apatch(client)
        
        # Flag for lazy RAG initialization
        self.rag_initialized = False

    async def process_query(self, query: str) -> str:
        """
        Process a user query by routing it and generating an answer.

        Args:
            query: The user's query text
        """
        try:
            orchestrator_config = self.agents_config["orchestrator"]
            employment_config = self.agents_config["employment_expert"]
            compliance_config = self.agents_config["compliance_specialist"]
            equity_config = self.agents_config["equity_management_expert"]
            
            # Construct prompt for routing the query
            routing_prompt = self.tasks_config["route_request"]["description"].format(
                query=query,
                agent_role=orchestrator_config["role"],
                agent_goal=orchestrator_config["goal"],
                agent_backstory=orchestrator_config["backstory"],
                routing_guidelines="\n".join([f"- {item}" for item in orchestrator_config.get("routing_guidelines", [])]),
                tone=orchestrator_config.get("tone")
            )

            # Log request inspection details if debug is enabled
            log_request_inspection(model_type=RoutingDecision, prompt=routing_prompt, agent_name="ROUTING", enabled=self.debug_enabled)

            # Route the query using an LLM call
            routing_decision = await self.client.chat.completions.create(
                model=self.azure_deployment,
                messages=[{"role": "user", "content": routing_prompt}],
                response_model=RoutingDecision,
                max_retries=2  # Retry on validation failure
            )

            # Define agent handlers with their corresponding configs
            agent_handlers = {
                AgentName.EMPLOYMENT: lambda q: self._handle_employment_query(q, employment_config),
                AgentName.COMPLIANCE: lambda q: self._handle_compliance_query(q, compliance_config),
                AgentName.EQUITY: lambda q: self._handle_equity_query(q, equity_config)
            }
            
            # Use the appropriate handler or return a default message
            handler = agent_handlers.get(routing_decision.agent_name)
            if handler:
                return await handler(query)
            
            return "**[Support Request Orchestrator]** I'm sorry, but I cannot answer that question."

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return "An error occurred while processing your query."
    
    async def _handle_employment_query(self, query: str, employment_config: dict) -> str:
        """Handle queries related to employment and stock options."""
        relevant_context = await self.get_relevant_context(query)

        employment_prompt = self.tasks_config["answer_employment_question"]["description"].format(
            query=query, 
            relevant_context=relevant_context,
            agent_role=employment_config["role"],
            agent_goal=employment_config["goal"],
            agent_backstory=employment_config["backstory"],
            expertise_areas="\n".join([f"- {item}" for item in employment_config.get("expertise_areas", [])]),
            response_guidelines=employment_config.get("response_guidelines"),
            tone=employment_config.get("tone")
        )

        log_request_inspection(model_type=Answer, prompt=employment_prompt, agent_name="EMPLOYMENT", enabled=self.debug_enabled)

        answer = await self.client.chat.completions.create(
            model=self.azure_deployment,
            messages=[{"role": "user", "content": employment_prompt}],
            response_model=Answer,
            max_retries=2
        )
        return f"**[Employment Expert]** {answer.content}"
    
    async def _handle_compliance_query(self, query: str, compliance_config: dict) -> str:
        """Handle queries related to compliance and regulatory requirements."""
        compliance_prompt = self.tasks_config["answer_compliance_question"]["description"].format(
            query=query,
            agent_role=compliance_config["role"],
            agent_goal=compliance_config["goal"],
            agent_backstory=compliance_config["backstory"],
            response_guidelines=compliance_config.get("response_guidelines"),
            tone=compliance_config.get("tone")
        )

        log_request_inspection(model_type=Answer, prompt=compliance_prompt, agent_name="COMPLIANCE", enabled=self.debug_enabled)
        
        answer = await self.client.chat.completions.create(
            model=self.azure_deployment,
            messages=[{"role": "user", "content": compliance_prompt}],
            response_model=Answer,
            max_retries=2
        )
        return f"**[Compliance Specialist]** {answer.content}"
    
    async def _handle_equity_query(self, query: str, equity_config: dict) -> str:
        """
        Handle queries related to equity management and company structure.
        
        Args:
            query: The user's query text
            equity_config: The configuration for the equity management expert agent
        """
        equity_prompt = self.tasks_config["answer_equity_question"]["description"].format(
            query=query,
            agent_role=equity_config["role"],
            agent_goal=equity_config["goal"],
            agent_backstory=equity_config["backstory"],
            expertise_areas="\n".join([f"- {item}" for item in equity_config.get("expertise_areas", [])]),
            response_guidelines=equity_config.get("response_guidelines"),
            tone=equity_config.get("tone")
        )

        log_request_inspection(model_type=Answer, prompt=equity_prompt, agent_name="EQUITY", enabled=self.debug_enabled)
        
        answer = await self.client.chat.completions.create(
            model=self.azure_deployment,
            messages=[{"role": "user", "content": equity_prompt}],
            response_model=Answer,
            max_retries=2
        )
        return f"**[Equity Management Expert]** {answer.content}"
    
    async def ensure_rag_initialized(self):
        """Ensure the RAG document store is initialized, but only once."""
        if not self.rag_initialized:
            await initialize_document_store()
            self.rag_initialized = True
    
    async def search_documents(self, query: str, limit: int = 5):
        """Search for relevant documents in the document store."""
        await self.ensure_rag_initialized()
        results = await document_store.search(query, limit)
        return results
    
    async def get_relevant_context(self, query: str) -> str:
        """Retrieve and format relevant document context for the query."""
        try:
            await self.ensure_rag_initialized()
            results = await self.search_documents(query)
            
            if not results or len(results) == 0:
                return "No relevant documents found."
            
            context = "Here is relevant information from our documents:\n\n"
            for i, result in enumerate(results):
                context += f"Document {i+1}: {result['document_name']}\n"
                if result.get('section'):
                    context += f"Section: {result['section']}\n"
                context += f"Content: {result['text']}\n\n"
            return context
        except Exception as e:
            logger.error(f"Error retrieving document context: {e}")
            return "Could not retrieve relevant documents due to an error."

# Function to log request inspection details
def log_request_inspection(model_type: Type[BaseModel], prompt: str, agent_name: str = "INSTRUCTOR", enabled: bool = True):
    """
    Log the request inspection details for an agent call.
    
    Args:
        model_type: The Pydantic model type being used for the response
        prompt: The prompt text being sent to the agent
        agent_name: Name of the agent for logging purposes
        enabled: Whether logging is enabled
    """
    if not enabled:
        return
        
    # Get the Pydantic schema for the model
    schema = model_type.model_json_schema()
    
    print(f"\n\n==== {agent_name} REQUEST INSPECTION ====")
    print("Messages:", json.dumps([{"role": "user", "content": prompt}], indent=2))
    print("Pydantic Schema:", json.dumps(schema, indent=2))
    print("=================================================\n\n")