"""
Test Document Diff Generation
문서 변경 내용 Diff 생성 테스트 (TDD)
"""
import pytest
from datetime import datetime


@pytest.mark.unit
class TestDiffGeneration:
    """Diff 생성 테스트"""

    async def test_generate_text_diff_simple(self):
        """간단한 텍스트 Diff 생성 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_content = "원본 텍스트입니다.\n두번째 줄입니다."
        new_content = "수정된 텍스트입니다.\n두번째 줄입니다."

        # Diff 생성
        diff = generator.generate_text_diff(old_content, new_content)

        # Diff 포맷 확인 (unified diff)
        assert diff is not None
        assert len(diff) > 0
        assert "-원본 텍스트입니다." in diff
        assert "+수정된 텍스트입니다." in diff

    async def test_generate_text_diff_no_change(self):
        """변경 없음 Diff 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        content = "동일한 텍스트입니다."

        # Diff 생성
        diff = generator.generate_text_diff(content, content)

        # 변경사항 없음
        assert diff == "" or diff is None

    async def test_generate_text_diff_multiline(self):
        """여러 줄 Diff 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_content = """제1조 목적
이 법은 개인정보의 처리 및 보호에 관한 사항을 정한다.

제2조 정의
1. 개인정보란 생존하는 개인에 관한 정보를 말한다."""

        new_content = """제1조 목적
이 법은 개인정보의 수집, 처리 및 보호에 관한 사항을 정한다.

제2조 정의
1. 개인정보란 살아있는 개인에 관한 정보를 말한다."""

        # Diff 생성
        diff = generator.generate_text_diff(old_content, new_content)

        # 변경된 줄 확인
        assert diff is not None
        assert "처리" in diff or "수집" in diff
        assert "생존하는" in diff or "살아있는" in diff

    async def test_generate_document_diff(self):
        """문서 전체 Diff 생성 테스트 (title, content 포함)"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_doc = {
            "title": "개인정보보호법",
            "content": "제1조 목적\n이 법은 개인정보를 보호한다.",
            "document_type": "law"
        }

        new_doc = {
            "title": "개인정보 보호법",
            "content": "제1조 목적\n이 법은 개인정보를 보호하고 권리를 보장한다.",
            "document_type": "law"
        }

        # 문서 전체 Diff 생성
        diff_result = generator.generate_document_diff(old_doc, new_doc)

        # Diff 결과 확인
        assert diff_result is not None
        assert "title_diff" in diff_result or "content_diff" in diff_result
        assert diff_result["has_changes"] is True

    async def test_generate_document_diff_no_change(self):
        """문서 변경 없음 Diff 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        doc = {
            "title": "동일 문서",
            "content": "동일 내용",
            "document_type": "law"
        }

        # 문서 Diff 생성
        diff_result = generator.generate_document_diff(doc, doc)

        # 변경사항 없음
        assert diff_result is not None
        assert diff_result["has_changes"] is False


@pytest.mark.unit
class TestDiffFormatting:
    """Diff 포맷팅 테스트"""

    async def test_format_diff_as_html(self):
        """HTML 포맷 Diff 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_content = "원본 내용"
        new_content = "수정된 내용"

        # HTML 포맷 Diff
        html_diff = generator.generate_html_diff(old_content, new_content)

        # HTML 태그 확인
        assert html_diff is not None
        assert "<" in html_diff and ">" in html_diff
        assert "원본" in html_diff or "수정된" in html_diff

    async def test_format_diff_as_json(self):
        """JSON 포맷 Diff 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_doc = {
            "title": "원본",
            "content": "원본 내용"
        }

        new_doc = {
            "title": "수정본",
            "content": "수정된 내용"
        }

        # JSON 포맷 Diff
        diff_result = generator.generate_document_diff(old_doc, new_doc)

        # JSON 구조 확인
        assert isinstance(diff_result, dict)
        assert "has_changes" in diff_result
        assert "changes" in diff_result or "title_diff" in diff_result or "content_diff" in diff_result


@pytest.mark.unit
class TestDiffStatistics:
    """Diff 통계 테스트"""

    async def test_calculate_diff_statistics(self):
        """Diff 통계 계산 테스트"""
        from app.services.diff_generator import DiffGenerator

        generator = DiffGenerator()

        old_content = "첫번째 줄\n두번째 줄\n세번째 줄"
        new_content = "첫번째 줄\n수정된 두번째 줄\n세번째 줄\n네번째 줄"

        # 통계 계산
        stats = generator.calculate_diff_stats(old_content, new_content)

        # 통계 확인
        assert stats is not None
        assert "lines_added" in stats
        assert "lines_removed" in stats
        assert "lines_changed" in stats
        assert stats["lines_added"] >= 1  # 네번째 줄 추가
        assert stats["lines_changed"] >= 1  # 두번째 줄 수정
