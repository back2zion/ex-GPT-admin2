"""
Diff Generator Service
문서 변경 내용 Diff 생성 서비스
"""
import difflib
from typing import Dict, List, Optional
from html import escape
import logging

logger = logging.getLogger(__name__)


class DiffGenerator:
    """문서 Diff 생성 서비스"""

    def generate_text_diff(
        self,
        old_text: str,
        new_text: str,
        context_lines: int = 3
    ) -> str:
        """
        두 텍스트 간의 Unified Diff 생성

        Args:
            old_text: 원본 텍스트
            new_text: 새 텍스트
            context_lines: 컨텍스트 줄 수 (기본 3)

        Returns:
            str: Unified diff 문자열
        """
        if old_text == new_text:
            return ""

        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="원본",
            tofile="수정본",
            lineterm="",
            n=context_lines
        )

        return "".join(diff)

    def generate_document_diff(
        self,
        old_doc: Dict,
        new_doc: Dict
    ) -> Dict:
        """
        문서 전체 Diff 생성 (title, content 등)

        Args:
            old_doc: 원본 문서 딕셔너리
            new_doc: 새 문서 딕셔너리

        Returns:
            Dict: {
                "has_changes": bool,
                "title_diff": str or None,
                "content_diff": str or None,
                "changes": List[str]
            }
        """
        result = {
            "has_changes": False,
            "title_diff": None,
            "content_diff": None,
            "changes": []
        }

        # Title 비교
        old_title = old_doc.get("title", "")
        new_title = new_doc.get("title", "")

        if old_title != new_title:
            result["has_changes"] = True
            result["title_diff"] = self.generate_text_diff(old_title, new_title)
            result["changes"].append("title")

        # Content 비교
        old_content = old_doc.get("content", "")
        new_content = new_doc.get("content", "")

        if old_content != new_content:
            result["has_changes"] = True
            result["content_diff"] = self.generate_text_diff(old_content, new_content)
            result["changes"].append("content")

        return result

    def generate_html_diff(
        self,
        old_text: str,
        new_text: str,
        inline: bool = True
    ) -> str:
        """
        HTML 포맷 Diff 생성

        Args:
            old_text: 원본 텍스트
            new_text: 새 텍스트
            inline: True면 inline diff, False면 side-by-side

        Returns:
            str: HTML diff
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        if inline:
            # Inline diff (한 컬럼에 +/- 표시)
            diff = difflib.unified_diff(
                old_lines,
                new_lines,
                lineterm=""
            )

            html_parts = ['<div class="diff">']
            for line in diff:
                escaped = escape(line)
                if line.startswith('+'):
                    html_parts.append(f'<div class="diff-added">{escaped}</div>')
                elif line.startswith('-'):
                    html_parts.append(f'<div class="diff-removed">{escaped}</div>')
                elif line.startswith('@@'):
                    html_parts.append(f'<div class="diff-header">{escaped}</div>')
                else:
                    html_parts.append(f'<div class="diff-context">{escaped}</div>')
            html_parts.append('</div>')

            return "\n".join(html_parts)
        else:
            # Side-by-side diff
            diff_obj = difflib.HtmlDiff()
            return diff_obj.make_table(
                old_lines,
                new_lines,
                fromdesc="원본",
                todesc="수정본"
            )

    def calculate_diff_stats(
        self,
        old_text: str,
        new_text: str
    ) -> Dict:
        """
        Diff 통계 계산

        Args:
            old_text: 원본 텍스트
            new_text: 새 텍스트

        Returns:
            Dict: {
                "lines_added": int,
                "lines_removed": int,
                "lines_changed": int,
                "total_changes": int
            }
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))

        stats = {
            "lines_added": 0,
            "lines_removed": 0,
            "lines_changed": 0,
            "total_changes": 0
        }

        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                stats["lines_added"] += 1
            elif line.startswith('-') and not line.startswith('---'):
                stats["lines_removed"] += 1

        # 변경된 줄 = min(추가, 삭제) - 한 줄이 수정되면 추가+삭제로 표시됨
        stats["lines_changed"] = min(stats["lines_added"], stats["lines_removed"])

        # 실제 추가/삭제에서 변경된 줄 제외
        stats["lines_added"] -= stats["lines_changed"]
        stats["lines_removed"] -= stats["lines_changed"]

        stats["total_changes"] = (
            stats["lines_added"] +
            stats["lines_removed"] +
            stats["lines_changed"]
        )

        return stats

    def generate_side_by_side_diff(
        self,
        old_text: str,
        new_text: str
    ) -> List[Dict]:
        """
        Side-by-side 비교를 위한 라인별 Diff 생성

        Args:
            old_text: 원본 텍스트
            new_text: 새 텍스트

        Returns:
            List[Dict]: [
                {
                    "old_line_num": int or None,
                    "old_content": str or None,
                    "new_line_num": int or None,
                    "new_content": str or None,
                    "change_type": "equal" | "insert" | "delete" | "replace"
                },
                ...
            ]
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        result = []

        old_line_num = 1
        new_line_num = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # 동일한 줄
                for i in range(i1, i2):
                    result.append({
                        "old_line_num": old_line_num,
                        "old_content": old_lines[i],
                        "new_line_num": new_line_num,
                        "new_content": new_lines[j1 + (i - i1)],
                        "change_type": "equal"
                    })
                    old_line_num += 1
                    new_line_num += 1

            elif tag == 'replace':
                # 변경된 줄
                max_lines = max(i2 - i1, j2 - j1)
                for k in range(max_lines):
                    old_content = old_lines[i1 + k] if (i1 + k) < i2 else None
                    new_content = new_lines[j1 + k] if (j1 + k) < j2 else None

                    result.append({
                        "old_line_num": old_line_num if old_content else None,
                        "old_content": old_content,
                        "new_line_num": new_line_num if new_content else None,
                        "new_content": new_content,
                        "change_type": "replace"
                    })

                    if old_content:
                        old_line_num += 1
                    if new_content:
                        new_line_num += 1

            elif tag == 'delete':
                # 삭제된 줄
                for i in range(i1, i2):
                    result.append({
                        "old_line_num": old_line_num,
                        "old_content": old_lines[i],
                        "new_line_num": None,
                        "new_content": None,
                        "change_type": "delete"
                    })
                    old_line_num += 1

            elif tag == 'insert':
                # 추가된 줄
                for j in range(j1, j2):
                    result.append({
                        "old_line_num": None,
                        "old_content": None,
                        "new_line_num": new_line_num,
                        "new_content": new_lines[j],
                        "change_type": "insert"
                    })
                    new_line_num += 1

        return result
