"""
Test script for LLM-based conversation categorization
"""
import asyncio
import sys
import time
sys.path.insert(0, '/app')

from app.services.categorization import categorize_conversation_safe, categorize_conversation_vllm, categorize_by_keywords

async def test_categorization():
    """Test LLM-based automatic categorization with sample questions"""

    test_cases = [
        {
            "question": "통행료는 어떤 방식으로 산정되나요?",
            "answer": "통행료는 도로의 건설비용, 유지비용 등을 고려하여 산정됩니다.",
            "expected_main": "기술분야",
            "expected_sub": "교통"
        },
        {
            "question": "직원 복지 제도에는 어떤 것들이 있나요?",
            "answer": "직원 복지 제도로는 건강검진, 휴가, 연금 등이 있습니다.",
            "expected_main": "경영분야",
            "expected_sub": "복리후생"
        },
        {
            "question": "도로 안전 점검은 얼마나 자주 하나요?",
            "answer": "도로 안전 점검은 정기적으로 월 1회 실시하며, 긴급 상황 시 수시로 진행합니다.",
            "expected_main": "기술분야",
            "expected_sub": "도로/안전"
        },
        {
            "question": "마케팅 전략은 어떻게 수립하나요?",
            "answer": "시장 조사와 고객 분석을 통해 마케팅 전략을 수립합니다.",
            "expected_main": "경영분야",
            "expected_sub": "영업/디지털"
        },
        {
            "question": "안녕하세요",
            "answer": "안녕하세요! 무엇을 도와드릴까요?",
            "expected_main": "미분류",
            "expected_sub": "없음"
        }
    ]

    print("=== LLM-based Categorization Test ===\n")

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Question: {test['question']}")
        print(f"  Answer: {test['answer'][:50]}...")
        print(f"  Expected: {test['expected_main']} > {test['expected_sub']}")

        start_time = time.time()

        # LLM-based categorization
        main_cat, sub_cat = await categorize_conversation_safe(
            test['question'],
            test['answer']
        )

        elapsed = time.time() - start_time

        match = "✅" if (main_cat == test['expected_main'] and sub_cat == test['expected_sub']) else "❌"
        print(f"  Result: {main_cat} > {sub_cat} {match}")
        print(f"  Time: {elapsed:.2f}s")
        print()

    # Keyword-based comparison
    print("\n=== Keyword-based Comparison ===\n")
    for i, test in enumerate(test_cases[:3], 1):
        main_cat, sub_cat = categorize_by_keywords(test['question'], test['answer'])
        print(f"Test {i}: {main_cat} > {sub_cat}")

if __name__ == "__main__":
    asyncio.run(test_categorization())
