"""Small, shared presentation elements for the explorer's Streamlit pages."""
from html import escape

import streamlit as st


def page_heading(number: str, title: str) -> None:
    st.html(
        f'<h1 class="lab-heading"><span class="page-number">{escape(number)}</span>'
        f'<span>{escape(title)}</span></h1>'
    )
