# flow/agent.py
# The Agentic Flow
# This uses LangGraph to coordinate between processing and user-facing analysis
# from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI # [OPENAI_LANGCHAIN](https://langchain.com)
# from modules.extraction import process_inbound_directory

import os
from typing import TypedDict, List, Dict, Any, Union
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from modules.extraction import process_inbound_directory

## packages to load .env file
# from dotenv import load_dotenv
# from pathlib import Path

## sample ENV file:
# export OPENAI_API_KEY="OpenAI-API-Key"
# export ANTHROPIC_API_KEY="Anthropic-API-Key"
# export JOESANDBOX_API_KEY="JoeSandbox-API-Key"

# try: load_dotenv(Path('../.env'))
# except: load_dotenv()
# final: print(f"ENV file '.env' not found")

# 1. Define the Graph State
# This object is passed between every node in your graph.
class AgentState(TypedDict):
    query: str                   # User input from Streamlit chat
    processed_files: List[Dict]  # Results from the ingestion pipeline
    answer: str                  # Final response from GPT-4o
    api_keys: Dict[str, str]     # Keys passed from the UI sidebar

def build_agentic_flow():
    # Analyst Agent (GPT-4o)
    llm = ChatOpenAI(model="gpt-4o")
    
    workflow = StateGraph(dict)
    
    # Define Nodes: Processing -> Analysis -> Response
    workflow.add_node("ingest", run_file_processing) # Calls security & extraction
    workflow.add_node("analyze", lambda state: {"answer": llm.invoke(state["query"])})
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "analyze")
    workflow.add_edge("analyze", END)
    
    return workflow.compile()


def run_agent_query(user_query, api_key):
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
    
    workflow = StateGraph(dict)
    
    # Simple Analyst Node: Query DB and Summarize
    def analyst_node(state):
        # In a real app, this would use SQLDatabaseChain
        response = llm.invoke(f"Based on the invoice database, answer: {state['query']}")
        return {"answer": response.content}

    workflow.add_node("analyze", analyst_node)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", END)
    
    app = workflow.compile()
    return app.invoke({"query": user_query})

# 2. Define the "Processing" Node
# This bridges your extraction.py logic into the LangGraph flow.
def run_file_processing(state: AgentState):
    """
    Node: Scans the 'data' directory and runs security/extraction.
    """
    print("--- INGESTION NODE: Starting File Processing ---")
    
    # Trigger the core logic from extraction.py
    # We pull the keys from the state which were set in app.py
    summary = process_inbound_directory(
        input_dir="data",
        output_dir="invoices",
        anthropic_key=state['api_keys'].get('anthropic'),
        joe_key=state['api_keys'].get('joe')
    )
    
    # Return updates to the state
    return {"processed_files": summary}

# 3. Define the "Analyst" Node
# This uses GPT-4o to query your local SQLite database.
def run_sql_analyst(state: AgentState):
    """
    Node: Uses an LLM to answer questions about the processed data.
    """
    print(f"--- ANALYST NODE: Querying SQL for '{state['query']}' ---")
    
    if not state['query']:
        return {"answer": "No query provided. How can I help with your invoices today?"}

    # Connect to the DB created during ingestion
    db = SQLDatabase.from_uri("sqlite:///local_invoices.db")
    
    # Initialize GPT-4o as the analyst
    llm = ChatOpenAI(
        model="gpt-4o", 
        openai_api_key=state['api_keys'].get('openai'), 
        temperature=0
    )
    
    # Create the SQL Agent
    agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
    
    try:
        # Execute the query against the database
        result = agent_executor.invoke({"input": state['query']})
        return {"answer": result["output"]}
    except Exception as e:
        return {"answer": f"Analysis Error: {str(e)}"}

# --- New Router Function ---
def check_ingestion_success(state: AgentState):
    """
    Decision Point: Should we proceed to the Analyst or stop?
    """
    # If no files were processed or all files failed security/extraction
    if not state.get("processed_files"):
        print("--- ROUTER: Ingestion failed or empty. Ending Flow. ---")
        return "failed"
    
    # Optional: Check if there's at least one successful record in the DB
    print("--- ROUTER: Ingestion successful. Moving to Analyst. ---")
    return "success"

"""
# 4. Construct the Graph - previous without 'check_ingestion_success'
workflow = StateGraph(AgentState)

# Add our two primary nodes
workflow.add_node("ingest_node", run_file_processing)
workflow.add_node("analyst_node", run_sql_analyst)

# Define the flow: 
# When the app starts, it runs ingestion first, then the analyst.
workflow.add_edge(START, "ingest_node")
workflow.add_edge("ingest_node", "analyst_node")
workflow.add_edge("analyst_node", END)

# 5. Compile the Graph
# This 'app' object is what you import and call in your streamlit app.py
agent_app = workflow.compile()
"""

# --- Rebuilding the Graph with Conditions ---
workflow = StateGraph(AgentState)

workflow.add_node("ingest_node", run_file_processing)
workflow.add_node("analyst_node", run_sql_analyst)

workflow.set_entry_point("ingest_node")

# ADD CONDITIONAL EDGES
# After 'ingest_node', call 'check_ingestion_success' to decide next step
workflow.add_conditional_edges(
    "ingest_node",
    check_ingestion_success,
    {
        "success": "analyst_node",
        "failed": END
    }
)

workflow.add_edge("analyst_node", END)
agent_app = workflow.compile()




