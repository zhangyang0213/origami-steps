"""教程页面解析模块 - 抓取并提取折纸教程的步骤信息"""

import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from config import settings

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": settings.user_agent,
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def parse_tutorial_page(url: str) -> dict:
    """
    抓取教程页面并提取结构化内容。

    Args:
        url: 教程页面 URL

    Returns:
        {
            "title": str,
            "url": str,
            "steps": [
                {
                    "step_number": int,
                    "title": str,
                    "image_url": str,
                    "description": str,
                },
                ...
            ]
        }
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("无法获取页面 %s: %s", url, exc)
        return {"title": "", "url": url, "steps": []}

    soup = BeautifulSoup(resp.text, "html.parser")

    # 提取标题
    title = _extract_title(soup)

    # 提取步骤
    steps = _extract_steps(soup, url)

    # 如果结构化提取失败，使用通用段落/图片回退策略
    if not steps:
        steps = _fallback_extract(soup, url)

    logger.info("解析 %s: 标题='%s', 步骤数=%d", url, title, len(steps))
    return {"title": title, "url": url, "steps": steps}


# ---------------------------------------------------------------------------
# 标题提取
# ---------------------------------------------------------------------------
def _extract_title(soup: BeautifulSoup) -> str:
    """优先取 <h1>，否则取 <title>"""
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""


# ---------------------------------------------------------------------------
# 结构化步骤提取
# ---------------------------------------------------------------------------
_STEP_PATTERNS = re.compile(
    r"step\s*(\d+)", re.IGNORECASE
)


def _extract_steps(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    尝试按常见 HTML 模式提取步骤：
      - <ol> / <ul> 内的 <li>
      - class/id 含 "step" 的容器
    """
    steps: list[dict] = []

    # 策略1: 查找 class/id 含 step 的元素
    step_elements = soup.find_all(_match_step_container)

    if step_elements:
        for idx, elem in enumerate(step_elements, start=1):
            step = _parse_step_element(elem, idx, base_url)
            if step:
                steps.append(step)

    # 策略2: 查找有序/无序列表
    if not steps:
        for list_tag in soup.find_all(["ol", "ul"]):
            for idx, li in enumerate(list_tag.find_all("li"), start=1):
                step = _parse_step_element(li, idx, base_url)
                if step:
                    steps.append(step)

    return steps


def _match_step_container(tag: Tag) -> bool:
    """匹配 class 或 id 包含 step 的容器"""
    classes = " ".join(tag.get("class", []))
    tag_id = tag.get("id", "")
    combined = (classes + " " + tag_id).lower()
    return "step" in combined


def _parse_step_element(elem: Tag, step_num: int, base_url: str) -> dict | None:
    """从单个步骤元素中提取图片和文字"""
    # 提取图片
    img_url = ""
    img_tag = elem.find("img")
    if img_tag:
        src = img_tag.get("src") or img_tag.get("data-src") or ""
        if src:
            img_url = urljoin(base_url, src)

    # 提取文字描述
    text = elem.get_text(separator=" ", strip=True)
    if not text and not img_url:
        return None

    # 尝试提取步骤标题
    step_title = ""
    heading = elem.find(["h2", "h3", "h4", "h5", "strong", "b"])
    if heading:
        step_title = heading.get_text(strip=True)

    # 从文本中识别步骤号（覆盖自动编号）
    match = _STEP_PATTERNS.search(text)
    if match:
        step_num = int(match.group(1))

    return {
        "step_number": step_num,
        "title": step_title,
        "image_url": img_url,
        "description": _clean_text(text),
    }


# ---------------------------------------------------------------------------
# 通用回退提取
# ---------------------------------------------------------------------------
def _fallback_extract(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    当结构化提取失败时，回退到按段落 + 图片交替提取。
    收集所有 <p> 和 <img>（在文章区域），按出现顺序配对。
    """
    # 尝试定位文章主体
    article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|post|entry", re.I))
    container = article if article else soup

    steps: list[dict] = []
    step_num = 0
    current_text = ""
    current_img = ""

    for child in container.children:
        if not isinstance(child, Tag):
            continue

        # 收集图片
        if child.name == "img":
            src = child.get("src") or child.get("data-src") or ""
            if src:
                current_img = urljoin(base_url, src)
        elif child.name == "figure":
            img_tag = child.find("img")
            if img_tag:
                src = img_tag.get("src") or img_tag.get("data-src") or ""
                if src:
                    current_img = urljoin(base_url, src)
            caption = child.find("figcaption")
            if caption:
                current_text = caption.get_text(strip=True)

        # 收集文字
        if child.name in ("p", "h2", "h3", "h4", "div"):
            text = child.get_text(strip=True)
            if text and len(text) > 5:
                current_text = _clean_text(text)

            # 当文字和图片都收集到时，生成一个步骤
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


# ---------------------------------------------------------------------------
# 文本清洗
# ---------------------------------------------------------------------------
def _clean_text(text: str) -> str:
    """清洗文本：去除多余空白、换行等"""
    text = re.sub(r"\s+", " ", text).strip()
    # 去掉开头的 "Step X:" 之类的前缀（已在 step_number 中体现）
    text = re.sub(r"^step\s*\d+\s*[:\-\.]\s*", "", text, flags=re.IGNORECASE)
    return text
