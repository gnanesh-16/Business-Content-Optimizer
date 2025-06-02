import streamlit as st
from typing import Dict, Any

def render_home_page(analyze_handler):
    """
    Render the home page UI
    
    This function creates the user interface for the home page, which includes:
    - A title and description of the application
    - A text input for entering a documentation URL
    - An "Analyze" button to trigger the analysis process
    
    Args:
        analyze_handler: Function to call when the Analyze button is clicked
    """
    st.title("📘 AI-Powered Documentation Improver")
    
    st.write("Enter a documentation URL below to analyze and improve its readability, structure, completeness, and style.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input("Enter a documentation article URL:", 
                           placeholder="https://help.moengage.com/hc/en-us/articles/...")
    with col2:
        analyze_button = st.button("Analyze", type="primary", use_container_width=True)

    # Process URL when Analyze button is clicked
    if analyze_button and url:
        analyze_handler(url)
    elif analyze_button and not url:
        st.warning("Please enter a URL to analyze.")

def render_history_page(all_sessions, view_session_handler):
    """
    Render the history page UI
    
    This function creates the user interface for the history page, which displays:
    - A table of all past analysis sessions
    - A dropdown selector for choosing a session to view
    - A button to load the selected session
    
    Args:
        all_sessions: List of all analysis session data from the database
        view_session_handler: Function to call when viewing a session's details
    """
    st.title("📊 Analysis History")
    
    if all_sessions:
        # Create a dataframe for better display
        import pandas as pd
        sessions_df = pd.DataFrame([
            {"ID": s[0][:8], "URL": s[1], "Date": s[6]} 
            for s in all_sessions
        ])
        
        # Display as a table
        st.dataframe(
            sessions_df,
            column_config={
                "ID": "Session ID",
                "URL": st.column_config.LinkColumn("URL"),
                "Date": "Date"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Selection for viewing details
        selected_id = st.selectbox("Select a session to view", 
                                  options=[s[0] for s in all_sessions],
                                  format_func=lambda x: f"{x[:8]} - {next((s[1] for s in all_sessions if s[0] == x), '')}")
        
        if selected_id:
            if st.button("View Details", type="primary"):
                view_session_handler(selected_id)
    else:
        st.info("No analysis history found")

def render_results_page(session_data: Dict[str, Any] = None, analysis_results: Dict[str, Any] = None):
    """
    Render the results page UI
    
    This function creates the user interface for the results page, which displays:
    - The analysis results in tabbed sections (readability, structure, completeness, style)
    - A full report tab with all results
    - Download options for the analysis report
    
    Args:
        session_data: Session data from the database (for viewing past sessions)
        analysis_results: Analysis results from the current session
    """
    if session_data:
        session_id = session_data[0]
        url = session_data[1]
        readability = session_data[2]
        structure = session_data[3]
        completeness = session_data[4] 
        style = session_data[5]
        
        # Display results
        display_results(session_id, url, readability, structure, completeness, style)
        
    elif analysis_results:
        # Display results from current analysis
        results = analysis_results
        
        display_results(
            results['session_id'], 
            results['url'],
            results['readability'],
            results['structure'],
            results['completeness'],
            results['style'],
            results.get('readability_score')
        )
    else:
        st.error("No results to display")
        st.button("Return to Home", on_click=lambda: setattr(st.session_state, 'current_page', 'home'))

def display_results(session_id, url, readability, structure, completeness, style, readability_score=None):
    """
    Helper function to display analysis results
    
    This function formats and displays the analysis results in a tabbed interface:
    - Each analysis category has its own tab
    - Results are displayed in expandable sections based on markdown headers
    - The full report tab includes all results and download options
    
    Args:
        session_id: Unique identifier for the analysis session
        url: URL of the analyzed document
        readability: Readability analysis from the LLM
        structure: Structure analysis from the LLM
        completeness: Completeness analysis from the LLM
        style: Style analysis from the LLM
        readability_score: Optional Flesch Reading Ease score
    """
    st.title("Analysis Results")
    st.subheader(f"URL: {url}")
    st.caption(f"Session ID: {session_id}")
    
    # Show results in tabs
    tabs = st.tabs(["📖 Readability", "🔄 Structure", "📋 Completeness", "✒️ Style", "📑 Full Report"])
    
    with tabs[0]:
        st.subheader("🔍 Readability for Marketers")
        
        # Readability score with visual indicator
        if readability_score is not None:
            score_color = "green" if readability_score > 60 else "orange" if readability_score > 30 else "red"
            score_label = "Easy to read" if readability_score > 60 else "Moderately difficult" if readability_score > 30 else "Difficult to read"
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric(label="Flesch Reading Ease", value=f"{readability_score:.1f}")
            with col2:
                st.markdown(f"<div style='background-color: {score_color}; padding: 10px; border-radius: 5px; color: white;'><strong>{score_label}</strong></div>", unsafe_allow_html=True)
        
        # Split the readability feedback into sections if it contains headers
        if "## Assessment" in readability or "### Assessment" in readability:
            sections = readability.split("##")
            for section in sections:
                if section.strip():
                    section_title = section.split('\n')[0].strip()
                    section_content = '\n'.join(section.split('\n')[1:]).strip()
                    if section_title and section_content:
                        with st.expander(f"{section_title}", expanded=True):
                            st.markdown(section_content)
        else:
            st.markdown(readability)
        
    with tabs[1]:
        st.subheader("📐 Structure and Flow")
        
        # Split the structure feedback into sections if it contains headers
        if "## Assessment" in structure or "### Assessment" in structure:
            sections = structure.split("##")
            for section in sections:
                if section.strip():
                    section_title = section.split('\n')[0].strip()
                    section_content = '\n'.join(section.split('\n')[1:]).strip()
                    if section_title and section_content:
                        with st.expander(f"{section_title}", expanded=True):
                            st.markdown(section_content)
        else:
            st.markdown(structure)
        
    with tabs[2]:
        st.subheader("📖 Completeness of Information")
        
        # Split the completeness feedback into sections if it contains headers
        if "## Assessment" in completeness or "### Assessment" in completeness:
            sections = completeness.split("##")
            for section in sections:
                if section.strip():
                    section_title = section.split('\n')[0].strip()
                    section_content = '\n'.join(section.split('\n')[1:]).strip()
                    if section_title and section_content:
                        with st.expander(f"{section_title}", expanded=True):
                            st.markdown(section_content)
        else:
            st.markdown(completeness)
        
    with tabs[3]:
        st.subheader("🎯 Style Guide Adherence")
        
        # Split the style feedback into sections if it contains headers
        if "## Assessment" in style or "### Assessment" in style:
            sections = style.split("##")
            for section in sections:
                if section.strip():
                    section_title = section.split('\n')[0].strip()
                    section_content = '\n'.join(section.split('\n')[1:]).strip()
                    if section_title and section_content:
                        with st.expander(f"{section_title}", expanded=True):
                            st.markdown(section_content)
        else:
            st.markdown(style)
        
    with tabs[4]:
        st.subheader("📑 Comprehensive Analysis Report")
        
        # Generate markdown report
        report_md = f"""
        # Documentation Analysis Report

        ## 📌 Article: [{url}]({url})
        
        ### 📖 Readability for Marketers
        {readability}
        
        ### 🔄 Structure and Flow
        {structure}
        
        ### 📋 Completeness of Information
        {completeness}
        
        ### 🎯 Style Guide Adherence
        {style}
        """
        st.markdown(report_md)
        
        # Provide download options
        import json
        
        # Provide download as markdown
        report_download = report_md.encode()
        st.download_button(
            label="📥 Download Report as Markdown",
            data=report_download,
            file_name=f"doc_analysis_{session_id[:8]}.md",
            mime="text/markdown"
        )
        
        # Generate JSON report
        report_json = {
            "url": url,
            "session_id": session_id,
            "analysis": {
                "readability": readability,
                "structure": structure,
                "completeness": completeness,
                "style": style
            }
        }
        
        # Provide download as JSON
        json_download = json.dumps(report_json, indent=2).encode()
        st.download_button(
            label="📥 Download Report as JSON",
            data=json_download,
            file_name=f"doc_analysis_{session_id[:8]}.json",
            mime="application/json"
        )

def render_sidebar(navigation_handlers, api_key, sessions):
    """
    Render the sidebar UI
    
    This function creates the user interface for the sidebar, which includes:
    - Navigation buttons for different pages
    - API connection status
    - List of recent analysis sessions
    
    Args:
        navigation_handlers: Dictionary of functions for handling navigation actions
        api_key: OpenRouter API key for displaying connection status
        sessions: List of recent analysis sessions from the database
    """
    with st.sidebar:
        st.title("📚 Documentation Assistant")
        
        # Navigation
        st.subheader("Navigation")
        if st.button("🏠 Home", use_container_width=True):
            navigation_handlers["go_home"]()
        if st.button("📊 History", use_container_width=True):
            navigation_handlers["go_history"]()
        
        # API Key Status
        st.divider()
        if api_key:
            st.success(f"✅ API Connected: {api_key[:5]}...")
        else:
            st.error("❌ API Not Connected")
        
        # Recent Sessions
        st.divider()
        st.subheader("Recent Sessions")
        
        if sessions:
            for session in sessions:
                session_id = session[0]
                url = session[1]
                
                # Format for display
                display_url = url[:30] + "..." if len(url) > 30 else url
                
                # Create an expander for each session
                with st.expander(f"**{display_url}**"):
                    st.caption(f"ID: {session_id[:8]}")
                    if st.button("Load Session", key=f"load_{session_id}"):
                        navigation_handlers["load_session"](session_id)
        else:
            st.info("No analysis history yet")