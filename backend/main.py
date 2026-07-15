"""FastAPI 入口 - 折纸步骤分解 Web 应用后端"""

import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from ai.extractor import extract_steps
from config import settings
from crawler.page_parser import parse_tutorial_page
from crawler.search import search_origami_tutorials
from models.schemas import SearchResponse, StepData, TutorialResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Origami Steps API",
    description="折纸步骤分解服务 - 搜索折纸教程并生成步骤流程图",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse)
async def search(
    text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
):
    """
    搜索折纸教程，支持文字和图片两种输入。

    流程：输入 → 匹配/搜索教程URL → 爬取页面 → 提取步骤 → 返回结果
    """
    query = _build_query(text, image)
    if not query:
        return SearchResponse(query="", results=[], error="请输入搜索关键词")

    logger.info("搜索请求: query='%s'", query)

    # 1. 搜索教程 URL
    try:
        urls = search_origami_tutorials(query)
    except Exception as exc:
        logger.error("搜索失败: %s", exc)
        return SearchResponse(query=query, results=[], error=f"搜索服务失败: {exc}")

    if not urls:
        return SearchResponse(query=query, results=[], error="未找到相关折纸教程")

    # 2. 依次尝试解析教程页面
    results: list[TutorialResult] = []
    last_error = ""

    for url in urls[:settings.max_tutorial_parse]:
        try:
            raw = parse_tutorial_page(url)
        except Exception as exc:
            logger.warning("解析页面失败 %s: %s", url, exc)
            last_error = str(exc)
            continue

        if not raw.get("steps") or len(raw.get("steps", [])) < 2:
            logger.info("页面步骤太少，跳过 %s", url)
            continue

        # 3. 清洗步骤
        try:
            cleaned_steps = extract_steps(raw)
        except Exception as exc:
            logger.warning("步骤提取失败 %s: %s", url, exc)
            continue

        if not cleaned_steps or len(cleaned_steps) < 2:
            continue

        results.append(
            TutorialResult(
                title=raw.get("title", ""),
                source_url=url,
                steps=[StepData(**s) for s in cleaned_steps],
            )
        )

        # 找到一个好的结果就够了
        if results:
            break

    if not results:
        error_msg = f"无法从 '{query}' 提取折纸步骤"
        if last_error:
            error_msg += f"（{last_error}）"
        logger.info("搜索无有效结果: %s", error_msg)
        return SearchResponse(query=query, results=[], error=error_msg)

    logger.info("搜索成功: query='%s', 结果='%s', 步骤数=%d",
                query, results[0].title, len(results[0].steps))
    return SearchResponse(query=query, results=results, error="")


@app.get("/api/demo")
async def get_demo():
    """返回纸鹤演示数据（实时从 origami.me 爬取）"""
    try:
        raw = parse_tutorial_page("https://origami.me/crane/")
        if raw.get("steps"):
            cleaned = extract_steps(raw)
            if cleaned:
                return SearchResponse(
                    query="纸鹤",
                    results=[TutorialResult(
                        title=raw.get("title", "传统纸鹤"),
                        source_url="https://origami.me/crane/",
                        steps=[StepData(**s) for s in cleaned],
                    )],
                    error="",
                )
    except Exception as exc:
        logger.error("演示数据获取失败: %s", exc)

    return SearchResponse(query="纸鹤", results=[], error="无法获取演示数据，请检查网络连接")


def _build_query(text: str, image: UploadFile | None) -> str:
    parts: list[str] = []

    if text and text.strip():
        parts.append(text.strip())

    if image is not None:
        filename = Path(image.filename or "").stem if image.filename else ""
        if filename:
            hint = filename.replace("-", " ").replace("_", " ").strip()
            hint = _clean_filename_hint(hint)
            if hint:
                parts.append(hint)

    return " ".join(parts)


def _clean_filename_hint(hint: str) -> str:
    import re
    hint = re.sub(r"\b\d+\b", "", hint)
    hint = re.sub(r"\s+", " ", hint).strip()
    noise_words = {"img", "image", "photo", "pic", "picture", "copy", "screen", "shot"}
    hint = " ".join(w for w in hint.split() if w.lower() not in noise_words)
    return hint


# ---------------------------------------------------------------------------
# 图片代理 — 解决浏览器直接访问 origami.me 图片被拦截的问题
# ---------------------------------------------------------------------------
import requests as _requests

@app.get("/api/proxy/image")
async def proxy_image(url: str = ""):
    """代理图片请求，解决跨域和防盗链问题"""
    if not url or not url.startswith("http"):
        return RedirectResponse(url="/")

    try:
        resp = _requests.get(url, headers={
            "User-Agent": settings.user_agent,
            "Referer": "https://origami.me/",
        }, timeout=15, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return StreamingResponse(
            resp.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except Exception as exc:
        logger.warning("图片代理失败 %s: %s", url, exc)
        return RedirectResponse(url="/")


# ---------------------------------------------------------------------------
# 页面代理 — 让"查看原文"能正常打开
# ---------------------------------------------------------------------------
@app.get("/api/proxy/page", response_class=HTMLResponse)
async def proxy_page(url: str = ""):
    """代理教程页面，解决用户浏览器无法直接访问的问题"""
    if not url or not url.startswith("http"):
        return HTMLResponse("<html><body><h3>无效链接</h3></body></html>")

    try:
        resp = _requests.get(url, headers={
            "User-Agent": settings.user_agent,
            "Accept": "text/html",
        }, timeout=15)
        resp.raise_for_status()

        html = resp.text
        # 注入 base 标签让相对路径资源能正常加载
        if "<head>" in html:
            html = html.replace("<head>", f'<head><base href="{url}">')

        return HTMLResponse(content=html)
    except Exception as exc:
        logger.warning("页面代理失败 %s: %s", url, exc)
        return HTMLResponse(f"<html><body><h3>无法加载页面</h3><p>原链接: <a href='{url}' target='_blank'>{url}</a></p></body></html>")
