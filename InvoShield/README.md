This README.md is designed to give a quick overview of the various functions in InvoShield ecosystem in under 5 minutes.  
It covers the directory structure, environment setup, and how to trigger the Agentic flow.

## README.md
# 🛡️ InvoShield | Agentic SQL & Vision Orchestrator
InvoShield is an enterprise-grade pipeline that uses **Claude 3.5 Sonnet** for visual document extraction, **GPT-4o** for agentic SQL analysis, and **Joe Sandbox** for automated exploit detection.  
__Note__: this is WIP (Work -in- Progress). All related functions are still being worked on


### 🏗️ Project Architecture
```text
project_root/
├── app.py                        # Streamlit UI & PDF Previewer
├── data/                         # Input: Drop raw invoices here (supports subfolders)
├── invoices/                     # Output: Standardized PDFs (UUID-named, no PII)
├── modules/
│   ├── security.py               # Signature Verification & Sandbox Logic
│   ├── extraction.py             # Claude 3.5 (HF/Anthropic) & Tesseract Logic
│   ├── display_analytics.py      # Display analytics based on User's search criteria
│   ├── invoice_entry             # Streamlit FORM to manually enter Invoice Data
│   └── storage.py                # SQLite Persistence & Pydantic Schemas
├── tests/                        # Pytest Suite (Security, Extraction, Storage)
├── flow/
│   └── agent.py           # LangGraph + GPT-4o SQL Agent
├── tests/                 # Pytest Suite (Security, Extraction, Storage)
└── .github/workflows/     # CI/CD Pipeline (GitHub Actions)

## 🚀 Quick Start## 1. Prerequisites

* Python 3.10+
* Tesseract OCR Engine:
* Ubuntu: sudo apt install tesseract-ocr
   * Mac: brew install tesseract

## 2. Installation
# Clone the repo
git clone https://github.com/invoshield

# Install dependencies
cd invoshield
pip install -r requirements.txt

## 3. Environment Configuration
Create a .env file (or enter directly in the Streamlit Sidebar):

ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_gpt4_key
JOE_SANDBOX_KEY=your_sandbox_key
* https://www.joesandbox.com/
- if you are a freelancer, researcher, student - Google Search "joesandbox registration requires company name and company web address.what if you only have gmail account and no company weblink"

## 4. Launch the Playground

streamlit run app.py
```
------------------------------
## 🧪 Testing & CI/CD## Local Testing
Run the full suite including mocks for AI models:

pytest tests/

### GitHub Actions
The pipeline automatically runs on every push to main.
Requirement: Ensure you have added your API keys to GitHub Settings > Secrets > Actions.

------------------------------
## 🛠️ Key Features

* Exploit Guard: Automatically flags files with mismatched signatures or <25% extraction confidence.
* Vibe-Coding UI: Side-by-side SQL data exploration and PDF previewing.
* Agentic Analyst: Ask "What was my highest spend last month?" to query the local SQLite DB via Natural Language.
* PII Protection: Original filenames are discarded in favor of unique IDs (UUIDs) for the final storage layer.

------------------------------
## 📜 License
Internal Use Only. Built with 🦾 using LangChain, LangGraph, and Streamlit.

### **Final Project Checklist**
1.  **Run `pip install -r requirements.txt`** to ensure your local environment is synced.
2.  **Verify `data/` folder exists**: The script will create it, but it's best to have it ready with a few test PDFs.
3.  **Check Tesseract**: Run `tesseract --version` in your terminal to confirm the OCR engine is accessible.




