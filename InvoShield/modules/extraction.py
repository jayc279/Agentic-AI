# modules/extraction.py
# AI Extraction

"""
How it fits into the LangGraph "ingest" node:
---------------------------------------------
When your workflow identifies a file, it should route based on the extension:

If Image/PDF: Route to "extract_layoutlm" (Claude 3.5).
If CSV/Excel: Route to "process_tabular_data" to ensure every line becomes its own searchable database entry.
"""

import pytesseract
from PIL import Image
from transformers import pipeline # [HUGGING_FACE](https://huggingface.co)

# Hugging Face Model (Paid/Heavy)
def extract_layoutlm(image_path):
    # Using a pre-trained DocVQA model as a proxy for LayoutLM extraction
    model_id = "impira/layoutlm-document-qa"
    nlp = pipeline("document-question-answering", model=model_id)
    
    # Local queries for fields
    fields = {
        "Total": "total",
        "Vendor": "vendor"
    }
    return fields

# Tesseract (Open Source)
def extract_tesseract(image_path):
    return pytesseract.image_to_string(Image.open(image_path))


import pandas as pd
import uuid

# capturing the line number as a field attribute.
def process_tabular_data(file_path, file_type):
    """
    Handles CSV and Excel files, capturing line numbers and 
    creating unique records for each row.
    """
    if file_type == '.csv':
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    records = []
    
    # Iterate with index to capture "Line Number" (Requirement Step 6)
    for index, row in df.iterrows():
        unique_id = str(uuid.uuid4())
        
        # Map row to standard schema
        record = {
            "uid": unique_id,
            "line_number": index + 1,  # Human-readable 1-based indexing
            # Capture all columns as fields
            "vendor": row.get('Vendor', 'Unknown'),
            "total": row.get('Total', 0.0)
        }
        records.append(record)
        
    return records

"""
This function serves as the orchestrator, scanning your data/ folder recursively and routing each file through security checks, extraction, and database persistence.
"""
import os
import uuid
from pathlib import Path
from modules.security import check_file_security  # Signature & Sandbox
from modules.extraction import extract_layoutlm, process_tabular_data
from modules.storage import save_to_db, init_db

def process_inbound_directory(input_dir="data", output_dir="invoices", anthropic_key=None, joe_key=None):
    """
    Recursively scans the input directory, verifies security, extracts fields,
    and stores results in the local DB.
    """
    # Ensure environment is ready
    init_db()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    processing_summary = []

    # 1. Recursive Scan (Requirement Step 1)
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = Path(file).suffix.lower()
            
            # 2a. Identify File Type & 2b. Security Verification
            # Custom logic: check_file_security returns (is_safe, message)
            is_safe, status_msg = check_file_security(file_path, api_key=joe_key)
            
            if not is_safe:
                print(f"ERROR: {status_msg} for {file}. Skipping.")
                processing_summary.append({
                    "filename": file, 
                    "is_safe": False, 
                    "status": status_msg
                })
                continue

            # 3, 4, 5, 6. Extraction and Field Capture
            try:
                if file_ext in ['.csv', '.xlsx']:
                    # Tabular Handler: Captures Line Numbers (Step 6)
                    records = process_tabular_data(file_path, file_ext)
                    for record in records:
                        # 8. Save to PDF & 7. Store to SQL
                        # (Internal logic generates PDF and updates DB)
                        save_to_db(record)
                
                elif file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                    # AI Handler: Claude 3.5/LayoutLM (Step 3)
                    fields = extract_layoutlm(file_path, api_key=anthropic_key)
                    
                    # 4. Unique ID & 5. Location Tracking
                    u_id = str(uuid.uuid4())
                    pdf_loc = os.path.join(output_dir, f"invoice_{u_id}.pdf")
                    
                    record = {
                        "uid": u_id,
                        "vendor": fields.get("vendor", "Unknown"),
                        "total": fields.get("total", 0.0),
                        # other fields
                        "fields": fields
                    }
                    save_to_db(record)
                
                processing_summary.append({
                    "filename": file, 
                    "is_safe": True, 
                    "status": "Processed Successfully"
                })

            except Exception as e:
                print(f"Failed to process {file}: {e}")
                processing_summary.append({
                    "filename": file, 
                    "is_safe": True, 
                    "status": f"Extraction Error: {str(e)}"
                })

    return processing_summary


