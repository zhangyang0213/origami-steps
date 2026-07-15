"""应用配置模块 - 搜索引擎设置、超时值、最大结果数等"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """全局配置，frozen=True 保证运行时不可修改"""

    # ---- 搜索引擎 ----
    search_engine: str = "bing"  # 可选 "google" | "bing"
    google_search_url: str = "https://www.google.com/search"
    bing_search_url: str = "https://www.bing.com/search"

    # ---- 请求参数 ----
    request_timeout: int = 10  # 单次 HTTP 请求超时（秒）
    max_search_results: int = 10  # 搜索结果最大抓取数
    max_tutorial_parse: int = 3  # 最多解析的教程页数

    # ---- 爬虫 Headers ----
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    # ---- 折纸相关优质站点域名（用于过滤搜索结果） ----
    trusted_domains: list[str] = field(default_factory=lambda: [
        "origami.me",
        "origami-instructions.com",
        "origami-fun.com",
        "paperkawaii.com",
        "origami.guide",
        "origamimakes.com",
        "instructables.com",
        "youtube.com",
    ])

    # ---- CORS ----
    cors_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:5173",
    ])


# 全局单例
settings = Settings()
