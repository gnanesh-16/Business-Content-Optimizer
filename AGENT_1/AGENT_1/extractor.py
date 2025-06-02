import asyncio
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from typing import Dict, Any

async def fetch_article_text_async(url: str) -> Dict[str, Any]:
    """
    Asynchronously fetch article text from URL using crawl4ai with content filtering
    
    This function is responsible for extracting the main content from a documentation URL.
    It uses the crawl4ai library with specific configuration options to:
    1. Initialize a headless browser via the AsyncWebCrawler
    2. Apply content filtering to focus on the main article text (using PruningContentFilter)
    3. Convert the extracted content to markdown format
    4. Return the content along with metadata
    
    Args:
        url (str): The URL of the documentation to extract
        
    Returns:
        Dict[str, Any]: Dictionary containing the extracted content, title, URL, and success status
    """
    try:
        browser_config = BrowserConfig()
        
        # Create a pruning filter for better content extraction
        # This helps filter out navigation, headers, footers, and other non-content elements
        # The threshold value (0.45) determines how aggressive the pruning is
        prune_filter = PruningContentFilter(
            threshold=0.45,
            threshold_type="dynamic",
            min_word_threshold=5
        )
        
        # Set up markdown generator with content filtering
        # This converts the extracted HTML content to formatted markdown
        md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
        
        # Configure crawler with specific tags to exclude
        # This helps focus the extraction on the main content
        run_config = CrawlerRunConfig(
            excluded_tags=["nav", "footer", "header", "aside", "sidebar"],
            exclude_external_links=True,
            markdown_generator=md_generator
        )
        
        # Initialize and run the crawler to extract content
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            
            # Extract markdown content from the result
            if hasattr(result, 'markdown'):
                # Try to get fit_markdown first, fall back to raw markdown
                # fit_markdown contains content that has been filtered and processed
                markdown_content = ""
                if hasattr(result.markdown, 'fit_markdown') and result.markdown.fit_markdown:
                    markdown_content = result.markdown.fit_markdown
                else:
                    markdown_content = result.markdown
                
                return {
                    "content": markdown_content,
                    "title": result.title if hasattr(result, 'title') else "",
                    "url": url,
                    "success": True
                }
            else:
                return {
                    "content": "",
                    "title": "",
                    "url": url,
                    "success": False,
                    "error": "Failed to extract content"
                }
    except Exception as e:
        return {
            "content": "",
            "title": "",
            "url": url,
            "success": False,
            "error": str(e)
        }

def fetch_article_text(url: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for fetch_article_text_async
    
    This function serves as a convenient synchronous interface for the asynchronous
    content extraction function. It runs the async function in an event loop and
    returns the result.
    
    Args:
        url (str): The URL of the documentation to extract
        
    Returns:
        Dict[str, Any]: Dictionary containing the extracted content, title, URL, and success status
    """
    return asyncio.run(fetch_article_text_async(url))

def format_markdown_for_display(markdown: str, max_length: int = 500) -> str:
    """
    Format markdown for preview display
    
    This utility function creates a preview of the extracted markdown content
    by truncating it to a specified maximum length and adding an ellipsis.
    
    Args:
        markdown (str): The markdown content to format
        max_length (int): Maximum length of the preview
        
    Returns:
        str: Formatted markdown preview
    """
    if not markdown:
        return ""
        
    preview = markdown[:max_length] + "..." if len(markdown) > max_length else markdown
    return preview