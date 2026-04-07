"""Web search via DuckDuckGo (duckduckgo-search package)."""

from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    q = (query or "").strip()
    if not q:
        return "Error: search query is required"
    max_results = max(1, min(int(max_results), 10))
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(q, max_results=max_results))
    except Exception as e:
        return f"Error: search failed — {e}"
    if not results:
        return f"No results found for '{q}'."
    lines = []
    for i, r in enumerate(results, start=1):
        title = r.get("title") or "(no title)"
        body = (r.get("body") or "")[:400]
        href = r.get("href") or ""
        lines.append(f"{i}. {title}\n   {body}\n   {href}")
    return "\n\n".join(lines)


def web_search_openai_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web and return short summaries/snippets from top results. "
                "Use for current events, facts, or anything needing up-to-date information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (1–10). Default 5.",
                    },
                },
                "required": ["query"],
            },
        },
    }
