"""搜索引擎爬虫模块 - 通过 Google/Bing 搜索折纸教程 URL"""

import logging
import re
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from config import settings

logger = logging.getLogger(__name__)

# 通用请求头
_HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def search_origami_tutorials(query: str) -> list[str]:
    """
    根据查询词搜索折纸教程 URL 列表。

    Args:
        query: 搜索关键词，如 "crane origami tutorial steps"

    Returns:
        去重后的教程页面 URL 列表
    """
    # 构建完整搜索词
    full_query = f"{query} origami tutorial steps"
    encoded_query = quote_plus(full_query)

    # 根据配置选择搜索引擎
    if settings.search_engine == "google":
        urls = _search_google(encoded_query)
    else:
        urls = _search_bing(encoded_query)

    # 过滤：只保留可信域名 & 合法 HTTP(S) 链接
    filtered = _filter_urls(urls)

    logger.info("搜索 '%s' 得到 %d 条有效结果（原始 %d 条）", full_query, len(filtered), len(urls))
    return filtered[: settings.max_search_results]


# ---------------------------------------------------------------------------
# Google 搜索
# ---------------------------------------------------------------------------
def _search_google(encoded_query: str) -> list[str]:
    url = f"{settings.google_search_url}?q={encoded_query}&num={settings.max_search_results}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=settings.request_timeout)
        resp.raise_for_status()
        return _extract_urls_from_html(resp.text)
    except requests.RequestException as exc:
        logger.warning("Google 搜索请求失败: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Bing 搜索
# ---------------------------------------------------------------------------
def _search_bing(encoded_query: str) -> list[str]:
    url = f"{settings.bing_search_url}?q={encoded_query}&count={settings.max_search_results}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=settings.request_timeout)
        resp.raise_for_status()
        return _extract_urls_from_html(resp.text)
    except requests.RequestException as exc:
        logger.warning("Bing 搜索请求失败: %s", exc)
        return []


# ---------------------------------------------------------------------------
# HTML 解析 — 提取搜索结果中的 URL
# ---------------------------------------------------------------------------
def _extract_urls_from_html(html: str) -> list[str]:
    """
    从搜索引擎结果页面 HTML 中提取 URL。
    策略：
      1. 先尝试从 <a href> 中提取 /url?q=... 或直接链接
      2. 用正则兜底提取 http(s) 链接
    """
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Google 重定向格式: /url?q=REAL_URL&...
        if "/url?q=" in href:
            real_url = href.split("/url?q=")[1].split("&")[0]
            urls.append(real_url)
        elif href.startswith("http"):
            urls.append(href)

    # 正则兜底
    if not urls:
        url_pattern = re.compile(r"https?://[^\s\"\'<>]+")
        urls = url_pattern.findall(html)

    return _deduplicate(urls)


# ---------------------------------------------------------------------------
# 辅助方法
# ---------------------------------------------------------------------------
def _filter_urls(urls: list[str]) -> list[str]:
    """只保留可信域名的 URL，排除搜索引擎自身页面"""
    result = []
    for u in urls:
        parsed = urlparse(u)
        domain = parsed.netloc.lower()
        # 排除搜索引擎自身域名
        if domain in ("www.google.com", "google.com", "www.bing.com", "bing.com"):
            continue
        # 检查是否匹配可信域名
        for trusted in settings.trusted_domains:
            if trusted in domain:
                result.append(u)
                break
    return result


def _deduplicate(urls: list[str]) -> list[str]:
    """保持顺序去重"""
    seen: set[str] = set()
    result: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
