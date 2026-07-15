"""应用配置模块"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    # 请求参数
    request_timeout: int = 15
    max_tutorial_parse: int = 3
    max_search_results: int = 8

    # 爬虫 Headers
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    # CORS
    cors_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])


settings = Settings()
