"""Pydantic 数据模型定义"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """搜索请求（文本输入场景），图片上传走 multipart"""
    text: str = Field(..., min_length=1, description="搜索关键词，如 '纸鹤'")


class StepData(BaseModel):
    """单个折叠步骤"""
    step_number: int = Field(..., description="步骤序号，从 1 开始")
    title: str = Field(default="", description="步骤标题")
    image_url: str = Field(default="", description="步骤配图 URL")
    description: str = Field(default="", description="步骤详细描述")


class TutorialResult(BaseModel):
    """单个教程结果"""
    title: str = Field(..., description="教程标题")
    source_url: str = Field(..., description="来源页面 URL")
    steps: list[StepData] = Field(default_factory=list, description="步骤列表")


class SearchResponse(BaseModel):
    """搜索接口统一响应"""
    query: str = Field(..., description="原始搜索词")
    results: list[TutorialResult] = Field(default_factory=list, description="教程结果列表")
