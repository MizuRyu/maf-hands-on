"""テキスト分析 Agent のツール定義。"""

from typing import Annotated

from agent_framework import tool


@tool
def count_words(
    text: Annotated[str, "単語数をカウントする対象テキスト"],
) -> str:
    """テキストの単語数をカウントして結果を返す。

    日本語テキストは文字数、英語テキストはスペース区切りの単語数をそれぞれ集計する。
    """
    chars = len(text)
    words = len(text.split())
    return f"文字数: {chars}, 単語数(空白区切り): {words}"


@tool
def summarize_text(
    text: Annotated[str, "要約対象のテキスト"],
    max_sentences: Annotated[int, "要約の最大文数"] = 3,
) -> str:
    """テキストを指定された文数以内に要約する。

    句点(。)で文を分割し、先頭から最大文数分を抽出する簡易要約を行う。
    LLM による高度な要約が必要な場合は Agent 自身の推論に委ねる。
    """
    sentences = [s.strip() for s in text.split("。") if s.strip()]
    selected = sentences[:max_sentences]
    summary = "。".join(selected)
    if summary and not summary.endswith("。"):
        summary += "。"
    return f"要約({len(selected)}/{len(sentences)} 文): {summary}"
