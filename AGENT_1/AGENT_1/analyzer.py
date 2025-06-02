import textstat
import requests
import json
from typing import Dict, Any, Optional

class DocumentAnalyzer:
    """
    Analyze documents and provide improvement suggestions
    
    This class is responsible for analyzing documentation content using a combination
    of textstat for readability scoring and Large Language Models (LLMs) for deeper
    analysis. It provides comprehensive feedback on readability, structure, 
    completeness, and style adherence to help improve documentation quality.
    """
    
    def __init__(self, api_key: str, db_manager):
        """
        Initialize analyzer with API key and database manager
        
        Args:
            api_key (str): OpenRouter API key for accessing LLM services
            db_manager: Database manager instance for storing analysis results
        """
        self.api_key = api_key
        self.db_manager = db_manager
    
    def analyze_document(self, session_id: str, url: str, text: str) -> Dict[str, Any]:
        """
        Analyze document and return feedback on readability, structure, completeness, and style
        
        This is the main method that orchestrates the analysis process:
        1. Calculates readability scores using textstat
        2. Sends prompts to LLM for detailed analysis
        3. Compiles all results into a structured dictionary
        4. Saves results to databases via the db_manager
        
        Args:
            session_id (str): Unique identifier for this analysis session
            url (str): URL of the document being analyzed
            text (str): Extracted content of the document
            
        Returns:
            Dict[str, Any]: Structured analysis results with feedback in each category
        """
        try:
            # Calculate readability score using textstat's Flesch Reading Ease
            # Higher scores (90-100) indicate very easy to read text
            # Lower scores (0-30) indicate very difficult text
            readability_score = textstat.flesch_reading_ease(text)
            
            # Get detailed analysis from LLM by sending specialized prompts
            readability = self._analyze_readability(text, readability_score)
            structure = self._analyze_structure(text)
            completeness = self._analyze_completeness(text)
            style = self._analyze_style(text)
            
            # Compile all analysis results into a structured dictionary
            analysis_results = {
                "readability": {
                    "score": readability_score,
                    "analysis": readability
                },
                "structure": structure,
                "completeness": completeness,
                "style": style
            }
            
            # Save results to databases for future reference and retrieval
            # This uses both SQLite (for session data) and ChromaDB (for content)
            self.db_manager.save_analysis(session_id, url, text, analysis_results)
            
            return analysis_results
        
        except Exception as e:
            raise e
    
    def _analyze_readability(self, text: str, readability_score: float) -> str:
        """
        Analyze document readability
        
        Creates a specialized prompt for the LLM to analyze readability from a
        marketer's perspective, including the Flesch Reading Ease score and
        requesting specific, actionable improvement suggestions.
        
        Args:
            text (str): Document content to analyze
            readability_score (float): Calculated Flesch Reading Ease score
            
        Returns:
            str: Detailed readability analysis from the LLM
        """
        readability_prompt = f"""
        Analyze the readability of this documentation article for a non-technical marketer:
        1. The Flesch Reading Ease score is {readability_score}.
        2. Explain what this score means in the context of marketing documentation.
        3. Identify 3-4 specific sentences or paragraphs that affect readability.
        4. Provide specific, actionable suggestions to improve readability for marketers.
        
        Format your response with these specific markdown sections:
        ## Assessment
        [Your assessment of the readability and what the score means]
        
        ## Problem Areas
        [List the specific sentences or paragraphs that affect readability]
        
        ## Actionable Suggestions
        [List numbered, specific suggestions for improvement]
        
        Article: {text[:2000]}
        """
        return self._ask_llm(readability_prompt)
    
    def _analyze_structure(self, text: str) -> str:
        """
        Analyze document structure and flow
        
        Creates a specialized prompt for the LLM to analyze the document's
        organization, including headings, subheadings, paragraph length,
        and overall information flow.
        
        Args:
            text (str): Document content to analyze
            
        Returns:
            str: Detailed structure analysis from the LLM
        """
        structure_prompt = f"""
        Analyze the structure and flow of this documentation article:
        1. Evaluate the use of headings, subheadings, paragraph length, and lists.
        2. Assess if information flows logically and is easy to navigate.
        3. Identify 3-4 specific structural issues that could be improved.
        4. Provide specific, actionable suggestions for better structure and flow.
        
        Format your response with these specific markdown sections:
        ## Assessment
        [Your assessment of the overall structure and flow]
        
        ## Structural Elements
        [Analysis of headings, subheadings, paragraph length, lists, etc.]
        
        ## Flow Issues
        [Specific issues with information flow and navigation]
        
        ## Improvement Suggestions
        [Numbered, specific suggestions for improvement]
        
        Article: {text[:2000]}
        """
        return self._ask_llm(structure_prompt)
    
    def _analyze_completeness(self, text: str) -> str:
        """
        Analyze document completeness and examples
        
        Creates a specialized prompt for the LLM to analyze whether the document
        provides sufficient information and examples for understanding the topic.
        
        Args:
            text (str): Document content to analyze
            
        Returns:
            str: Detailed completeness analysis from the LLM
        """
        completeness_prompt = f"""
        Analyze the completeness of information and examples in this documentation article:
        1. Assess if there's enough detail to understand and implement the feature or concept.
        2. Evaluate the quality and quantity of examples provided.
        3. Identify 3-4 specific areas where more information or examples are needed.
        4. Provide specific, actionable suggestions for improving completeness.
        
        Format your response with these specific markdown sections:
        ## Assessment
        [Your assessment of the overall completeness]
        
        ## Information Gaps
        [Specific areas where more information is needed]
        
        ## Example Quality
        [Assessment of examples provided and what's missing]
        
        ## Improvement Suggestions
        [Numbered, specific suggestions for adding information or examples]
        
        Article: {text[:2000]}
        """
        return self._ask_llm(completeness_prompt)
    
    def _analyze_style(self, text: str) -> str:
        """
        Analyze document style guide adherence
        
        Creates a specialized prompt for the LLM to analyze whether the document
        follows Microsoft Style Guide principles for technical writing.
        
        Args:
            text (str): Document content to analyze
            
        Returns:
            str: Detailed style analysis from the LLM
        """
        style_prompt = f"""
        Analyze this article using Microsoft's Style Guide principles, focusing on:
        1. Voice and Tone: Is it customer-focused, clear, and concise?
        2. Clarity and Conciseness: Are there complex sentences or jargon that could be simplified?
        3. Action-oriented language: Does it guide the user effectively?
        4. Identify 3-4 specific style issues that should be addressed.
        5. Provide specific, actionable suggestions for improving style adherence.
        
        Format your response with these specific markdown sections:
        ## Assessment
        [Your overall assessment of style guide adherence]
        
        ## Voice and Tone
        [Analysis of customer focus, clarity, and conciseness]
        
        ## Language Issues
        [Specific examples of complex sentences, jargon, or passive voice]
        
        ## Improvement Suggestions
        [Numbered, specific suggestions for style improvements]
        
        Article: {text[:2000]}
        """
        return self._ask_llm(style_prompt)
    
    def _ask_llm(self, prompt: str) -> str:
        """
        Send prompt to LLM API and get response
        
        Handles the communication with the OpenRouter API to access LLM services.
        This method sets up the API request with the appropriate headers and
        handles response parsing and error handling.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: The LLM's response or an error message
        """
        # Check if API key is available
        if not self.api_key:
            return "Error: API key is not set. Please add your API key to the .env file as OPENROUTER_API_KEY."
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://moengage-doc-improver.streamlit.app",
            "X-Title": "MoEngage Doc Improver"
        }
        data = {
            "model": "meta-llama/llama-3.3-8b-instruct:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=headers, 
                                    json=data)
            
            # Check if the response is JSON
            try:
                response_json = response.json()
            except ValueError:
                return f"API Error: Non-JSON response - {response.text}"
            
            # Check for errors in the response
            if response.status_code != 200:
                return f"API Error: HTTP {response.status_code} - {response_json.get('error', response_json)}"
            
            if 'error' in response_json:
                return f"API Error: {response_json['error']}"
                
            if 'choices' not in response_json:
                return f"Unexpected API response format: {response_json}"
                
            return response_json["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error connecting to API: {str(e)}"