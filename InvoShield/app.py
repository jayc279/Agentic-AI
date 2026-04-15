## app.py
"""
InvoShield | Agentic SQL & Vision Orchestrator
Note: this is WIP (Work -in- Progress). All related functions are still being worked on

This app integrates the Claude 3.5 Sonnet (Anthropic) for extraction and GPT-4o (OpenAI) for the SQL Analyst. 
And a PDF Previewer component.

In the context of this Streamlit app:
--------------------------------------
Import: app.py imports the compiled graph (the app or workflow object) from flow/agent.py.

Invocation: When a user interacts with the UI (e.g., clicks a button or sends a chat message), app.py calls the .invoke() or .stream() method on that imported graph object.

State Management: The graph then executes its defined nodes (Python functions) in the specified order, updating the "State" as it goes

Stateful Selection: You can click a row in the dataframe and the PDF appears instantly on the right.

Hybrid AI Power: 
- Claude 3.5 Sonnet handles the "messy" vision task (extraction), while 
- GPT-4o handles the "logical" task (SQL analysis).

Real Security: The Security Audit section specifically surfaces the files flagged by your Joe Sandbox hook.

Summary of the connections
---------------------------
* extraction.py: Contains the "worker" logic (the actual file scanning and AI parsing).
* agent.py: Contains the "orchestrator" logic (defines run_file_processing as a node in the graph).
* app.py: Contains the "interface" logic (the Streamlit button that calls the agent)

When you click "Start Processing" in Streamlit, it triggers the Agent, 
which executes the run_file_processing node, which in turn runs the code in extraction.py.

This app has 4 tab1, tab2, tab3, tab4
TAB 1: Ingestion Engine
TAB 2: Data Explorer & Preview
TAB 3: AI Analyst
TAB 4: Invoice Data Entry Form
"""

import streamlit as st
import os
import pandas as pd
import sqlite3
import base64
from pathlib import Path

import plotly.express as px
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

# Local Files
from modules.extraction import process_inbound_directory # High-precision logic
from modules.storage import init_db
from modules.invoice_entry import invoice_entry_tab
from display_analytics import display_analytics

# Import StreamLit CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Call the function with your file path
local_css("style.css")

# import LangGraph Agent
from flow.agent import agent_app

# 1. Setup & Configuration
st.set_page_config(page_title="InvoShield AI", layout="wide", page_icon="🛡️")

# Ensure directories exist
for folder in ["data", "invoices"]:
    Path(folder).mkdir(exist_ok=True)

if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []

# 2. Sidebar: Professional Config
with st.sidebar:
    st.title("Settings")
    anthropic_key = st.text_input("Anthropic API Key (Claude 3.5)", type="password")
    openai_key = st.text_input("OpenAI API Key (Analyst)", type="password")
    joe_key = st.text_input("Joe Sandbox Key (Security)", type="password")
    
    st.divider()
    if st.button("Clear Local Database"):
        if os.path.exists("local_invoices.db"):
            os.remove("local_invoices.db")
            init_db()
            st.rerun()

# 3. Main Interface
st.title("🛡️ InvoShield: Enterprise Invoice Intelligence")

tab1, tab2, tab3, tab4 = st.tabs(["📥 Ingestion Engine", "🔍 Data Explorer & Preview", "🤖 AI Analyst", "Data Entry"])

# --- TAB 1: INGESTION ---
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Pipeline Control")
	# For `use_container_width=True`, use `width='stretch'`. 
	# For `use_container_width=False`, use `width='content'`.
	# 'use_container_width' will be removed after 2025-12-31.
        if st.button("▶️ Start Processing 'data/' folder", width='content'):
            if not anthropic_key:
                st.error("Extraction requires an Anthropic Key for Claude 3.5 Sonnet.")
            else:
                with st.spinner("Analyzing files with Claude 3.5 & running security scans..."):
                    # <added>
                    # Logic loops through subfolders, checks signatures, calls Joe Sandbox if <25% confidence
                    summary = process_inbound_directory(
                        input_dir="data", 
                        output_dir="invoices",
                        anthropic_key=anthropic_key,
                        joe_key=joe_key
                    )
                    st.session_state.processed_files = summary
                    # </added>
                    st.success(f"Successfully processed {len(summary)} files.")

    with col2:
        st.subheader("Security Audit")
        # <added>
        exploits = [f for f in st.session_state.processed_files if not f.get('is_safe', True)]
        if exploits:
            st.error(f"Found {len(exploits)} Suspicious Files")
            for ex in exploits:
                st.write(f"🚩 {ex['filename']} (Flagged by Signature/Sandbox)")
        else:
            st.info("No threats detected in the 'data' directory.")
        # </added>

# --- TAB 2: EXPLORER & PREVIEW ---
with tab2:
    # <added>
    conn = sqlite3.connect('local_invoices.db')
    df = pd.read_sql_query("SELECT * FROM invoices", conn)
    conn.close()
    
    if not df.empty:
        col_list, col_prev = st.columns([1, 1])
        
        with col_list:
            st.subheader("Invoice Records")
	    # For `use_container_width=True`, use `width='stretch'`. 
	    # For `use_container_width=False`, use `width='content'`.
	    # 'use_container_width' will be removed after 2025-12-31.
            selected_row = st.dataframe(df, width='content', on_select="rerun", selection_mode="single-row")
            
            # Visual Vibe: Spend Analysis
            fig = px.pie(df, values='total', names='vendor', title="Total Spend Distribution")
            st.plotly_chart(fig, width='content')
            
        with col_prev:
            st.subheader("PDF Preview")
            if selected_row and len(selected_row.selection.rows) > 0:
                idx = selected_row.selection.rows[0]
                pdf_path = df.iloc[idx]['pdf_loc']
                
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
                    st.markdown(pdf_display, unsafe_allow_all_html=True)
                else:
                    st.warning("PDF file not found in storage.")
    else:
        st.write("Database is empty. Please run ingestion to populate data.")
    # </added>

# --- TAB 3: AI ANALYST ---
with tab3:
    st.subheader("Agentic Data Analysis")
    if not openai_key:
        st.warning("Please provide an OpenAI Key to enable the GPT-4o SQL Agent.")
    else:

	"""
	# Set up the initial state
	initial_state = {
    		"query": user_chat_input,
    		"processed_files": [],
    		"api_keys": {
        		"anthropic": anthropic_key,
        		"openai": openai_key,
        		"joe": joe_key
    		}
	}
	"""

        # <added>
        query = st.chat_input("Show me all invoices over $500 and their PDF links.")
        
        if query:
            with st.chat_message("user"):
                st.write(query)
            
            with st.chat_message("assistant"):
                db = SQLDatabase.from_uri("sqlite:///local_invoices.db")
                llm = ChatOpenAI(model="gpt-4o", openai_api_key=openai_key, temperature=0)
                # Production SQL Agent with error recovery
                agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
                
                try:
                    response = agent_executor.invoke({"input": query})
                    st.write(response["output"])
                except Exception as e:
                    st.error(f"Agent reasoning failed: {str(e)}")
        # </added>
	"""
		# Run the flow
		final_state = agent_app.invoke(initial_state)

		# Display results
		st.write(final_state["answer"])
	"""
		# NEW setup with check_ingestion_success in langgraph flow
		try:
    			final_state = agent_app.invoke(initial_state)
    
    			if not final_state.get("processed_files"):
        			st.warning("⚠️ Analysis skipped: No valid invoices were found in the data folder.")
    			else:
        			st.write(final_state["answer"])
		except Exception as e:
    			st.error(f"System Error: {e}")

# --- TAB 4: DATA ENTRY ---
with tab4:
	# from modules.data_entry import show_data_entry_tab        	# this contains sample fields
	# from modules.show_invoice_entry import show_invoice_tab	# this contains actual XLS files
	# from modules.show_invoice_entry import dynamic_invoice_entry	# dynamically calculates Totals
	invoice_entry_tab()

# call the function in sidebar
with st.sidebar:
    display_analytics()




