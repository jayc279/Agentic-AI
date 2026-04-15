import streamlit as st
import sqlite3
import uuid
from datetime import date

## DATA ENTRY FIELDS
"""
Name of Vendor : Str
Address : Str
Date : System Date Format
Invoice No : Int
Product : Str
Current GST No : AlphaNumeric
Qty : Float
HSN Code : Int
INV Base Price : Float
SGST as % : Decimal
CGST as % : Decimal
IGST as % : Decimal
SGST Amount = INV Base Price * SGST : Float
CGST Amount = INV Base Price * CGST : Float
IGST Amount = INV Base Price * IGST : Float
Total Amount = INV Base Price + SGST Amount + CGST Amount + IGST Amount : Float
"""

# Function to reset session state values
# Function to reset session state values
def reset_form():
    st.session_state.vendor_name = ""
    st.session_state.invoice_no = 0
    st.session_state.inv_date = date.today()
    st.session_state.address = ""
    st.session_state.product = ""
    st.session_state.gst_no = ""
    st.session_state.qty = 0.0
    st.session_state.hsn_code = 0
    st.session_state.base_price = 0.0
    st.session_state.sgst_pct = 0.0
    st.session_state.cgst_pct = 0.0
    st.session_state.igst_pct = 0.0


def invoice_entry_tab():
    st.header("📄 New Invoice Entry")
    
    # Section 1: Header Info
    col1, col2, col3 = st.columns(3)
    # vendor_name = col1.text_input("Name of Vendor")
    # invoice_no = col2.number_input("Invoice No", step=1, format="%d")
    vendor_name = col1.text_input("Name of Vendor", placeholder="Enter name of vendor...", key="vendor_name")
    invoice_no = col2.number_input("Invoice No", step=1, format="%d", key="invoice_no")

    # inv_date = col3.date_input("Date", value=date.today())
    inv_date = col3.date_input("Date", key="inv_date")

    # address = st.text_area("Address", placeholder="Enter vendor address...")
    address = st.text_area("Address", placeholder="Enter vendor address...", key="address")

    # Section 2: Product Details
    col4, col5 = st.columns(2)
    # product = col4.text_input("Product")
    # gst_no = col5.text_input("Current GST No")
    product = col4.text_input("Product", key="product")
    gst_no = col5.text_input("Current GST No", key="gst_no")

    col6, col7, col8 = st.columns(3)
    # qty = col6.number_input("Qty", min_value=0.0, step=1.0, format="%.2f")
    # hsn_code = col7.number_input("HSN Code", step=1, format="%d")
    # base_price = col8.number_input("INV Base Price", min_value=0.0, step=0.01, format="%.2f")
    qty = col6.number_input("Qty", min_value=0.0, step=1.0, format="%.2f", key="qty")
    hsn_code = col7.number_input("HSN Code", step=1, format="%d", key="hsn_code")
    base_price = col8.number_input("INV Base Price", min_value=0.0, step=0.01, format="%.2f", key="base_price")

    # Section 3: Taxes & Real-time Calculations
    st.markdown("---")
    st.subheader("Tax Configuration & Preview")
    t1, t2, t3 = st.columns(3)
    # sgst_pct = t1.number_input("SGST %", min_value=0.0, max_value=100.0, value=0.0)
    # cgst_pct = t2.number_input("CGST %", min_value=0.0, max_value=100.0, value=0.0)
    # igst_pct = t3.number_input("IGST %", min_value=0.0, max_value=100.0, value=0.0)

    sgst_pct = t1.number_input("SGST %", min_value=0.0, max_value=100.0, key="sgst_pct")
    cgst_pct = t2.number_input("CGST %", min_value=0.0, max_value=100.0, key="cgst_pct")
    igst_pct = t3.number_input("IGST %", min_value=0.0, max_value=100.0, key="igst_pct")

    # Automated Calculations
    sgst_amt = base_price * (sgst_pct / 100)
    cgst_amt = base_price * (cgst_pct / 100)
    igst_amt = base_price * (igst_pct / 100)
    total_amt = base_price + sgst_amt + cgst_amt + igst_amt

    # Live Totals Display
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("SGST Amt", f"{sgst_amt:.2f}")
    p2.metric("CGST Amt", f"{cgst_amt:.2f}")
    p3.metric("IGST Amt", f"{igst_amt:.2f}")
    p4.metric("Grand Total", f"{total_amt:.2f}")

    # For `use_container_width=True`, use `width='stretch'`. 
    # For `use_container_width=False`, use `width='content'`.
    # 'use_container_width' will be removed after 2025-12-31.
    sav, cncl = st.columns([3,1])
    if st.button("Save Transaction", type="primary", width='content'):
        if not vendor_name:
            st.warning("Please provide a Vendor Name before saving.")
            return

        uid = str(uuid.uuid4())
        try:
            conn = sqlite3.connect('invoices.db')
            c = conn.cursor()
            c.execute('''INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                (uid, vendor_name, address, str(inv_date), invoice_no, product, 
                 gst_no, qty, hsn_code, base_price, sgst_pct, cgst_pct, igst_pct, 
                 sgst_amt, cgst_amt, igst_amt, total_amt))
            conn.commit()
            conn.close()
            st.success(f"Invoice saved successfully! ID: {uid}")
            # st.balloons()
            reset_form() # Optional: Clear after saving too!
            st.rerun()

        except Exception as e:
            st.error(f"Database error: {e}")

    # Button outside the form to clear it manually
    cncl.button("Clear Form", on_click=reset_form)





