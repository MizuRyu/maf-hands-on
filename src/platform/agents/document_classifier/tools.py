"""ドキュメント分類 Agent のツール定義。"""

from typing import Annotated

from agent_framework import tool

DOCUMENT_KEYWORDS = {
    "contract": ["契約", "甲", "乙", "合意", "締結", "有効期間", "違約金"],
    "invoice": ["請求", "振込", "支払", "金額", "税込", "明細", "合計"],
    "report": ["報告", "結果", "分析", "考察", "まとめ", "調査", "推移"],
    "correspondence": ["拝啓", "敬具", "ご連絡", "お願い", "ご確認", "お世話"],
    "manual": ["手順", "操作", "設定", "インストール", "ステップ", "注意事項"],
}


@tool
def extract_document_keywords(
    text: Annotated[str, "分析対象の文書テキスト"],
) -> str:
    """文書からカテゴリ判定に役立つキーワードを抽出する。"""
    found: dict[str, list[str]] = {}
    for category, keywords in DOCUMENT_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in text]
        if matched:
            found[category] = matched

    if not found:
        return "キーワード検出結果: 該当カテゴリのキーワードが見つかりませんでした"

    lines = ["キーワード検出結果:"]
    for cat, kws in found.items():
        lines.append(f"  {cat}: {', '.join(kws)}")
    return "\n".join(lines)
