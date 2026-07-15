"""AI 提取模块 - 将原始爬取内容结构化为干净的步骤数据"""

import logging
import re

from models.schemas import StepData

logger = logging.getLogger(__name__)


def extract_steps(raw_content: dict) -> list[dict]:
    """
    将原始爬取的教程内容转换为干净的步骤列表。

    Args:
        raw_content: parse_tutorial_page 的返回值
            {
                "title": str,
                "url": str,
                "steps": [{ step_number, title, image_url, description }, ...]
            }

    Returns:
        清洗后的步骤字典列表: [{ step_number, title, image_url, description }]
    """
    raw_steps = raw_content.get("steps", [])
    if not raw_steps:
        logger.info("教程 '%s' 无步骤数据", raw_content.get("title", ""))
        return []

    cleaned: list[dict] = []
    seen_numbers: set[int] = set()

    for raw in raw_steps:
        step = _clean_step(raw)
        if step is None:
            continue

        # 去重：相同步骤号只保留第一个
        if step["step_number"] in seen_numbers:
            continue
        seen_numbers.add(step["step_number"])
        cleaned.append(step)

    # 重新编号确保连续
    cleaned = _renumber(cleaned)

    logger.info("提取完成: %d 步 -> %d 步", len(raw_steps), len(cleaned))
    return cleaned


# ---------------------------------------------------------------------------
# 单步清洗
# ---------------------------------------------------------------------------
def _clean_step(raw: dict) -> dict | None:
    """清洗单条步骤数据"""
    description = raw.get("description", "")
    image_url = raw.get("image_url", "")
    title = raw.get("title", "")
    step_number = raw.get("step_number", 0)

    # 过滤空步骤（既无文字也无图片）
    if not description and not image_url:
        return None

    # 清洗描述文本
    description = _normalize_description(description)

    # 清洗标题
    title = _normalize_title(title, step_number)

    # 清洗图片 URL
    image_url = _normalize_image_url(image_url)

    return {
        "step_number": step_number,
        "title": title,
        "image_url": image_url,
        "description": description,
    }


# ---------------------------------------------------------------------------
# 描述清洗
# ---------------------------------------------------------------------------
# 常见无意义前缀
_NOISE_PREFIXES = re.compile(
    r"^(step\s*\d+\s*[:\-\.]?\s*|第\d+步\s*[:：]?\s*)",
    re.IGNORECASE,
)


def _normalize_description(text: str) -> str:
    """标准化步骤描述"""
    if not text:
        return ""

    # 去除多余空白
    text = re.sub(r"\s+", " ", text).strip()

    # 去除步骤号前缀（已在 step_number 体现）
    text = _NOISE_PREFIXES.sub("", text)

    # 去除首尾标点空白
    text = text.strip(" -:.,")

    return text


# ---------------------------------------------------------------------------
# 标题清洗
# ---------------------------------------------------------------------------
def _normalize_title(title: str, step_number: int) -> str:
    """标准化步骤标题，若为空则生成默认标题"""
    if title:
        title = re.sub(r"\s+", " ", title).strip()
        title = _NOISE_PREFIXES.sub("", title)
        return title

    # 默认标题
    return f"Step {step_number}"


# ---------------------------------------------------------------------------
# 图片 URL 清洗
# ---------------------------------------------------------------------------
def _normalize_image_url(url: str) -> str:
    """标准化图片 URL"""
    if not url:
        return ""

    # 去除首尾空白
    url = url.strip()

    # 过滤明显不是图片的 URL（如跟踪像素、图标）
    skip_patterns = ["pixel", "tracker", "1x1", "spacer", "blank", "icon", "logo", "favicon"]
    lower = url.lower()
    for pattern in skip_patterns:
        if pattern in lower:
            return ""

    # 确保是合法 URL
    if not url.startswith(("http://", "https://", "//")):
        return ""

    # 协议相对路径补全
    if url.startswith("//"):
        url = f"https:{url}"

    return url


# ---------------------------------------------------------------------------
# 重新编号
# ---------------------------------------------------------------------------
def _renumber(steps: list[dict]) -> list[dict]:
    """确保步骤编号从 1 开始连续"""
    for idx, step in enumerate(steps, start=1):
        step["step_number"] = idx
    return steps
