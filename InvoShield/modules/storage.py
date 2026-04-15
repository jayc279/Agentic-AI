# modules/storage.py
# Schemas & DB
# Handles Pydantic and SQLite persistence
import sqlite3
import uuid
import json # added
from pydantic import BaseModel
from typing import List, Optional

class InvoiceItem(BaseModel):
    description: str
    quantity: int
    price: float

class InvoiceData(BaseModel):
    uid: str
    vendor: str
    total: float
    items: List[InvoiceItem]
    orig_loc: str
    pdf_loc: str
    line_num: Optional[int] = None

def init_db_old():
    conn = sqlite3.connect('local_invoices.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            uid TEXT PRIMARY KEY,
            vendor TEXT,
            total REAL,
            line_num INTEGER,
            # other entries
            fields TEXT
        )
    ''')
    conn.close()

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            uid TEXT PRIMARY KEY,
            vendor_name TEXT, address TEXT, invoice_date TEXT, 
            invoice_no INTEGER, product TEXT, gst_no TEXT, 
            qty REAL, hsn_code INTEGER, base_price REAL, 
            sgst_pct REAL, cgst_pct REAL, igst_pct REAL, 
            sgst_amt REAL, cgst_amt REAL, igst_amt REAL, total_amt REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(record):
    conn = sqlite3.connect('local_invoices.db')
    cursor = conn.cursor()
    
    # Requirement Step 3 & 7: Serialize fields dict to JSON string for SQL
    fields_json = json.dumps(record.get('fields', {}))
    
    cursor.execute('''
        INSERT OR REPLACE INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        record['uid'],
        record.get('vendor', 'Unknown'),
        record.get('total', 0.0),
        record.get('line_number'), # Step 6 capture
        # other field entries
        fields_json
    ))
    conn.commit()
    conn.close()


