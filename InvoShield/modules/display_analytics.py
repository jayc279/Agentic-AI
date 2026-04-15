# "Category Breakdown" chart in the sidebar to show the percentage of spending per AI-labeled Category

"""
To visualize spending paterns, use Plotly - to provide interactive charts
1. Data Aggregration -> first extract metadata from ChromaDB to count how many invoices fall into each category
2. Implement Bar and PIE Charts -> add to sidebar -or- a dedicated "Ananlytics TAB"
"""

import plotly.express as px
import pandas as pd
import streamlit as st

def display_analytics():
    if st.session_state.vectostore:
        # 1. Fetch metadata from ChromaDB
        data = st.session_state.vectorstore.get()
        metadatas = data['metadatas']

        if not metadatas:
            st.info("No data available for charts.")
            return
    
        # 2. Convert to DataFrame
        # We ensure uniqueness as we don't double-count chunks of same file
        df_meta = pd.DataFrame(metadatas).drop_duplicates(subset=['sorce'])

        # 3. Process data for plotting
        category_counts = df_meta['category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Invoice Count']

        st.sidebar.divider()
        st.sidebar.subheader("Spending Breakdown")

        # --- PIE Chart ---
        fig_pie = px.pie(
            category_counts,
            values = 'Invoice Count',
            names = 'Category',
            title = 'Distribution by Volume',
            hole = 0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.sidebar.plotly_chart(fig_pie, use_container_width=True)

        # --- BAR Chart ---
        fig_bar = px.bar(
            category_counts,
            x = 'Category',
            y = 'Invoice Count',
            title = 'Invoices per Category',
            color = "Category",
            text_auto=True
        )

        # Clean-Up Layput
        fig_bar.update_layout(showlegend=False)
        st.sidebar.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.sidebar.info("Process invoices to see analytics")

# if __name__ == "__main__":
#     display_analytics()