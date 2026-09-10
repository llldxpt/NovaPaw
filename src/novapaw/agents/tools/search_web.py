# -*- coding: utf-8 -*-
"""Web search tool backed by a local SearXNG instance."""

from ...runtime.tool_registry import tool_descriptor

import logging
from typing import Literal

import httpx
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

logger = logging.getLogger(__name__)

_SEARXNG_BASE = "http://127.0.0.1:8080"
_TIMEOUT = 15.0
_MAX_RESULTS = 10

_CATEGORY_MAP = {
    "web": "general",
    "images": "images",
    "news": "news",
    "videos": "videos",
}


@tool_descriptor(
    tool_type="network",
    target_param="query",
    policy_name="SearxngSearch",
    default_policy="allow",
    policy_reason="Allow local SearXNG web search",
    ui_description="Search the web via local SearXNG meta-search engine",
    ui_icon="🔎",
)
async def search_web(
    query: str,
    category: Literal["web", "images", "news", "videos"] = "web",
    language: str = "zh",
    engines: str = "",
    pageno: int = 1,
) -> ToolResponse:
    """Search the internet via the local SearXNG meta-search engine.

    Use this tool when you need up-to-date information from the web,
    such as current events, documentation, facts, or any knowledge
    beyond your training data.

    Args:
        query: The search query string.
        category: Result category — "web" (default), "images", "news", or "videos".
        language: Language code, e.g. "zh" for Chinese, "en" for English.
        engines: Comma-separated engine names (e.g. "google,wikipedia").
                 Leave empty to use all enabled engines.
        pageno: Page number starting from 1.

    Returns:
        `ToolResponse` with formatted search results including title, url,
        content snippet, and source engine for each result.
    """
    searxng_cat = _CATEGORY_MAP.get(category, "general")
    params: dict = {
        "q": query,
        "format": "json",
        "categories": searxng_cat,
        "language": language,
        "pageno": str(pageno),
    }
    if engines:
        params["engines"] = engines

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_SEARXNG_BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        logger.warning("SearXNG is not running at %s", _SEARXNG_BASE)
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "SearXNG service is not running. "
                        "Please start it at http://127.0.0.1:5050 first."
                    ),
                ),
            ],
        )
    except Exception as exc:
        logger.exception("SearXNG search failed")
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Search failed: {exc}",
                ),
            ],
        )

    results = data.get("results", [])[:_MAX_RESULTS]
    if not results:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"No results found for: {query}",
                ),
            ],
        )

    lines = [f'SearXNG search results for "{query}" ({category}):', ""]
    for i, r in enumerate(results, 1):
        title = r.get("title", "?")
        url = r.get("url", "?")
        snippet = (r.get("content") or "").replace("\n", " ").strip()
        engine = ", ".join(r.get("engines", ["?"]))
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        lines.append(f"{i}. **{title}**")
        lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   {snippet}")
        lines.append(f"   Source: {engine}")
        lines.append("")

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text="\n".join(lines),
            ),
        ],
    )
