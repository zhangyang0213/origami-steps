"""Pydantic 数据模型"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StepData(BaseModel):
    step_number: int = Field(..., description="步骤序号")
    title: str = Field(default="", description="步骤标题")
    image_url: str = Field(default="", description="步骤配图（URL 或 SVG data URI）")
    description: str = Field(default="", description="步骤描述")


class TutorialResult(BaseModel):
    title: str = Field(..., description="教程标题")
    source_url: str = Field(default="", description="来源页面 URL")
    steps: list[StepData] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str = Field(..., description="搜索词")
    results: list[TutorialResult] = Field(default_factory=list)
    error: str = Field(default="", description="错误信息")
