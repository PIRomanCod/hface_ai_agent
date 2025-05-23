from duckduckgo_search import DDGS
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from langchain_community.document_loaders import WikipediaLoader, ArxivLoader
import requests


@tool
def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query as string
        
    Returns:
        Search results
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found."
            return "\n\n".join([f"{r['title']}\n{r['body']}" for r in results])
    except Exception as e:
        return f"Error searching web: {str(e)}"


@tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for information.
    
    Args:
        query: Search query 
        
    Returns:
        Wikipedia article content
    """
    try:
        wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wiki.run(query)
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}" 

@tool
def arvix_search(query: str) -> str:
    """Search Arxiv for a query and return maximum 3 result.
    
    Args:
        query: The search query."""
    search_docs = ArxivLoader(query=query, load_max_docs=3).load()
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'page="{doc.metadata.get("page", "")}"/>\n{doc.page_content[:1000]}\n</Document>'
            for doc in search_docs
        ])
    return {"arvix_results": formatted_search_docs}


@tool
def search_wikipedia_info(query: str) -> str:
    """Fetches a short summary about a query from Wikipedia.
    Args: topic (str): The query to search for on Wikipedia.
    Returns: str: A summary or error message."""
    print(f"EXECUTING TOOL: get_wikipedia_info(topic='{query}')")
    try:
        search_url=f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
        search_response=requests.get(search_url, timeout=10); search_response.raise_for_status()
        search_data=search_response.json()
        if not search_data.get('query', {}).get('search', []): return f"No Wikipedia info for '{query}'."
        page_id=search_data['query']['search'][0]['pageid']
        content_url=f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids={page_id}&format=json"
        content_response=requests.get(content_url, timeout=10); content_response.raise_for_status()
        content_data=content_response.json(); extract=content_data['query']['pages'][str(page_id)]['extract']
        if len(extract)>500: extract=extract[:500]+"..."
        result=f"Wikipedia summary for '{query}':\n{extract}"
        print(f"-> Tool Result (Wikipedia): {result[:100]}...")
        return result
    except Exception as e: print(f"❌ Error in get_wikipedia_info: {e}"); traceback.print_exc(); return f"Error wiki: {e}"
    