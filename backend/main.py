"""FastAPI 入口 - 折纸步骤分解 Web 应用后端"""

import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ai.extractor import extract_steps
from config import settings
from crawler.page_parser import parse_tutorial_page
from crawler.search import search_origami_tutorials
from models.schemas import SearchResponse, StepData, TutorialResult

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI 实例
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Origami Steps API",
    description="折纸步骤分解服务 - 搜索并提取折纸教程的分步内容",
    version="1.0.0",
)

# CORS — 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """服务健康检查端点"""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 搜索接口
# ---------------------------------------------------------------------------
@app.post("/api/search", response_model=SearchResponse)
async def search(
    text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
):
    """
    搜索折纸教程。

    支持两种输入方式（可同时传入）：
    - text: 文本关键词
    - image: 图片上传（当前使用文件名作为搜索提示，后续可接入视觉模型）
    """
    # 1. 确定搜索词
    query = _build_query(text, image)
    if not query:
        return SearchResponse(query="", results=[])

    logger.info("搜索请求: query='%s'", query)

    # 2. 搜索教程 URL
    try:
        urls = search_origami_tutorials(query)
    except Exception as exc:
        logger.error("搜索失败: %s", exc)
        return SearchResponse(query=query, results=[])

    if not urls:
        logger.info("未找到相关教程")
        return SearchResponse(query=query, results=[])

    # 3. 解析前 N 个教程页面
    results: list[TutorialResult] = []
    for url in urls[: settings.max_tutorial_parse]:
        try:
            raw = parse_tutorial_page(url)
        except Exception as exc:
            logger.warning("解析页面失败 %s: %s", url, exc)
            continue

        if not raw.get("steps"):
            continue

        # 4. 用 AI 提取器清洗步骤
        try:
            cleaned_steps = extract_steps(raw)
        except Exception as exc:
            logger.warning("步骤提取失败 %s: %s", url, exc)
            continue

        if not cleaned_steps:
            continue

        results.append(
            TutorialResult(
                title=raw.get("title", ""),
                source_url=url,
                steps=[StepData(**s) for s in cleaned_steps],
            )
        )

    logger.info("搜索完成: query='%s', 返回 %d 条结果", query, len(results))
    return SearchResponse(query=query, results=results)


# ---------------------------------------------------------------------------
# 辅助方法
# ---------------------------------------------------------------------------
def _build_query(text: str, image: UploadFile | None) -> str:
    """
    根据输入构建搜索查询词。

    - 文本输入直接使用
    - 图片输入使用文件名作为提示（占位方案，后续可接入视觉模型）
    - 两者都有时合并
    """
    parts: list[str] = []

    if text and text.strip():
        parts.append(text.strip())

    if image is not None:
        # 占位方案：从文件名提取关键词
        filename = Path(image.filename or "").stem if image.filename else ""
        if filename:
            # 将文件名中的分隔符替换为空格，去除常见后缀
            hint = filename.replace("-", " ").replace("_", " ").strip()
            # 去除数字和常见无关词
            hint = _clean_filename_hint(hint)
            if hint:
                parts.append(hint)

    return " ".join(parts)


def _clean_filename_hint(hint: str) -> str:
    """清洗文件名作为搜索提示"""
    # 去除纯数字
    import re
    hint = re.sub(r"\b\d+\b", "", hint)
    # 去除多余空白
    hint = re.sub(r"\s+", " ", hint).strip()
    # 去除常见无关词
    noise_words = {"img", "image", "photo", "pic", "picture", "copy", "screen", "shot"}
    hint = " ".join(w for w in hint.split() if w.lower() not in noise_words)
    return hint
