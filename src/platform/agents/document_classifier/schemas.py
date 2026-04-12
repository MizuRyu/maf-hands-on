"""ドキュメント分類 Agent の構造化出力スキーマ。"""

from pydantic import BaseModel, Field


class DocumentClassification(BaseModel):
    """ドキュメント分類の結果。"""

    category: str = Field(description="分類カテゴリ")
    confidence: float = Field(description="確信度 (0.0-1.0)")
    reasoning: str = Field(description="分類理由")
    keywords: list[str] = Field(description="抽出されたキーワード")
