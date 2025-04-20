from mcp.server.fastmcp import FastMCP
import httpx
import time
import asyncio
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import os
import sys
import io
from load_dotenv import load_dotenv
import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from src.utils.utils import register_mcp_router
from src.utils.setup_logger import get_logger

load_dotenv()

api_key = os.getenv("BRAVE_API_KEY")

if not api_key:
    raise ValueError("BRAVE_API_KEY environment variable required")

logger = get_logger("brave_server")

mode = os.environ.get("MODE", "local")

print(f"Running in {mode} mode")

if mode == "local":
    transport = "stdio"
else:
    transport = "sse"

app = FastAPI()


class RateLimitError(Exception):
    pass

@dataclass
class RateLimit:
    per_second: int = 1
    per_month: int = 2000
    _requests: Dict[str, int] = None
    _last_reset: float = 0.0

    def __post_init__(self):
        self._requests = {"second": 0, "month": 0}
        self._last_reset = time.time()

    def check(self):
        now = time.time()
        if now - self._last_reset > 1:
            self._requests["second"] = 0
            self._last_reset = now
        
        if (self._requests["second"] >= self.per_second or 
            self._requests["month"] >= self.per_month):
            raise RateLimitError("Rate limit exceeded")
        
        self._requests["second"] += 1
        self._requests["month"] += 1

class BraveSearchServer:
    def __init__(self, api_key: str):
        # Configure stdout for UTF-8
        if sys.platform == 'win32':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            
        self.mcp = FastMCP(
            "brave",
            dependencies=["httpx", "asyncio"]
        )
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1"
        self.rate_limit = RateLimit()
        self._client = None
        self._setup_tools()

    def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip"
                },
                timeout=30.0
            )
        return self._client

    async def _get_web_results(self, query: str, min_results: int) -> List[Dict]:
        """Fetch web results with pagination until minimum count is reached"""
        client = self.get_client()
        self.rate_limit.check()
        
        try:
            # Make a single request with the maximum allowed count
            response = await client.get(
                f"{self.base_url}/web/search",
                params={
                    "q": query,
                    "count": min_results
                }
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("web", {}).get("results", [])
            return results
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                # If we get a 422, try with a smaller count
                response = await client.get(
                    f"{self.base_url}/web/search",
                    params={
                        "q": query,
                        "count": 10  # Fall back to smaller count
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("web", {}).get("results", [])
            raise  # Re-raise other HTTP errors

    def _format_web_results(self, data: Dict, min_results: int = 10) -> str:
        """Format web search results with enhanced information"""
        results = []
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results[:max(min_results, len(web_results))]:
            # Strip or replace any potential Unicode characters
            title = result.get('title', 'N/A').encode('ascii', 'replace').decode()
            desc = result.get('description', 'N/A').encode('ascii', 'replace').decode()
            
            formatted_result = [
                f"Title: {title}",
                f"Description: {desc}",
                f"URL: {result.get('url', 'N/A')}"
            ]
            
            # Add additional metadata if available
            if "meta_url" in result:
                formatted_result.append(f"Source: {result['meta_url']}")
            if "age" in result:
                formatted_result.append(f"Age: {result['age']}")
            if "language" in result:
                formatted_result.append(f"Language: {result['language']}")
                
            results.append("\n".join(formatted_result))
            
        return "\n\n".join(results)

    def _setup_tools(self):
        @self.mcp.tool()
        async def brave_web_search(
            query: str,
            count: Optional[int] = 20
        ) -> str:
            """Execute web search using Brave Search API with improved results
            
            Args:
                query: Search terms
                count: Desired number of results (10-20)
            """
            min_results = max(10, min(count, 20))  # Ensure between 10 and 20
            
            all_results = await self._get_web_results(query, min_results)
            
            if not all_results:
                return "No results found for the query."
                
            formatted_results = []
            for result in all_results[:min_results]:
                formatted_result = [
                    f"Title: {result.get('title', 'N/A')}",
                    f"Description: {result.get('description', 'N/A')}",
                    f"URL: {result.get('url', 'N/A')}"
                ]
                
                # Include additional context if available
                if result.get('extra_snippets'):
                    formatted_result.append("Additional Context:")
                    formatted_result.extend([f"- {snippet}" for snippet in result['extra_snippets'][:2]])
                    
                formatted_results.append("\n".join(formatted_result))
            
            return "\n\n".join(formatted_results)

        @self.mcp.tool() 
        async def brave_local_search(
            query: str,
            count: Optional[int] = 20  # Changed default from 5 to 20
        ) -> str:
            """Search for local businesses and places
            
            Args:
                query: Location terms
                count: Results (1-20
            """
            self.rate_limit.check()

            # Initial location search
            params = {
                "q": query,
                "search_lang": "en",
                "result_filter": "locations",
                "count": 20  # Always request maximum results
            }

            client = self.get_client()
            response = await client.get(
                f"{self.base_url}/web/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            location_ids = self._extract_location_ids(data)
            if not location_ids:
                # If no local results found, fallback to web search
                # with minimum 10 results
                return await brave_web_search(query, 20)

            # If we have less than 10 location IDs, try to get more
            offset = 0
            while len(location_ids) < 10 and offset < 40:
                offset += 20
                additional_response = await client.get(
                    f"{self.base_url}/web/search",
                    params={
                        "q": query,
                        "search_lang": "en",
                        "result_filter": "locations",
                        "count": 20,
                        "offset": offset
                    }
                )
                additional_data = additional_response.json()
                location_ids.extend(self._extract_location_ids(additional_data))

            # Get details for at least 10 locations
            pois, descriptions = await self._get_location_details(
                location_ids[:max(10, len(location_ids))]
            )
            return self._format_local_results(pois, descriptions)

    async def _get_location_details(
        self,
        ids: List[str]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Fetch POI and description data for locations"""
        client = self.get_client()
        pois_response, desc_response = await asyncio.gather(
            client.get(
                f"{self.base_url}/local/pois",
                params={"ids": ids}
            ),
            client.get(
                f"{self.base_url}/local/descriptions",
                params={"ids": ids}
            )
        )
        return (
            pois_response.json(),
            desc_response.json()
        )

    def _extract_location_ids(self, data: Dict) -> List[str]:
        """Extract location IDs from search response"""
        return [
            result["id"] 
            for result in data.get("locations", {}).get("results", [])
            if "id" in result
        ]

    def _format_local_results(
        self,
        pois: Dict[str, Any],
        descriptions: Dict[str, Any]
    ) -> str:
        """Format local search results with details"""
        results = []
        for poi in pois.get("results", []):
            location = {
                "name": poi.get("name", "N/A"),
                "address": self._format_address(poi.get("address", {})),
                "phone": poi.get("phone", "N/A"),
                "rating": self._format_rating(poi.get("rating", {})),
                "price": poi.get("priceRange", "N/A"),
                "hours": ", ".join(poi.get("openingHours", [])) or "N/A",
                "description": descriptions.get("descriptions", {}).get(
                    poi["id"], "No description available"
                )
            }
            
            results.append(
                f"Name: {location['name']}\n"
                f"Address: {location['address']}\n"
                f"Phone: {location['phone']}\n"
                f"Rating: {location['rating']}\n"
                f"Price Range: {location['price']}\n"
                f"Hours: {location['hours']}\n"
                f"Description: {location['description']}"
            )
        
        return "\n---\n".join(results) or "No local results found"

    def _format_address(self, addr: Dict) -> str:
        """Format address components"""
        components = [
            addr.get("streetAddress", ""),
            addr.get("addressLocality", ""),
            addr.get("addressRegion", ""),
            addr.get("postalCode", "")
        ]
        return ", ".join(filter(None, components)) or "N/A"

    def _format_rating(self, rating: Dict) -> str:
        """Format rating information"""
        if not rating:
            return "N/A"
        # Use ASCII star (*) instead of Unicode star
        stars = "*" * int(float(rating.get('ratingValue', 0)))
        return f"{rating.get('ratingValue', 'N/A')} {stars} ({rating.get('ratingCount', 0)} reviews)"

    def run(self):
        """Start the MCP server"""
        self.mcp.run()


if mode == "local":
    if __name__ == "__main__":
        server = BraveSearchServer(api_key)
        server.run()
else:
    if __name__ == "__main__":
        
        register_mcp_router(app, BraveSearchServer(api_key).mcp, "/mcp")
        PORT = int(os.getenv("PORT_BRAVE_SERVER", 5002))
        logger.info(f"Starting brave MCP server in production (SSE) mode on port {PORT}.")
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info") 
