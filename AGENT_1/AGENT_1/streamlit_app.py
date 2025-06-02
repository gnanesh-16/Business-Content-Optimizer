import os
import uuid
import streamlit as st
from dotenv import load_dotenv

# Import custom modules
from database import init_databases
from extractor import fetch_article_text, format_markdown_for_display
from analyzer import DocumentAnalyzer
from ui import render_home_page, render_history_page, render_results_page, render_sidebar

# Load environment variables
# The .env file contains the OpenRouter API key needed for LLM access
load_dotenv(dotenv_path="/workspaces/codespaces-blank/AGENT_1/.env")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize database manager
# This creates the necessary database connections and tables for storing analysis results
db_manager = init_databases()

# Initialize document analyzer
# The analyzer uses the OpenRouter API to access LLM services for document analysis
analyzer = DocumentAnalyzer(OPENROUTER_API_KEY, db_manager)

# App configuration
# Set up the Streamlit application with a wide layout and expanded sidebar
st.set_page_config(
    page_title="Documentation Improver",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
# This maintains the application state across user interactions
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'selected_session' not in st.session_state:
    st.session_state.selected_session = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'article_text' not in st.session_state:
    st.session_state.article_text = None

# Navigation handlers
# These functions control page navigation when the user clicks on different UI elements
def go_home():
    st.session_state.current_page = "home"
    st.session_state.selected_session = None

def go_history():
    st.session_state.current_page = "history"

def load_session(session_id):
    st.session_state.selected_session = session_id
    st.session_state.current_page = "results"
    st.rerun()

navigation_handlers = {
    "go_home": go_home,
    "go_history": go_history,
    "load_session": load_session
}

# URL analysis handler
# This function orchestrates the document extraction and analysis process
def analyze_url(url):
    # Generate a unique session ID using UUID
    # This ID links the analysis results in SQLite with the document content in ChromaDB
    session_id = str(uuid.uuid4())
    
    with st.spinner("🔍 Extracting article content..."):
        try:
            # Extract article text using crawl4ai
            extraction_result = fetch_article_text(url)
            
            if extraction_result["success"]:
                article_text = extraction_result["content"]
                st.session_state.article_text = article_text
                
                # Display a collapsible preview of the extracted content
                with st.expander("Extracted Content Preview", expanded=False):
                    st.markdown(format_markdown_for_display(article_text, max_length=1500))
                
                # Proceed directly to analysis without requiring confirmation
                with st.spinner("🧠 Analyzing document..."):
                    # Analyze the document using the DocumentAnalyzer
                    # This sends the content to the LLM for detailed analysis
                    analysis_result = analyzer.analyze_document(session_id, url, article_text)
                    
                    # Store results in session state for display
                    st.session_state.selected_session = session_id
                    st.session_state.analysis_results = {
                        "session_id": session_id,
                        "url": url,
                        "readability": analysis_result["readability"]["analysis"],
                        "readability_score": analysis_result["readability"]["score"],
                        "structure": analysis_result["structure"],
                        "completeness": analysis_result["completeness"],
                        "style": analysis_result["style"],
                        "article_text": article_text  # Store the article text for reference
                    }
                    
                    # Go to results page to display the analysis
                    st.session_state.current_page = "results"
                    st.rerun()
            else:
                st.error(f"Failed to extract content: {extraction_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Render sidebar
# This displays navigation options, API status, and recent sessions
render_sidebar(
    navigation_handlers=navigation_handlers,
    api_key=OPENROUTER_API_KEY,
    sessions=db_manager.get_recent_sessions()
)

# Render current page based on the session state
# This controls which page is displayed to the user
if st.session_state.current_page == "home":
    render_home_page(analyze_url)
elif st.session_state.current_page == "history":
    render_history_page(
        all_sessions=db_manager.get_all_sessions(),
        view_session_handler=load_session
    )
elif st.session_state.current_page == "results":
    if st.session_state.selected_session:
        session_data = db_manager.get_session(st.session_state.selected_session)
        render_results_page(session_data=session_data)
    elif st.session_state.analysis_results:
        render_results_page(analysis_results=st.session_state.analysis_results)
    else:
        st.error("No results to display")
        st.button("Return to Home", on_click=go_home)
