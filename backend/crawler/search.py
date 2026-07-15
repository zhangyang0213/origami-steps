"""搜索引擎爬虫 - 直接爬取 origami.me 教程列表"""

import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import settings

logger = logging.getLogger(__name__)

# origami.me 已知教程页面映射
_KNOWN_TUTORIALS = {
    "crane": "https://origami.me/crane/",
    "纸鹤": "https://origami.me/crane/",
    "rose": "https://origami.me/rose/",
    "玫瑰": "https://origami.me/rose/",
    "frog": "https://origami.me/frog/",
    "青蛙": "https://origami.me/frog/",
    "butterfly": "https://origami.me/butterfly/",
    "蝴蝶": "https://origami.me/butterfly/",
    "heart": "https://origami.me/heart/",
    "爱心": "https://origami.me/heart/",
    "star": "https://origami.me/star/",
    "星星": "https://origami.me/star/",
    "fish": "https://origami.me/fish/",
    "鱼": "https://origami.me/fish/",
    "boat": "https://origami.me/boat/",
    "船": "https://origami.me/boat/",
    "airplane": "https://origami.me/paper-airplane/",
    "飞机": "https://origami.me/paper-airplane/",
    "cat": "https://origami.me/cat/",
    "猫": "https://origami.me/cat/",
    "dog": "https://origami.me/dog/",
    "狗": "https://origami.me/dog/",
    "rabbit": "https://origami.me/rabbit/",
    "兔子": "https://origami.me/rabbit/",
    "dragon": "https://origami.me/dragon/",
    "龙": "https://origami.me/dragon/",
    "flower": "https://origami.me/flower/",
    "花": "https://origami.me/flower/",
    "box": "https://origami.me/box/",
    "盒子": "https://origami.me/box/",
    "envelope": "https://origami.me/envelope/",
    "信封": "https://origami.me/envelope/",
}

_HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_origami_tutorials(query: str) -> list[str]:
    """
    根据查询词搜索折纸教程 URL。

    策略：
    1. 精确匹配已知教程映射
    2. 从 origami.me 主页爬取教程列表进行模糊匹配
    3. 兜底：尝试 origami.me/{query}/ 直接拼接
    """
    q = query.strip().lower()

    # 1. 精确匹配
    for key, url in _KNOWN_TUTORIALS.items():
        if key in q or q in key:
            logger.info("精确匹配 '%s' -> %s", key, url)
            return [url]

    # 2. 从 origami.me 主页爬取教程链接
    try:
        site_urls = _scrape_origami_me_links()
        matched = _fuzzy_match(q, site_urls)
        if matched:
            logger.info("模糊匹配 '%s' -> %s", q, matched)
            return matched
    except Exception as exc:
        logger.warning("爬取 origami.me 失败: %s", exc)

    # 3. 兜底：直接拼接
    fallback_url = f"https://origami.me/{q}/"
    logger.info("兜底尝试: %s", fallback_url)
    return [fallback_url]


def _scrape_origami_me_links() -> list[dict]:
    """从 origami.me 主页获取所有教程链接"""
    try:
        resp = requests.get("https://origami.me/", headers=_HEADERS, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        # 匹配 origami.me/xxx/ 格式的教程链接
        if href.startswith("https://origami.me/") and href != "https://origami.me/":
            # 排除非教程页面
            path = urlparse(href).path.strip("/")
            skip = {"category", "about", "contact", "privacy", "terms", "disclaimer", "wp-", "author"}
            if not any(s in path.lower() for s in skip) and path:
                links.append({"url": href, "name": path.replace("-", " "), "text": text.lower()})

    return links


def _fuzzy_match(query: str, site_links: list[dict]) -> list[str]:
    """模糊匹配查询词与网站链接"""
    results = []
    q = query.lower()

    for link in site_links:
        name = link["name"].lower()
        text = link["text"].lower()
        # 查询词在名称或文本中
        if q in name or q in text or name in q:
            results.append(link["url"])

    return results[:settings.max_search_results]
