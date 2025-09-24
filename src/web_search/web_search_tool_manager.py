"""
Web Search Tool Manager for WhisperEngine

Integrates web search capabilities with the LLM tool calling system,
enabling characters to search for current events and real-time information.
Uses DuckDuckGo's free API for privacy-focused web search.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    """Represents a web search result"""
    title: str
    snippet: str
    url: str
    source: str
    relevance_score: float = 0.0


@dataclass
class WebSearchAction:
    """Represents a web search action taken by the LLM"""
    query: str
    search_type: str
    timestamp: datetime
    results_count: int
    success: bool
    error_message: Optional[str] = None
    results: Optional[List[WebSearchResult]] = field(default_factory=list)


class WebSearchToolManager:
    """Web search tools for LLM tool calling - enables current events awareness"""
    
    def __init__(self):
        self.tools = self._initialize_search_tools()
        self.search_history: List[WebSearchAction] = []
        self.session = requests.Session()
        # Set up session with reasonable defaults
        self.session.headers.update({
            'User-Agent': 'WhisperEngine-Bot/1.0 (Educational AI Assistant)'
        })
    
    def _initialize_search_tools(self) -> List[Dict[str, Any]]:
        """Initialize web search tools for LLM tool calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_current_events",
                    "description": "Search the web for current events, news, and recent information. Use when user asks about recent developments, current news, or up-to-date information not in memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for current events or news (e.g., 'AI developments 2025', 'latest climate change news')"
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 8,
                                "default": 5,
                                "description": "Maximum number of search results to return"
                            },
                            "search_focus": {
                                "type": "string",
                                "enum": ["news", "general", "recent", "factual"],
                                "default": "news",
                                "description": "Focus of the search - news for current events, recent for latest info, factual for verification"
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "verify_current_information",
                    "description": "Verify or fact-check information by searching current sources. Use when user asks to verify claims or check if information is still accurate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "claim_to_verify": {
                                "type": "string",
                                "description": "The claim, fact, or information to verify against current sources"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about what specifically needs verification"
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 2,
                                "maximum": 6,
                                "default": 4,
                                "description": "Number of sources to check for verification"
                            }
                        },
                        "required": ["claim_to_verify"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute a web search tool based on LLM tool call"""
        try:
            if tool_name == "search_current_events":
                return await self._search_current_events(parameters, user_id)
            elif tool_name == "verify_current_information":
                return await self._verify_current_information(parameters, user_id)
            else:
                return {"error": f"Unknown web search tool: {tool_name}"}
                
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            logger.error("Error executing web search tool %s: %s", tool_name, e)
            return {"error": f"Web search failed: {str(e)}"}
    
    async def _search_current_events(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Search for current events and news"""
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        search_focus = params.get("search_focus", "news")
        
        logger.info("Searching current events for user %s: '%s'", user_id, query)
        
        # Enhance query based on focus
        enhanced_query = self._enhance_query_for_current_events(query, search_focus)
        
        logger.info("🌐 Performing web search for current events - Query: '%s' -> Enhanced: '%s'", 
                   query, enhanced_query)
        
        # Perform search
        search_results = await self._perform_duckduckgo_search(enhanced_query, max_results)
        
        # Log the action
        action = WebSearchAction(
            query=enhanced_query,
            search_type="current_events",
            timestamp=datetime.now(),
            results_count=len(search_results),
            success=len(search_results) > 0,
            results=search_results
        )
        self.search_history.append(action)
        
        if not search_results:
            logger.warning("🔍 No current events results found for query: '%s'", query)
            return {
                "success": False,
                "message": f"No current events found for '{query}'. The information might be too recent or specific.",
                "query_used": enhanced_query,
                "suggestion": "Try rephrasing with more general terms or check back later."
            }
        
        return {
            "success": True,
            "query": query,
            "enhanced_query": enhanced_query,
            "results_count": len(search_results),
            "results": [
                {
                    "title": result.title,
                    "snippet": result.snippet,
                    "source": result.source,
                    "url": result.url
                }
                for result in search_results
            ],
            "search_type": "current_events",
            "timestamp": action.timestamp.isoformat()
        }
    
    async def _verify_current_information(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Verify information against current sources"""
        claim = params.get("claim_to_verify", "")
        context = params.get("context", "")
        max_results = params.get("max_results", 4)
        
        logger.info("Verifying information for user %s: '%s'", user_id, claim)
        
        # Create verification query
        verification_query = f"{claim} fact check verification {context}".strip()
        
        logger.info("🔍 Performing information verification - Claim: '%s' -> Query: '%s'", 
                   claim, verification_query)
        
        # Perform search
        search_results = await self._perform_duckduckgo_search(verification_query, max_results)
        
        # Log the action
        action = WebSearchAction(
            query=verification_query,
            search_type="verification",
            timestamp=datetime.now(),
            results_count=len(search_results),
            success=len(search_results) > 0,
            results=search_results
        )
        self.search_history.append(action)
        
        if not search_results:
            return {
                "success": False,
                "message": f"Could not find current sources to verify: '{claim}'",
                "claim": claim,
                "suggestion": "The claim might be too specific, new, or require specialized sources."
            }
        
        return {
            "success": True,
            "claim_verified": claim,
            "verification_query": verification_query,
            "sources_found": len(search_results),
            "verification_sources": [
                {
                    "title": result.title,
                    "snippet": result.snippet,
                    "source": result.source,
                    "url": result.url
                }
                for result in search_results
            ],
            "verification_note": "Cross-reference these sources to verify the claim",
            "timestamp": action.timestamp.isoformat()
        }
    
    def _enhance_query_for_current_events(self, query: str, search_focus: str) -> str:
        """Enhance search query - DuckDuckGo works better with general topics than news queries"""
        # Remove news-specific terms that make DuckDuckGo return empty results
        query_cleaned = query.replace("latest news", "").replace("recent news", "").replace("news", "")
        query_cleaned = query_cleaned.replace("latest", "").replace("recent", "").replace("developments", "")
        query_cleaned = query_cleaned.replace("2025", "").replace("2024", "").strip()
        
        # Use general topic terms that work better with DuckDuckGo
        if "AI" in query or "artificial intelligence" in query.lower():
            return "artificial intelligence"
        elif "machine learning" in query.lower():
            return "machine learning"
        elif "OpenAI" in query or "ChatGPT" in query:
            return "OpenAI GPT"
        else:
            return query_cleaned if query_cleaned else query
    
    async def _perform_duckduckgo_search(self, query: str, max_results: int) -> List[WebSearchResult]:
        """Perform web search using DuckDuckGo's instant answer API"""
        try:
            # DuckDuckGo Instant Answer API (free, no API key needed)
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1',
                'no_redirect': '1'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process instant answer if available
            if data.get('AbstractText'):
                results.append(WebSearchResult(
                    title=data.get('Heading', 'DuckDuckGo Instant Answer'),
                    snippet=data.get('AbstractText', ''),
                    url=data.get('AbstractURL', ''),
                    source=data.get('AbstractSource', 'DuckDuckGo'),
                    relevance_score=1.0
                ))
            
            # Process related topics
            for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(WebSearchResult(
                        title=topic.get('FirstURL', '').split('/')[-1].replace('_', ' ').title(),
                        snippet=topic.get('Text', ''),
                        url=topic.get('FirstURL', ''),
                        source='Wikipedia/DuckDuckGo',
                        relevance_score=0.8
                    ))
            
            # If we still need more results, try the web search fallback
            if len(results) < max_results // 2:
                fallback_results = await self._fallback_web_search(query, max_results - len(results))
                results.extend(fallback_results)
            
            logger.info("DuckDuckGo search for '%s' returned %d results", query, len(results))
            return results[:max_results]
            
        except requests.RequestException as e:
            logger.warning("DuckDuckGo search failed for '%s': %s", query, e)
            # Try fallback search
            return await self._fallback_web_search(query, max_results)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse DuckDuckGo response for '%s': %s", query, e)
            return await self._fallback_web_search(query, max_results)
        except (ValueError, KeyError) as e:
            logger.error("Unexpected error in DuckDuckGo search for '%s': %s", query, e)
            return []
    
    async def _fallback_web_search(self, query: str, max_results: int) -> List[WebSearchResult]:
        """Fallback web search using HTML scraping (simple approach)"""
        try:
            # Simple fallback using DuckDuckGo HTML (less reliable but free)
            search_url = "https://duckduckgo.com/html/"
            params = {'q': query}
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Very basic HTML parsing - in a real implementation you'd use BeautifulSoup
            # For now, just return a helpful result explaining search limitations  
            # Note: max_results is intentionally unused as this is a simple fallback
            return [WebSearchResult(
                title=f"Search attempted: {query}",
                snippet=f"I searched for information about '{query}' but couldn't find recent news results. My web search uses DuckDuckGo's free API which provides general knowledge but not current news. For specific topics, try asking about general concepts rather than recent developments.",
                url="https://duckduckgo.com",
                source="DuckDuckGo",
                relevance_score=0.5
            )]
            
        except (requests.RequestException, ValueError) as e:
            logger.error("Fallback web search failed for '%s': %s", query, e)
            return []
    
    def get_search_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history"""
        # Note: user_id filtering could be implemented in the future for per-user history
        _ = user_id  # Unused parameter for now
        recent_searches = self.search_history[-limit:]
        return [
            {
                "query": action.query,
                "search_type": action.search_type,
                "timestamp": action.timestamp.isoformat(),
                "results_count": action.results_count,
                "success": action.success
            }
            for action in recent_searches
        ]
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for web search tools"""
        total_searches = len(self.search_history)
        successful_searches = sum(1 for action in self.search_history if action.success)
        
        search_types = {}
        for action in self.search_history:
            search_types[action.search_type] = search_types.get(action.search_type, 0) + 1
        
        return {
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "success_rate": successful_searches / total_searches if total_searches > 0 else 0,
            "search_types": search_types,
            "tools_available": len(self.tools)
        }