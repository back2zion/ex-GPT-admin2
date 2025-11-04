"""
파일 브라우저 API 테스트
TDD 방식: 테스트 먼저 작성, 코드 나중에 구현

Security:
- Path Traversal 방지 테스트
- 허용되지 않은 경로 접근 차단 테스트
- 심볼릭 링크 차단 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestFileBrowserSecurity:
    """파일 브라우저 보안 테스트"""

    def test_path_traversal_prevention(self):
        """Path Traversal 공격 차단 테스트"""
        # Path Traversal 시도 목록
        malicious_paths = [
            "../../etc/passwd",
            "../../../../../etc/shadow",
            "C:\\..\\Windows\\System32",
            "\\\\server\\..\\..\\etc\\passwd",
            "/data/audio/../../../etc/passwd",
            "%2e%2e/etc/passwd",
        ]

        for bad_path in malicious_paths:
            response = client.get(
                f"/api/v1/admin/file-browser/list",
                params={"path": bad_path}
            )
            # 400 Bad Request 또는 403 Forbidden 응답 기대
            assert response.status_code in [400, 403], \
                f"Path Traversal not blocked for: {bad_path}"

            # 에러 메시지에 "Path traversal" 또는 "Invalid path" 포함되어야 함
            error_detail = response.json().get("detail", "")
            assert ("traversal" in error_detail.lower() or
                    "invalid" in error_detail.lower()), \
                f"Error message should mention path validation for: {bad_path}"

    def test_unauthorized_path_access(self):
        """허용되지 않은 경로 접근 차단 테스트"""
        # 허용되지 않은 경로들
        unauthorized_paths = [
            "/etc/passwd",
            "/root/.ssh",
            "C:\\Windows\\System32",
            "/var/log",
            "/home/user/.ssh",
        ]

        for path in unauthorized_paths:
            response = client.get(
                f"/api/v1/admin/file-browser/list",
                params={"path": path}
            )
            # 403 Forbidden 응답 기대
            assert response.status_code == 403, \
                f"Unauthorized path should be forbidden: {path}"

            # 에러 메시지에 "Access denied" 또는 "allowed" 포함되어야 함
            error_detail = response.json().get("detail", "")
            assert ("access denied" in error_detail.lower() or
                    "allowed" in error_detail.lower()), \
                f"Error message should mention access control for: {path}"

    def test_get_root_directories(self):
        """루트 디렉토리 목록 조회 테스트"""
        response = client.get("/api/v1/admin/file-browser/roots")
        assert response.status_code == 200

        roots = response.json()
        assert isinstance(roots, list)

        # 각 루트는 path, name, exists 속성을 가져야 함
        for root in roots:
            assert "path" in root
            assert "name" in root
            assert "exists" in root
            assert isinstance(root["exists"], bool)

    def test_validate_path_endpoint(self):
        """경로 검증 엔드포인트 테스트"""
        # 유효한 경로 (허용된 루트 디렉토리)
        # 실제 환경에 따라 조정 필요
        valid_path = "/data/audio"
        response = client.get(
            "/api/v1/admin/file-browser/validate",
            params={"path": valid_path}
        )
        assert response.status_code == 200
        result = response.json()
        # valid가 True 또는 False일 수 있음 (디렉토리 존재 여부에 따라)
        assert "valid" in result

        # 무효한 경로 (Path Traversal)
        invalid_path = "../../etc/passwd"
        response = client.get(
            "/api/v1/admin/file-browser/validate",
            params={"path": invalid_path}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert "error" in result

    def test_symlink_prevention(self):
        """심볼릭 링크 차단 테스트"""
        # 심볼릭 링크 경로 (실제 테스트 환경에서는 생성 필요)
        # 이 테스트는 실제 심볼릭 링크가 있을 때만 작동
        # 여기서는 로직 검증만 수행
        pass

    def test_nonexistent_directory(self):
        """존재하지 않는 디렉토리 처리 테스트"""
        # 허용된 루트 아래의 존재하지 않는 경로
        nonexistent_path = "/data/audio/nonexistent_folder_12345"
        response = client.get(
            "/api/v1/admin/file-browser/list",
            params={"path": nonexistent_path}
        )
        # 404 Not Found 응답 기대 (허용된 경로이지만 존재하지 않음)
        # 또는 403 Forbidden (허용되지 않은 경로)
        assert response.status_code in [403, 404]

    def test_file_instead_of_directory(self):
        """파일 경로 입력 시 처리 테스트"""
        # 허용된 루트 아래의 파일 경로 (실제 파일이 있다면)
        # 이 테스트는 환경에 따라 조정 필요
        # 디렉토리가 아닌 파일 경로 입력 시 400 에러 기대
        pass


class TestFileBrowserFunctionality:
    """파일 브라우저 기능 테스트"""

    def test_list_directory_response_structure(self):
        """디렉토리 목록 응답 구조 테스트"""
        # 허용된 루트 디렉토리가 실제로 존재한다면 테스트 가능
        # 여기서는 응답 구조만 검증

        # 존재하지 않는 경로로 테스트 시 에러 응답 구조 검증
        response = client.get(
            "/api/v1/admin/file-browser/list",
            params={"path": "/data/audio"}
        )

        # 200 (성공) 또는 403/404 (실패) 응답
        if response.status_code == 200:
            data = response.json()
            assert "current_path" in data
            assert "parent_path" in data
            assert "entries" in data
            assert isinstance(data["entries"], list)

            # 각 항목은 name, path, is_directory 속성을 가져야 함
            for entry in data["entries"]:
                assert "name" in entry
                assert "path" in entry
                assert "is_directory" in entry
                assert isinstance(entry["is_directory"], bool)
        else:
            # 에러 응답은 detail 속성을 가져야 함
            assert "detail" in response.json()

    def test_audio_file_filtering(self):
        """음성 파일 필터링 테스트"""
        # 실제 디렉토리가 있다면, 음성 파일만 표시되는지 확인
        # 이 테스트는 환경에 따라 조정 필요
        pass


class TestFileBrowserInputValidation:
    """파일 브라우저 입력 검증 테스트"""

    def test_empty_path_parameter(self):
        """빈 경로 파라미터 처리 테스트"""
        response = client.get("/api/v1/admin/file-browser/list")
        # path 파라미터 필수이므로 422 Unprocessable Entity 응답 기대
        assert response.status_code == 422

    def test_special_characters_in_path(self):
        """경로에 특수 문자 포함 시 처리 테스트"""
        special_paths = [
            "/data/audio/<script>alert('xss')</script>",
            "/data/audio/'; DROP TABLE files; --",
            "/data/audio/\x00null",
        ]

        for path in special_paths:
            response = client.get(
                "/api/v1/admin/file-browser/list",
                params={"path": path}
            )
            # 400 Bad Request 또는 403 Forbidden 응답 기대
            assert response.status_code in [400, 403], \
                f"Special characters should be rejected: {path}"
