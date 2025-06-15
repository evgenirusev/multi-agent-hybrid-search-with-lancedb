import os
import lancedb
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from typing import Optional
import uuid
import logging
from lancedb.pydantic import LanceModel, Vector
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("rag_document_store")

load_dotenv()

# Azure OpenAI configuration
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_KEY")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT") 
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_VERSION")

# Get configuration values
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION")
EMBEDDING_DEPLOYMENT_NAME = os.getenv("EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002")

# LanceDB configuration
LANCEDB_STORAGE = os.getenv("LANCEDB_STORAGE", "lancedb_local")
LANCEDB_URI = os.getenv("LANCEDB_URI", "az://lancedb")
LANCEDB_ACCOUNT_NAME = os.getenv("LANCEDB_ACCOUNT_NAME", "your-account-name")
LANCEDB_ACCOUNT_KEY = os.getenv("LANCEDB_ACCOUNT_KEY", "")

# Define the document schema
class DocumentChunk(LanceModel):
    vector: Vector(1536)  # Dimension for OpenAI ada-002 embeddings
    text: str
    document_id: str
    document_name: str
    chunk_index: int
    section: Optional[str] = None

# Main document store class
class DocumentStore:
    """Class to handle document storage and retrieval operations."""
    
    def __init__(self):
        """Initialize the document store."""
        self.db = None
        self.table = None
        self.embeddings_model = None
        
    async def initialize(self):
        """Initialize connections and resources."""
        self.embeddings_model = get_embeddings_model()
        
        # Connect to LanceDB - prioritize Azure Blob Storage
        if LANCEDB_ACCOUNT_NAME and LANCEDB_ACCOUNT_KEY:
            # Ensure we're using the correct URI format for Azure
            azure_uri = LANCEDB_URI if LANCEDB_URI.startswith("az://") else f"az://{LANCEDB_URI}"
            
            storage_options = {
                "account_name": LANCEDB_ACCOUNT_NAME,
                "account_key": LANCEDB_ACCOUNT_KEY
            }
            
            self.db = await lancedb.connect_async(
                azure_uri,
                storage_options=storage_options
            )
        else:
            # Throw an error if Azure Blob storage credentials are not provided
            raise ValueError("LANCEDB_ACCOUNT_NAME and LANCEDB_ACCOUNT_KEY must be provided")
        
        # Get or create table - use legal_documents for consistency
        table_name = "legal_documents"
        tables = await self.db.table_names()
        
        if table_name not in tables:
            self.table = await self.db.create_table(table_name, schema=DocumentChunk)
        else:
            self.table = await self.db.open_table(table_name)
            
        # Always ensure FTS index exists
        try:
            from lancedb.index import FTS
            # Check if FTS index exists
            indexes = await self.table.list_indices()
            has_fts = any(isinstance(idx, FTS) for idx in indexes)
            
            if not has_fts:
                logger.info("Creating full-text search index on 'text' column...")
                await self.table.create_index("text", config=FTS())
                logger.info("Full-text search index created successfully")
            else:
                logger.info("Full-text search index already exists")
        except Exception as e:
            logger.error(f"Error creating/verifying FTS index: {e}")
            raise
    
    async def add_document(self, text: str, document_name: str, document_id: Optional[str] = None):
        """Add a document to the store with chunking."""
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Split text into chunks
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " "],
            chunk_size=500,
            chunk_overlap=50,
        )
        
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            logger.warning("No chunks created from document")
            return {"document_id": document_id, "chunks_added": 0}
        
        # Get embeddings for all chunks
        embeddings = self.embeddings_model.embed_documents(chunks)
        
        # Create document chunks with vectors
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            documents.append(DocumentChunk(
                vector=embedding,
                text=chunk,
                document_id=document_id,
                document_name=document_name,
                chunk_index=i,
                section=identify_section(chunk)
            ))
        
        try:
            await self.table.add(documents)
        except Exception as e:
            logger.error(f"Error adding documents to LanceDB: {e}")
            raise

        return {"document_id": document_id, "chunks_added": len(documents)}
    
    async def ensure_fts_index(self):
        """Ensure the full-text search index exists."""
        try:
            from lancedb.index import FTS
            indexes = await self.table.list_indices()
            has_fts = any(isinstance(idx, FTS) for idx in indexes)
            
            if not has_fts:
                logger.info("Creating full-text search index on 'text' column...")
                await self.table.create_index("text", config=FTS())
                logger.info("Full-text search index created successfully")
        except Exception as e:
            logger.error(f"Error ensuring FTS index: {e}")
            raise

    async def search(self, query: str, limit: int = 5):
        """Search for documents matching the query using hybrid search."""
        # Ensure FTS index exists before searching
        await self.ensure_fts_index()
        
        # Get query embedding
        query_embedding = self.embeddings_model.embed_query(query)
        
        # Build hybrid search query step by step
        search_query = self.table.query()
        search_query = search_query.nearest_to(query_embedding)  # Vector similarity search
        search_query = search_query.nearest_to_text(query)       # Text search component
        search_query = search_query.rerank()                     # Combine and normalize scores
        search_query = search_query.limit(limit)                 # Limit results
        
        # Execute search and return results
        results = await search_query.to_list()
        
        return results
    
    async def delete_document(self, document_id: str):
        """Delete all chunks with the given document_id from the store."""
        try:
            # Create a filter condition to match the document_id
            delete_condition = f"document_id = '{document_id}'"
            
            # Get number of chunks to delete (for reporting)
            count_query = await self.table.query().where(delete_condition).to_pandas()
            chunks_count = len(count_query)
            
            if chunks_count == 0:
                logger.warning(f"No chunks found with document_id: {document_id}")
                return {"document_id": document_id, "chunks_deleted": 0}
            
            # Delete rows matching the condition
            await self.table.delete(delete_condition)
            
            logger.info(f"Deleted {chunks_count} chunks with document_id: {document_id}")
            return {"document_id": document_id, "chunks_deleted": chunks_count}
            
        except Exception as e:
            logger.error(f"Error deleting document from LanceDB: {e}")
            raise
            
    async def get_all_documents(self):
        """Retrieve all unique documents in the store."""
        try:
            # Get all documents from the table
            df = await self.table.query().to_pandas()
            
            if df.empty:
                logger.info("No documents found in the store")
                return []
            
            # Group by document_id and get the first document_name for each
            # Use drop_duplicates to get unique document_id/document_name pairs
            unique_docs = df[['document_id', 'document_name']].drop_duplicates()
            
            # Count chunks for each document
            chunk_counts = df.groupby('document_id').size().reset_index(name='chunks_count')
            
            # Merge to get document info with chunk counts
            result = pd.merge(unique_docs, chunk_counts, on='document_id')
            
            # Convert to list of dictionaries
            documents = result.to_dict('records')
            
            logger.info(f"Found {len(documents)} unique documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents from LanceDB: {e}")
            raise

# Create a global instance for use across the application
document_store = DocumentStore()

# Initialize function for application startup
async def initialize_document_store():
    """Initialize the document store at application startup."""
    await document_store.initialize() 

# Initialize Azure OpenAI Embeddings
def get_embeddings_model():
    """Initialize and return the Azure OpenAI Embeddings model."""
    return AzureOpenAIEmbeddings(
        azure_deployment=EMBEDDING_DEPLOYMENT_NAME,
        openai_api_version=AZURE_OPENAI_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    )

# Extract section from text if available
def identify_section(text: str) -> Optional[str]:
    """Extract section number and title from text if available."""
    import re
    # Pattern to match section numbers like "9.", "9.1", "10.", etc.
    section_pattern = r'^\s*(\d+(?:\.\d+)?)\s+(.+?)(?=\n|$)'
    match = re.search(section_pattern, text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None 