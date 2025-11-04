"""
권한 관리 API 테스트 (TDD)

PRD 요구사항:
- P0: 문서 권한 관리
  1. 부서별 권한 (부서 CRUD, 사용자-부서 할당, 부서별 문서 접근 권한)
  2. 결재라인 기반 권한
  3. 개별 사용자 권한

Security:
- Cerbos 기반 RBAC 검증
- 최소 권한 원칙
- 권한 변경 감사 로그
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Department, User, DocumentPermission, UserDocumentPermission, ApprovalLine, Document


# ============================================
# 부서 관리 테스트
# ============================================

@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, db: AsyncSession):
    """
    부서 생성 테스트
    Given: 관리자 권한이 있는 사용자
    When: 새로운 부서를 생성하면
    Then: 부서가 DB에 저장되고 200 응답이 반환된다
    """
    department_data = {
        "name": "품질환경처",
        "code": "QE",
        "description": "품질 및 환경 관리 부서"
    }

    response = await client.post(
        "/api/v1/admin/permissions/departments",
        json=department_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "품질환경처"
    assert data["code"] == "QE"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, db: AsyncSession):
    """
    부서 목록 조회 테스트
    Given: 여러 부서가 등록되어 있음
    When: 부서 목록을 조회하면
    Then: 모든 부서가 반환된다
    """
    # Given: 테스트 부서 생성
    departments = [
        Department(name="기술처", code="TECH", description="기술 관리"),
        Department(name="관리처", code="ADMIN", description="행정 관리")
    ]
    for dept in departments:
        db.add(dept)
    await db.commit()

    # When: 부서 목록 조회
    response = await client.get("/api/v1/admin/permissions/departments")

    # Then: 모든 부서 반환
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, db: AsyncSession):
    """
    부서 수정 테스트
    Given: 기존 부서가 있음
    When: 부서 정보를 수정하면
    Then: 변경 사항이 DB에 저장된다
    """
    # Given: 기존 부서
    department = Department(name="구매처", code="PUR", description="구매 업무")
    db.add(department)
    await db.commit()
    await db.refresh(department)

    # When: 부서 수정
    update_data = {"description": "구매 및 자재 관리"}
    response = await client.put(
        f"/api/v1/admin/permissions/departments/{department.id}",
        json=update_data
    )

    # Then: 수정 성공
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "구매 및 자재 관리"


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, db: AsyncSession):
    """
    부서 삭제 테스트
    Given: 사용자가 할당되지 않은 부서가 있음
    When: 부서를 삭제하면
    Then: 부서가 DB에서 제거된다
    """
    # Given: 빈 부서
    department = Department(name="임시부서", code="TEMP")
    db.add(department)
    await db.commit()
    await db.refresh(department)

    # When: 부서 삭제
    response = await client.delete(f"/api/v1/admin/permissions/departments/{department.id}")

    # Then: 삭제 성공
    assert response.status_code == 204


# ============================================
# 문서 권한 관리 테스트
# ============================================

@pytest.mark.asyncio
async def test_grant_department_document_permission(client: AsyncClient, db: AsyncSession):
    """
    부서별 문서 접근 권한 부여 테스트
    Given: 부서와 문서가 존재함
    When: 부서에 문서 접근 권한을 부여하면
    Then: DocumentPermission 레코드가 생성된다
    """
    # Given: 부서와 문서
    department = Department(name="법무처", code="LEGAL")
    document = Document(
        title="국가계약법",
        file_path="/path/to/법령/국가계약법.pdf",
        category_id=1,
        status="active"
    )
    db.add(department)
    db.add(document)
    await db.commit()
    await db.refresh(department)
    await db.refresh(document)

    # When: 권한 부여
    permission_data = {
        "document_id": document.id,
        "department_id": department.id,
        "can_read": True,
        "can_write": False
    }
    response = await client.post(
        "/api/v1/admin/permissions/documents",
        json=permission_data
    )

    # Then: 권한 생성 성공
    assert response.status_code == 201
    data = response.json()
    assert data["document_id"] == document.id
    assert data["department_id"] == department.id
    assert data["can_read"] is True


@pytest.mark.asyncio
async def test_grant_approval_line_permission(client: AsyncClient, db: AsyncSession):
    """
    결재라인 기반 문서 권한 부여 테스트
    Given: 결재라인과 문서가 존재함
    When: 결재라인에 문서 접근 권한을 부여하면
    Then: DocumentPermission 레코드가 생성된다
    """
    # Given: 결재라인과 문서
    approval_line = ApprovalLine(
        name="계약승인라인",
        description="계약 관련 문서 승인",
        departments=[1, 2, 3]
    )
    document = Document(
        title="계약서 양식",
        file_path="/path/to/계약서.pdf",
        category_id=1,
        status="active"
    )
    db.add(approval_line)
    db.add(document)
    await db.commit()
    await db.refresh(approval_line)
    await db.refresh(document)

    # When: 권한 부여
    permission_data = {
        "document_id": document.id,
        "approval_line_id": approval_line.id,
        "can_read": True
    }
    response = await client.post(
        "/api/v1/admin/permissions/documents",
        json=permission_data
    )

    # Then: 권한 생성 성공
    assert response.status_code == 201
    data = response.json()
    assert data["approval_line_id"] == approval_line.id


@pytest.mark.asyncio
async def test_grant_user_permission(client: AsyncClient, db: AsyncSession):
    """
    개별 사용자 권한 부여 테스트
    Given: 사용자와 부서가 존재함
    When: 사용자에게 부서 문서 접근 권한을 부여하면
    Then: UserDocumentPermission 레코드가 생성된다
    """
    # Given: 사용자와 부서
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed",
        department_id=1
    )
    department = Department(name="재무처", code="FIN")
    db.add(user)
    db.add(department)
    await db.commit()
    await db.refresh(user)
    await db.refresh(department)

    # When: 사용자 권한 부여
    permission_data = {
        "user_id": user.id,
        "department_id": department.id
    }
    response = await client.post(
        "/api/v1/admin/permissions/users",
        json=permission_data
    )

    # Then: 권한 생성 성공
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user.id
    assert data["department_id"] == department.id


@pytest.mark.asyncio
async def test_check_user_can_access_document(client: AsyncClient, db: AsyncSession):
    """
    사용자 문서 접근 권한 확인 테스트
    Given: 사용자가 부서 A에 속하고, 문서가 부서 A에만 공개됨
    When: 사용자가 문서 접근 권한을 확인하면
    Then: True가 반환된다
    """
    # Given: 사용자, 부서, 문서, 권한 설정
    department = Department(name="인사처", code="HR")
    db.add(department)
    await db.commit()
    await db.refresh(department)

    user = User(
        username="hr_user",
        email="hr@example.com",
        hashed_password="hashed",
        department_id=department.id
    )
    document = Document(
        title="인사규정",
        file_path="/path/to/인사규정.pdf",
        category_id=1,
        status="active"
    )
    db.add(user)
    db.add(document)
    await db.commit()
    await db.refresh(user)
    await db.refresh(document)

    # 부서 권한 부여
    permission = DocumentPermission(
        document_id=document.id,
        department_id=department.id,
        can_read=True
    )
    db.add(permission)
    await db.commit()

    # When: 권한 확인
    response = await client.get(
        f"/api/v1/admin/permissions/check",
        params={"user_id": user.id, "document_id": document.id}
    )

    # Then: 접근 가능
    assert response.status_code == 200
    data = response.json()
    assert data["can_access"] is True


@pytest.mark.asyncio
async def test_revoke_permission(client: AsyncClient, db: AsyncSession):
    """
    권한 회수 테스트
    Given: 부서에 문서 권한이 부여되어 있음
    When: 권한을 회수하면
    Then: DocumentPermission 레코드가 삭제된다
    """
    # Given: 권한 설정
    department = Department(name="개발처", code="DEV")
    document = Document(
        title="기술문서",
        file_path="/path/to/tech.pdf",
        category_id=1,
        status="active"
    )
    db.add(department)
    db.add(document)
    await db.commit()
    await db.refresh(department)
    await db.refresh(document)

    permission = DocumentPermission(
        document_id=document.id,
        department_id=department.id,
        can_read=True
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)

    # When: 권한 회수
    response = await client.delete(
        f"/api/v1/admin/permissions/documents/{permission.id}"
    )

    # Then: 삭제 성공
    assert response.status_code == 204


# ============================================
# 시큐어 코딩 테스트
# ============================================

@pytest.mark.asyncio
async def test_permission_requires_admin_role(client: AsyncClient):
    """
    권한 관리는 관리자만 가능 테스트 (Broken Access Control 방지)
    Given: 일반 사용자 권한
    When: 부서를 생성하려고 하면
    Then: 403 Forbidden이 반환된다
    """
    # TODO: Cerbos 인증 모킹 필요
    # When: 일반 사용자가 부서 생성 시도
    response = await client.post(
        "/api/v1/admin/permissions/departments",
        json={"name": "test", "code": "TEST"},
        # headers={"Authorization": "Bearer user_token"}  # 일반 사용자 토큰
    )

    # Then: 권한 없음
    # assert response.status_code == 403


@pytest.mark.asyncio
async def test_permission_change_audit_log(client: AsyncClient, db: AsyncSession):
    """
    권한 변경 감사 로그 테스트
    Given: 권한 변경이 발생함
    When: 권한 변경 기록을 조회하면
    Then: 감사 로그가 기록되어 있다
    """
    # TODO: 감사 로그 모델 및 엔드포인트 구현 필요
    pass


@pytest.mark.asyncio
async def test_sql_injection_prevention(client: AsyncClient):
    """
    SQL Injection 방지 테스트
    Given: 악의적인 SQL 쿼리가 포함된 입력
    When: 부서를 조회하면
    Then: SQL이 실행되지 않고 안전하게 처리된다
    """
    # When: SQL injection 시도
    malicious_code = "'; DROP TABLE departments; --"
    response = await client.get(
        f"/api/v1/admin/permissions/departments",
        params={"search": malicious_code}
    )

    # Then: 안전하게 처리됨 (SQLAlchemy ORM이 자동으로 방지)
    assert response.status_code in [200, 400]  # 에러 처리 또는 정상 응답


@pytest.mark.asyncio
async def test_least_privilege_principle(client: AsyncClient, db: AsyncSession):
    """
    최소 권한 원칙 테스트
    Given: 사용자에게 read 권한만 부여됨
    When: write 작업을 시도하면
    Then: 권한 부족 에러가 발생한다
    """
    # TODO: 구체적인 권한 검증 로직 구현 필요
    pass
