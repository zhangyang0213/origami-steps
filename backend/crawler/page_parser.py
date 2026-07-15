"""教程页面解析模块 - 抓取并提取折纸教程步骤"""

import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from config import settings

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def parse_tutorial_page(url: str) -> dict:
    """
    抓取教程页面并提取步骤内容。

    Returns:
        {"title": str, "url": str, "steps": [{step_number, title, image_url, description}]}
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("无法获取页面 %s: %s", url, exc)
        return {"title": "", "url": url, "steps": []}

    # 检测编码
    if not resp.encoding or resp.encoding == "ISO-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # 移除无关标签
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = _extract_title(soup)
    steps = _extract_steps_structured(soup, url)

    if not steps:
        steps = _extract_steps_from_lists(soup, url)

    if not steps:
        steps = _fallback_extract(soup, url)

    logger.info("解析 %s: 标题='%s', 步骤数=%d", url, title, len(steps))
    return {"title": title, "url": url, "steps": steps}


def _extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""


def _extract_steps_structured(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """策略1: 查找 class/id 含 step 的元素"""
    steps = []
    step_elements = soup.find_all(_match_step_container)
    if not step_elements:
        return []

    for idx, elem in enumerate(step_elements, start=1):
        step = _parse_step_element(elem, idx, base_url)
        if step:
            steps.append(step)
    return steps


def _extract_steps_from_lists(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """策略2: 从有序/无序列表提取"""
    steps = []
    for list_tag in soup.find_all(["ol", "ul"]):
        # 只处理包含5个以上项的列表（更可能是步骤说明）
        items = list_tag.find_all("li", recursive=False)
        if len(items) < 3:
            continue
        for idx, li in enumerate(items, start=1):
            step = _parse_step_element(li, idx, base_url)
            if step:
                steps.append(step)
        if steps:
            break
    return steps


def _match_step_container(tag: Tag) -> bool:
    classes = " ".join(tag.get("class", []))
    tag_id = tag.get("id", "")
    combined = (classes + " " + tag_id).lower()
    return "step" in combined


def _parse_step_element(elem: Tag, step_num: int, base_url: str) -> dict | None:
    img_url = ""
    img_tag = elem.find("img")
    if img_tag:
        # 优先级: data-lazy-src > data-src > src
        src = (img_tag.get("data-lazy-src")
               or img_tag.get("data-src")
               or img_tag.get("src")
               or "")
        # 跳过懒加载占位 SVG（没有实际内容的 data:image SVG）
        if src.startswith("data:image/svg") and len(src) < 500:
            src = ""
        if src:
            img_url = urljoin(base_url, src)

    text = elem.get_text(separator=" ", strip=True)
    if not text and not img_url:
        return None

    step_title = ""
    heading = elem.find(["h2", "h3", "h4", "h5", "strong", "b"])
    if heading:
        step_title = heading.get_text(strip=True)

    # 从文本中识别步骤号
    match = re.search(r"step\s*(\d+)", text, re.IGNORECASE)
    if match:
        step_num = int(match.group(1))

    return {
        "step_number": step_num,
        "title": step_title,
        "image_url": img_url,
        "description": _clean_text(text),
    }


def _fallback_extract(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """回退策略: 按段落+图片交替提取"""
    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"content|post|entry|tutorial", re.I))
    )
    container = article if article else soup

    steps = []
    step_num = 0
    current_text = ""
    current_img = ""

    for child in container.children:
        if not isinstance(child, Tag):
            continue

        if child.name == "img":
            src = (child.get("data-lazy-src") or child.get("data-src") or child.get("src") or "")
            if src.startswith("data:image/svg") and len(src) < 500:
                src = ""
            if src:
                current_img = urljoin(base_url, src)
        elif child.name == "figure":
            img_tag = child.find("img")
            if img_tag:
                src = (img_tag.get("data-lazy-src") or img_tag.get("data-src") or img_tag.get("src") or "")
                if src.startswith("data:image/svg") and len(src) < 500:
                    src = ""
                if src:
                    current_img = urljoin(base_url, src)
            caption = child.find("figcaption")
            if caption:
                current_text = caption.get_text(strip=True)

        if child.name in ("p", "h2", "h3", "h4", "div"):
            text = child.get_text(strip=True)
            if text and len(text) > 5:
                current_text = _clean_text(text)
            if current_text or current_img:
                step_num += 1
                steps.append({
                    "step_number": step_num,
                    "title": "",
                    "image_url": current_img,
                    "description": current_text,
                })
                current_text = ""
                current_img = ""

    return steps


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^step\s*\d+\s*[:\-\.]\s*", "", text, flags=re.IGNORECASE)
    return text
