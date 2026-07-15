"""AI 提取模块 - 清洗和结构化步骤数据"""

import logging
import re

logger = logging.getLogger(__name__)

_NOISE_PREFIXES = re.compile(
    r"^(step\s*\d+\s*[:\-\.]?\s*|第\d+步\s*[:：]?\s*)",
    re.IGNORECASE,
)


def extract_steps(raw_content: dict) -> list[dict]:
    """将原始爬取内容转换为干净的步骤列表"""
    raw_steps = raw_content.get("steps", [])
    if not raw_steps:
        return []

    cleaned = []
    seen_numbers = set()

    for raw in raw_steps:
        step = _clean_step(raw)
        if step is None:
            continue
        if step["step_number"] in seen_numbers:
            continue
        seen_numbers.add(step["step_number"])
        cleaned.append(step)

    # 重新编号确保连续
    for idx, step in enumerate(cleaned, start=1):
        step["step_number"] = idx

    logger.info("提取完成: %d 步 -> %d 步", len(raw_steps), len(cleaned))
    return cleaned


def _clean_step(raw: dict) -> dict | None:
    description = raw.get("description", "")
    image_url = raw.get("image_url", "")
    title = raw.get("title", "")
    step_number = raw.get("step_number", 0)

    if not description and not image_url:
        return None

    description = _normalize_description(description)
    title = _normalize_title(title, step_number)
    image_url = _normalize_image_url(image_url)

    if not description and not image_url:
        return None

    return {
        "step_number": step_number,
        "title": title,
        "image_url": image_url,
        "description": description,
    }


def _normalize_description(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    text = _NOISE_PREFIXES.sub("", text)
    text = text.strip(" -:.,")
    return text


def _normalize_title(title: str, step_number: int) -> str:
    if title:
        title = re.sub(r"\s+", " ", title).strip()
        title = _NOISE_PREFIXES.sub("", title)
        return title
    return f"Step {step_number}"


def _normalize_image_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    # 过滤明显不是步骤图的 URL（跟踪像素、图标等）
    # 只在文件名部分检查，避免误匹配域名
    from urllib.parse import urlparse as _urlparse
    url_path = _urlparse(url).path.lower()
    skip_patterns = ["pixel", "tracker", "1x1", "spacer", "blank", "favicon", "avatar", "logo."]
    for pattern in skip_patterns:
        if pattern in url_path:
            return ""
    # 确保 URL 合法：http(s)、协议相对路径、或 data URI
    if not url.startswith(("http://", "https://", "//", "data:")):
        return ""

    # 协议相对路径补全
    if url.startswith("//"):
        url = f"https:{url}"

    # data URI 保留（如 SVG 步骤图）
    if url.startswith("data:image"):
        return url

    return url
