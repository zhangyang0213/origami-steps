"""搜索引擎爬虫 - 使用 DuckDuckGo 搜索获取折纸教程 URL"""

import logging
from urllib.parse import urlparse

from duckduckgo_search import DDGS

from config import settings

logger = logging.getLogger(__name__)


def search_origami_tutorials(query: str) -> list[str]:
    """
    使用 DuckDuckGo 搜索折纸教程 URL。

    Args:
        query: 搜索关键词，如 "纸鹤" 或 "crane origami"

    Returns:
        去重后的教程页面 URL 列表
    """
    full_query = f"{query} origami tutorial steps instructions"
    urls: list[str] = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(full_query, max_results=settings.max_search_results))
            for r in results:
                href = r.get("href", "")
                if href and href.startswith("http"):
                    urls.append(href)
    except Exception as exc:
        logger.warning("DuckDuckGo 搜索失败: %s", exc)

    # 过滤掉搜索引擎自身和明显无关的 URL
    filtered = _filter_urls(urls)

    logger.info("搜索 '%s' 得到 %d 条结果（原始 %d 条）", full_query, len(filtered), len(urls))
    return filtered[:settings.max_search_results]


def _filter_urls(urls: list[str]) -> list[str]:
    """过滤不合适的 URL"""
    skip_domains = {
        "google.com", "www.google.com",
        "bing.com", "www.bing.com",
        "baidu.com", "www.baidu.com",
        "youtube.com", "www.youtube.com",  # 视频不便解析
        "facebook.com", "twitter.com", "instagram.com",
        "amazon.com", "ebay.com", "aliexpress.com",
        "pinterest.com",  # pinterest 链接不便解析
    }

    result = []
    seen = set()
    for u in urls:
        parsed = urlparse(u)
        domain = parsed.netloc.lower()
        # 跳过不需要的域名
        if domain in skip_domains:
            continue
        # 去重
        if u in seen:
            continue
        seen.add(u)
        result.append(u)
    return result
