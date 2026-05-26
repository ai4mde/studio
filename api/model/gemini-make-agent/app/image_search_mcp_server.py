"""MCP server for finding renderable image URLs for prototype sections."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from mcp.server import FastMCP

mcp = FastMCP("studio_image_search")


def _commons_api(params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"https://commons.wikimedia.org/w/api.php?{query}",
        headers={"User-Agent": "ai4mde-studio-image-search/1.0"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@mcp.tool()
def search_images(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search Wikimedia Commons and return direct image URLs suitable for HTML img tags.

    Args:
        query: Domain/topic/search phrase for the image, e.g. "loan office banking".
        count: Maximum number of image results to return.
    """
    safe_count = max(1, min(int(count or 5), 10))
    search_data = _commons_api(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrlimit": str(safe_count * 3),
            "prop": "imageinfo",
            "iiprop": "url|mime|extmetadata",
            "iiurlwidth": "1600",
            "origin": "*",
        }
    )
    pages = (search_data.get("query") or {}).get("pages") or {}
    results: list[dict[str, str]] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        mime = str(info.get("mime") or "")
        url = str(info.get("thumburl") or info.get("url") or "")
        if not url or not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        meta = info.get("extmetadata") or {}
        credit = (meta.get("Artist") or {}).get("value") or ""
        license_name = (meta.get("LicenseShortName") or {}).get("value") or ""
        results.append(
            {
                "title": str(page.get("title") or "").replace("File:", ""),
                "url": url,
                "source": str(info.get("descriptionurl") or ""),
                "license": str(license_name),
                "credit": str(credit),
            }
        )
        if len(results) >= safe_count:
            break
    return results


if __name__ == "__main__":
    mcp.run()
