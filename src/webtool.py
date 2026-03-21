import serpapi
from os import getenv

def format_to_markdown(data):
    md = "# 🔍 Search Results Report\n\n"

    # --- Knowledge Graph ---
    kg = data.get("knowledge_graph", {})
    md += "## 🧠 Knowledge Graph\n"

    if kg:
        for key, value in kg.items():
            if isinstance(value, dict):
                md += f"- **{key}**:\n"
                for k, v in value.items():
                    md += f"  - {k}: {v}\n"
            else:
                md += f"- **{key}**: {value}\n"
    else:
        md += "_No data_\n"

    md += "\n---\n\n"

    # --- Organic Results ---
    md += "## 🌐 Organic Results\n"
    md += "| Title | Link | Snippet |\n"
    md += "|-------|------|---------|\n"

    for r in data.get("organic_results", []):
        md += f"| {r.get('title','')} | {r.get('link','')} | {r.get('snippet','')} |\n"

    md += "\n---\n\n"

    # --- Inline Videos ---
    md += "## 🎥 Inline Videos\n"
    md += "| Title | Platform | Channel | Link |\n"
    md += "|------|----------|---------|------|\n"

    for v in data.get("inline_videos", []):
        md += f"| {v.get('title','')} | {v.get('platform','')} | {v.get('channel','')} | {v.get('link','')} |\n"

    md += "\n---\n\n"

    # --- Short Videos ---
    md += "## 📱 Short Videos\n"
    md += "| Title | Source | Profile | Link |\n"
    md += "|------|--------|---------|------|\n"

    for v in data.get("short_videos", []):
        md += f"| {v.get('title','')} | {v.get('source','')} | {v.get('profile_name','')} | {v.get('link','')} |\n"

    return md

def perform_google_search(query: str) -> str:
    sanitized = query.replace(" ", "+")

    client = serpapi.Client(api_key=getenv("SERP_API_KEY"))

    results = client.search({
        "q": sanitized,
        "location": "Austin, Texas, United States",
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com"
    })

    if results.data["search_metadata"]["status"] == "Success":
        md = format_to_markdown(results.data)
    else:
        md = "Failed to fetch results"
    
    return md