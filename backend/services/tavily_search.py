from tavily import TavilyClient
from config.settings import settings
import httpx
from httpx import TimeoutException
import json
import re
import asyncio
from typing import Optional

# Global client instance - initialized lazily
_client: Optional[TavilyClient] = None

def get_tavily_client() -> Optional[TavilyClient]:
    """Get Tavily client instance with lazy initialization."""
    global _client
    if _client is None and settings.tavily_api_key:
        try:
            _client = TavilyClient(api_key=settings.tavily_api_key)
        except Exception as e:
            print(f"Failed to initialize Tavily client: {e}")
            return None
    return _client

async def perform_web_search_async(query: str, http_client: httpx.AsyncClient = None, model_name: str = "qwen3"):
    # Get Tavily client
    client = get_tavily_client()
    if not client:
        return {
            "query": query,
            "results": [],
            "error": "Tavily search service is not available (API key not configured)"
        }
    
    # Enhance query for better results
    enhanced_query = enhance_search_query(query)
    
    # Enhanced search with better parameters for content quality
    response = client.search(
        query=enhanced_query, 
        max_results=15,  # Get more results to filter from
        include_raw_content=True,  # Get more detailed content
        search_depth="advanced",  # Use advanced search for better results
        exclude_domains=["google.com", "bing.com", "yahoo.com", "facebook.com", "twitter.com", "instagram.com", "tiktok.com", "pinterest.com"],  # Exclude low-content sites
        # Remove include_domains to get more diverse results
    )
    
    # Create structured results with enhanced content
    structured_results = {
        "query": query,
        "results": []
    }
    
    for i, result in enumerate(response["results"]):
        # Get more content - try raw_content first, then content
        content = result.get('raw_content', '') or result.get('content', '')
        
        # Filter out low-quality content (navigation pages, etc.)
        if is_low_quality_content(content, result.get('title', '')):
            continue
            
        # Clean and process content
        content = clean_content(content)
        
        # If content is too long, truncate it to ~12000 chars to get more content
        if len(content) > 12000:
            content = content[:12000] + "...[content truncated]"
        
        # Only add results with substantial content (reduced threshold for more sources)
        if len(content.strip()) > 20:  # Even further reduced minimum content length
            structured_results["results"].append({
                "title": result.get('title', 'No title'),
                "url": result.get('url', ''),
                "content": content,
                "score": result.get('score', 0),
                "published_date": result.get('published_date', ''),
                "index": len(structured_results["results"]) + 1
            })
    
    # Process results through LLM for better context (moved outside the loop)
    try:
        processed_results = await process_search_results_with_llm_async(query, structured_results, http_client, model_name)
        return processed_results
    except Exception as e:
        print(f"Error processing search results with LLM: {e}")
        # Return original results if LLM processing fails
        return structured_results

async def process_search_results_with_llm_async(query: str, search_results: dict, http_client: httpx.AsyncClient = None, model_name: str = "qwen3"):
    """Process search results through LLM to create better summaries and context."""
    
    # If no search results, return early
    if not search_results.get('results'):
        search_results['processing_status'] = 'no_results'
        search_results['processing_error'] = 'No search results to process'
        return search_results
    
    # Create a simpler prompt for faster processing
    results_text = "\n\n".join([
        f"Title: {result['title']}\nContent: {result['content'][:600]}..."  # Increased content length to 600
        for result in search_results['results'][:5]  # Only process first 5 results
    ])
    
    # Create source links for reference
    source_links = "\n".join([
        f"[{i+1}] {result['title']} - {result['url']}"
        for i, result in enumerate(search_results['results'])
    ])
    
    prompt = f"""Summarize for "{query}": {results_text}

Key points only. Sources: {source_links}"""
    
    try:
        # Use provided http_client or create a new one with increased timeout
        client = http_client or httpx.AsyncClient(timeout=120.0)  # Increased timeout for larger content
        
        # Try different models in order of preference
        model_options = [
            "qwen3-32K-Context",  # Try this first as it's likely available
            "deepseek-r1-0528-qwen3-8b",
            "qwen3-235b-a22b-q8_0-128K"
        ]
        
        success = False
        for model in model_options:
            try:
                print(f"Trying model: {model}")
                
                # Send request with much shorter timeout
                response = await client.post(
                    f"{settings.gpustack_api_base}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.gpustack_api_token or ''}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "Summarize search results briefly."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1000,  # Much shorter for faster processing
                        "temperature": 0.3,
                        "stream": False
                    },
                    timeout=90.0  # Increased timeout per attempt for thinking models
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        llm_summary = data['choices'][0]['message']['content']
                        
                        # Add sources section if not already included
                        if 'Sources:' not in llm_summary:
                            llm_summary += f"\n\n---\n\n**Sources:**\n{source_links}"
                        
                        # Add the LLM-processed summary to the results
                        search_results['llm_summary'] = llm_summary
                        search_results['processing_status'] = 'success'
                        print(f"LLM processing successful with model {model} for query: {query}")
                        success = True
                        break
                    else:
                        print(f"Model {model} returned no response")
                else:
                    print(f"Model {model} returned status {response.status_code}")
                    
            except httpx.TimeoutException:
                print(f"Model {model} timed out")
                continue
            except Exception as e:
                print(f"Error with model {model}: {e}")
                continue
        
        # Close client if we created it
        if not http_client:
            await client.aclose()
        
        if not success:
            # If all models failed, create a simple summary manually
            print(f"All models failed, creating manual summary for query: {query}")
            manual_summary = f"""🔍 Search Results for "{query}":\n\n{chr(10).join([f"• {result['title']}: {result['content'][:600]}..." for result in search_results['results'][:5]])}\n\n📚 Sources:\n{source_links}"""
            
            search_results['llm_summary'] = manual_summary
            search_results['processing_status'] = 'manual_fallback'
            search_results['processing_error'] = 'LLM processing failed, using manual summary'
            
    except Exception as e:
        print(f"Error in LLM processing for query '{query}': {e}")
        search_results['processing_status'] = 'error'
        search_results['processing_error'] = str(e)
    
    return search_results

def is_low_quality_content(content: str, title: str) -> bool:
    """Check if content is low quality (navigation, empty, etc.)"""
    if not content or len(content.strip()) < 20:  # Much more lenient
        return True
    
    # Check for navigation-heavy content
    nav_indicators = [
        "Settings", "Help", "Privacy", "Terms", "About", 
        "Navigation", "Menu", "Search", "Login", "Sign in",
        "Subscribe", "Newsletter", "Follow us", "Social media",
        "Cookie policy", "Advanced search", "Clear"
    ]
    
    # Count navigation indicators
    nav_count = sum(1 for indicator in nav_indicators if indicator.lower() in content.lower())
    
    # Much more lenient filtering
    content_words = len(content.split())
    if nav_count > 12 or (content_words < 30 and nav_count > 5):  # Much more lenient
        return True
    
    # Check for generic page titles (more lenient)
    generic_titles = ["google", "search", "news", "homepage", "home page"]
    if any(generic in title.lower() for generic in generic_titles) and len(content.strip()) < 100:
        return True
    
    return False

def clean_content(content: str) -> str:
    """Clean and improve content quality"""
    if not content:
        return ""
    
    # Remove excessive whitespace and newlines
    content = re.sub(r'\n\s*\n', '\n', content)
    content = re.sub(r'\s+', ' ', content)
    
    # Remove common navigation elements
    nav_patterns = [
        r'\*\s+[A-Za-z\s]+\n',  # Bullet points that are likely nav
        r'\[.*?\]\(.*?\)',       # Markdown links that are often nav
        r'Settings\s*\*.*?\n',   # Settings lines
        r'Help\s*\*.*?\n',      # Help lines
    ]
    
    for pattern in nav_patterns:
        content = re.sub(pattern, '', content)
    
    # Extract meaningful sentences
    sentences = content.split('.')
    meaningful_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        # Keep sentences that are substantial and informative
        if (len(sentence) > 20 and 
            not any(nav_word in sentence.lower() for nav_word in ["click", "menu", "navigation", "settings", "help"])):
            meaningful_sentences.append(sentence)
    
    return '. '.join(meaningful_sentences[:10])  # Limit to 10 meaningful sentences

def enhance_search_query(query: str) -> str:
    """Enhance search query for better results"""
    query = query.strip().lower()
    
    # Add context for news/current events queries
    news_keywords = ['news', 'today', 'latest', 'current', 'recent', 'market', 'stock']
    sports_keywords = ['soccer', 'football', 'sports', 'match', 'game', 'team', 'player']
    weather_keywords = ['weather', 'temperature', 'forecast', 'climate']
    
    # Enhanced weather queries
    if any(keyword in query for keyword in weather_keywords):
        return f"{query} current conditions forecast multiple sources"
    
    # Enhanced sports queries
    if any(keyword in query for keyword in sports_keywords):
        return f"{query} latest news updates results scores multiple sources"
    
    # Add context for news/current events queries
    if any(keyword in query for keyword in news_keywords):
        if 'stock' in query or 'market' in query:
            return f"{query} financial news articles latest multiple sources"
        else:
            return f"{query} news articles latest updates multiple sources"
    
    # For general queries, add context for better content
    return f"{query} comprehensive information articles latest multiple sources"

# Backward compatibility - sync wrapper
def perform_web_search(query: str):
    """Synchronous wrapper for backward compatibility"""
    return asyncio.get_event_loop().run_until_complete(
        perform_web_search_async(query)
    )

