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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Origami Steps API",
    description="折纸步骤分解服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 内置演示数据 — 爬虫失败时降级使用，确保前端始终有内容可展示
# ---------------------------------------------------------------------------
_DEMO_DATA = {
    "纸鹤": TutorialResult(
        title="传统纸鹤折法 (Traditional Origami Crane)",
        source_url="https://origami.guide/origami-birds/origami-cranes/traditional-origami-crane/",
        steps=[
            StepData(step_number=1, title="准备正方形纸", image_url="",
                     description="取一张正方形折纸，彩色面朝下放置，形成菱形"),
            StepData(step_number=2, title="对折成三角形", image_url="",
                     description="将纸从下角向上角对折，形成一个三角形"),
            StepData(step_number=3, title="再次对折", image_url="",
                     description="将三角形的左角折向右角，形成一个小三角形"),
            StepData(step_number=4, title="展开并压平 - 上层", image_url="",
                     description="展开上层，将顶部角向下折到底边，形成一个小正方形（方形基础）"),
            StepData(step_number=5, title="翻面重复", image_url="",
                     description="翻到背面，重复上一步，形成完整的方形基础"),
            StepData(step_number=6, title="折鸟型基础", image_url="",
                     description="将方形基础的左右下边缘向中线对折，展开后沿折痕将底角向上拉起"),
            StepData(step_number=7, title="翻面重复", image_url="",
                     description="翻到背面重复鸟型基础折法"),
            StepData(step_number=8, title="折叠翅膀", image_url="",
                     description="将上层左右边缘向中线对折，形成更窄的菱形"),
            StepData(step_number=9, title="折叠头部和尾巴", image_url="",
                     description="将下方的两个角向上折作为翅膀，将一侧的尖端向下折作为头部"),
            StepData(step_number=10, title="完成纸鹤", image_url="",
                     description="轻轻拉开翅膀，整理形状，纸鹤完成！"),
        ],
    ),
    "玫瑰": TutorialResult(
        title="简单折纸玫瑰 (Simple Origami Rose)",
        source_url="https://origami.me/rose/",
        steps=[
            StepData(step_number=1, title="准备正方形纸", image_url="",
                     description="取一张正方形红色折纸，面朝下放置"),
            StepData(step_number=2, title="对折再对折", image_url="",
                     description="将纸上下对折，然后左右对折，形成小正方形"),
            StepData(step_number=3, title="折叠四角", image_url="",
                     description="将四个角分别向中心点折叠"),
            StepData(step_number=4, title="再次折叠四角", image_url="",
                     description="将新的四个角再次向中心点折叠"),
            StepData(step_number=5, title="第三次折角", image_url="",
                     description="继续将四个角向中心折叠"),
            StepData(step_number=6, title="翻转并折角", image_url="",
                     description="翻面，将四个角向中心折叠"),
            StepData(step_number=7, title="拉出花瓣", image_url="",
                     description="轻轻拉出每片花瓣，塑造玫瑰形状"),
            StepData(step_number=8, title="整理完成", image_url="",
                     description="调整花瓣间距和弧度，折纸玫瑰完成！"),
        ],
    ),
    "青蛙": TutorialResult(
        title="跳跃折纸青蛙 (Jumping Origami Frog)",
        source_url="https://origami.guide/origami-animals/origami-frogs/jumping-origami-frog/",
        steps=[
            StepData(step_number=1, title="准备长方形纸", image_url="",
                     description="取一张长方形绿色折纸"),
            StepData(step_number=2, title="折出对角线", image_url="",
                     description="上下对折后展开，形成水平中线折痕"),
            StepData(step_number=3, title="折叠上部三角形", image_url="",
                     description="将上半部分的左右角向中线折叠，形成三角形"),
            StepData(step_number=4, title="折叠前腿", image_url="",
                     description="将三角形两侧的角向外斜折，形成前腿形状"),
            StepData(step_number=5, title="折叠身体", image_url="",
                     description="将纸从中间向后对折"),
            StepData(step_number=6, title="折叠后腿", image_url="",
                     description="将下方的两侧分别向上向外折叠，形成后腿"),
            StepData(step_number=7, title="制作弹簧", image_url="",
                     description="将下半部分来回折叠形成弹簧结构"),
            StepData(step_number=8, title="完成跳跃青蛙", image_url="",
                     description="按压弹簧部分松手，青蛙就会跳起来！"),
        ],
    ),
}


def _get_demo_result(query: str) -> TutorialResult | None:
    """从演示数据中匹配结果"""
    q = query.lower().strip()
    for key, result in _DEMO_DATA.items():
        if key in q or any(k in q for k in [key, key.replace("纸", "")]):
            return result
    # 默认返回纸鹤
    return _DEMO_DATA["纸鹤"]


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 搜索接口
# ---------------------------------------------------------------------------
@app.post("/api/search", response_model=SearchResponse)
async def search(
    text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
):
    """搜索折纸教程，支持文字和图片两种输入"""
    query = _build_query(text, image)
    if not query:
        return SearchResponse(query="", results=[], error="请输入搜索关键词")

    logger.info("搜索请求: query='%s'", query)

    # 1. 尝试真实爬取
    results, error = _do_search(query)

    # 2. 爬取失败则降级到演示数据
    if not results:
        demo = _get_demo_result(query)
        if demo:
            logger.info("爬取无结果，使用演示数据")
            return SearchResponse(
                query=query,
                results=[demo],
                error="",
                is_demo=True,
            )
        return SearchResponse(query=query, results=[], error=error or "未找到相关折纸教程")

    return SearchResponse(query=query, results=results, error="", is_demo=False)


def _do_search(query: str) -> tuple[list[TutorialResult], str]:
    """执行真实搜索，返回结果和错误信息"""
    try:
        urls = search_origami_tutorials(query)
    except Exception as exc:
        logger.error("搜索失败: %s", exc)
        return [], f"搜索服务暂时不可用: {exc}"

    if not urls:
        return [], "搜索引擎未返回结果"

    results: list[TutorialResult] = []
    errors: list[str] = []

    for url in urls[:settings.max_tutorial_parse]:
        try:
            raw = parse_tutorial_page(url)
        except Exception as exc:
            logger.warning("解析页面失败 %s: %s", url, exc)
            errors.append(str(exc))
            continue

        if not raw.get("steps"):
            continue

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

    if not results and errors:
        return [], f"页面解析失败: {errors[0]}"

    return results, ""


# ---------------------------------------------------------------------------
# 演示数据接口 - 前端可直接请求演示
# ---------------------------------------------------------------------------
@app.get("/api/demo")
async def get_demo():
    """返回默认演示数据（纸鹤）"""
    demo = _DEMO_DATA["纸鹤"]
    return SearchResponse(query="纸鹤", results=[demo], error="", is_demo=True)


# ---------------------------------------------------------------------------
# 辅助方法
# ---------------------------------------------------------------------------
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
