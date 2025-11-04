"""
벡터 데이터 카테고리 관리 API (EDB 기반)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import os
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/vector-categories", tags=["admin-vector-categories"])

# EDB 설정
EDB_HOST = os.getenv("EDB_HOST", "host.docker.internal")
EDB_PORT = int(os.getenv("EDB_PORT", "5444"))
EDB_DATABASE = os.getenv("EDB_DATABASE", "AGENAI")
EDB_USER = os.getenv("EDB_USER", "wisenut_dev")
EDB_PASSWORD = os.getenv("EDB_PASSWORD", "express!12")


async def get_edb_connection():
    """EDB 데이터베이스 연결 생성"""
    try:
        conn = await asyncpg.connect(
            host=EDB_HOST,
            port=EDB_PORT,
            database=EDB_DATABASE,
            user=EDB_USER,
            password=EDB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to EDB: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 연결 실패: {str(e)}"
        )


# Pydantic Models
class CategoryCreate(BaseModel):
    """카테고리 생성 요청"""
    code: str = Field(..., min_length=1, max_length=50, description="카테고리 코드 (예: 17, 18)")
    name: str = Field(..., min_length=1, max_length=500, description="카테고리명")
    description: Optional[str] = Field(None, max_length=2000, description="설명")
    additional_info: Optional[str] = Field(None, max_length=2000, description="추가 정보")


class CategoryUpdate(BaseModel):
    """카테고리 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="카테고리명")
    description: Optional[str] = Field(None, max_length=2000, description="설명")
    additional_info: Optional[str] = Field(None, max_length=2000, description="추가 정보")
    use_yn: Optional[str] = Field(None, pattern="^[YN]$", description="사용 여부 (Y/N)")


class CategoryResponse(BaseModel):
    """카테고리 응답"""
    code: str
    name: str
    description: Optional[str]
    additional_info: Optional[str]
    use_yn: str
    document_count: int
    created_at: datetime
    updated_at: Optional[datetime]


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    include_inactive: bool = False
):
    """
    카테고리 목록 조회

    Args:
        include_inactive: 비활성 카테고리 포함 여부 (기본: False)

    Returns:
        카테고리 목록 (문서 수 포함)
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # WHERE 조건 구성
        where_clause = "c.level_n1_cd = 'DOC_CAT_CD'"
        if not include_inactive:
            where_clause += " AND c.use_yn = 'Y'"

        # 카테고리 목록 조회 (문서 수 포함)
        query = f"""
            SELECT
                c.level_n2_cd as code,
                c.level_n2_nm as name,
                c.level_n2_desc as description,
                c.level_n2_add_info as additional_info,
                c.use_yn,
                c.reg_dt as created_at,
                c.mod_dt as updated_at,
                COALESCE(COUNT(d.doc_id), 0) as document_count
            FROM wisenut.com_cd_lv2 c
            LEFT JOIN wisenut.doc_bas_lst d
                ON d.doc_cat_cd = c.level_n2_cd
                AND d.use_yn = 'Y'
            WHERE {where_clause}
            GROUP BY c.level_n2_cd, c.level_n2_nm, c.level_n2_desc,
                     c.level_n2_add_info, c.use_yn, c.reg_dt, c.mod_dt
            ORDER BY c.level_n2_cd
        """

        rows = await conn.fetch(query)

        categories = []
        for row in rows:
            categories.append({
                "code": row['code'],
                "name": row['name'],
                "description": row['description'],
                "additional_info": row['additional_info'] or "",
                "use_yn": row['use_yn'],
                "document_count": row['document_count'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at'],
            })

        logger.info(f"Returned {len(categories)} categories")
        return categories

    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 목록 조회 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.post("", status_code=201)
async def create_category(category: CategoryCreate):
    """
    카테고리 생성

    Args:
        category: 카테고리 생성 정보

    Returns:
        생성된 카테고리 정보
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 카테고리 코드 중복 확인
        existing = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            category.code
        )

        if existing > 0:
            raise HTTPException(
                status_code=400,
                detail=f"이미 존재하는 카테고리 코드입니다: {category.code}"
            )

        # 카테고리 생성 (level_n2_seq는 자동 생성)
        await conn.execute(
            """
            INSERT INTO wisenut.com_cd_lv2
            (level_n1_cd, level_n2_cd, level_n2_nm,
             level_n2_desc, level_n2_add_info, use_yn, reg_usr_id, reg_dt)
            VALUES ('DOC_CAT_CD', $1, $2, $3, $4, 'Y', 'admin', CURRENT_TIMESTAMP)
            """,
            category.code,
            category.name,
            category.description,
            category.additional_info or ""
        )

        logger.info(f"Created category: {category.code} - {category.name}")

        return {
            "code": category.code,
            "name": category.name,
            "description": category.description,
            "additional_info": category.additional_info or "",
            "use_yn": "Y",
            "document_count": 0,
            "created_at": datetime.now(),
            "updated_at": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 생성 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.put("/{code}")
async def update_category(code: str, category: CategoryUpdate):
    """
    카테고리 수정

    Args:
        code: 카테고리 코드
        category: 수정할 정보

    Returns:
        수정된 카테고리 정보
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 카테고리 존재 확인
        existing = await conn.fetchrow(
            """
            SELECT *
            FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            code
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"카테고리를 찾을 수 없습니다: {code}"
            )

        # 수정할 필드 구성
        updates = []
        params = []
        param_count = 1

        if category.name is not None:
            updates.append(f"level_n2_nm = ${param_count}")
            params.append(category.name)
            param_count += 1

        if category.description is not None:
            updates.append(f"level_n2_desc = ${param_count}")
            params.append(category.description)
            param_count += 1

        if category.additional_info is not None:
            updates.append(f"level_n2_add_info = ${param_count}")
            params.append(category.additional_info)
            param_count += 1

        if category.use_yn is not None:
            updates.append(f"use_yn = ${param_count}")
            params.append(category.use_yn)
            param_count += 1

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="수정할 정보가 없습니다"
            )

        # 수정자 및 수정일 추가
        updates.append(f"mod_usr_id = ${param_count}")
        params.append("admin")
        param_count += 1

        updates.append(f"mod_dt = ${param_count}")
        params.append(datetime.now())
        param_count += 1

        # 코드 추가 (WHERE 절용)
        params.append(code)

        # 카테고리 수정
        query = f"""
            UPDATE wisenut.com_cd_lv2
            SET {", ".join(updates)}
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = ${param_count}
        """

        await conn.execute(query, *params)

        # 수정된 카테고리 조회
        updated = await conn.fetchrow(
            """
            SELECT
                c.level_n2_cd as code,
                c.level_n2_nm as name,
                c.level_n2_desc as description,
                c.level_n2_add_info as additional_info,
                c.use_yn,
                c.reg_dt as created_at,
                c.mod_dt as updated_at,
                COALESCE(COUNT(d.doc_id), 0) as document_count
            FROM wisenut.com_cd_lv2 c
            LEFT JOIN wisenut.doc_bas_lst d
                ON d.doc_cat_cd = c.level_n2_cd
                AND d.use_yn = 'Y'
            WHERE c.level_n1_cd = 'DOC_CAT_CD' AND c.level_n2_cd = $1
            GROUP BY c.level_n2_cd, c.level_n2_nm, c.level_n2_desc,
                     c.level_n2_add_info, c.use_yn, c.reg_dt, c.mod_dt
            """,
            code
        )

        logger.info(f"Updated category: {code}")

        return {
            "code": updated['code'],
            "name": updated['name'],
            "description": updated['description'],
            "additional_info": updated['additional_info'] or "",
            "use_yn": updated['use_yn'],
            "document_count": updated['document_count'],
            "created_at": updated['created_at'],
            "updated_at": updated['updated_at'],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 수정 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.delete("/{code}")
async def delete_category(code: str, hard_delete: bool = False):
    """
    카테고리 삭제

    Args:
        code: 카테고리 코드
        hard_delete: 완전 삭제 여부 (기본: False, soft delete)

    Returns:
        삭제 결과
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 카테고리 존재 확인
        existing = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            code
        )

        if existing == 0:
            raise HTTPException(
                status_code=404,
                detail=f"카테고리를 찾을 수 없습니다: {code}"
            )

        # 해당 카테고리의 문서 수 확인
        doc_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM wisenut.doc_bas_lst
            WHERE doc_cat_cd = $1 AND use_yn = 'Y'
            """,
            code
        )

        if doc_count > 0 and hard_delete:
            raise HTTPException(
                status_code=400,
                detail=f"문서가 {doc_count}건 존재하는 카테고리는 삭제할 수 없습니다"
            )

        if hard_delete:
            # 완전 삭제
            await conn.execute(
                """
                DELETE FROM wisenut.com_cd_lv2
                WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
                """,
                code
            )
            logger.info(f"Hard deleted category: {code}")
        else:
            # Soft delete (use_yn = 'N')
            await conn.execute(
                """
                UPDATE wisenut.com_cd_lv2
                SET use_yn = 'N', mod_usr_id = 'admin', mod_dt = CURRENT_TIMESTAMP
                WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
                """,
                code
            )
            logger.info(f"Soft deleted category: {code}")

        return {
            "code": code,
            "deleted": True,
            "hard_delete": hard_delete
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 삭제 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/next-code")
async def get_next_category_code():
    """
    다음 사용 가능한 카테고리 코드 조회

    Returns:
        다음 사용 가능한 카테고리 코드
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 현재 사용 중인 카테고리 코드 조회
        existing_codes = await conn.fetch(
            """
            SELECT level_n2_cd
            FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD'
            ORDER BY level_n2_cd
            """
        )

        # 숫자 코드 추출
        numeric_codes = []
        for row in existing_codes:
            try:
                numeric_codes.append(int(row['level_n2_cd']))
            except ValueError:
                pass  # 숫자가 아닌 코드는 무시

        # 다음 코드 찾기 (01부터 99까지)
        for i in range(1, 100):
            if i not in numeric_codes:
                return {"next_code": f"{i:02d}"}

        raise HTTPException(
            status_code=400,
            detail="사용 가능한 카테고리 코드가 없습니다 (01-99)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get next category code: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"다음 카테고리 코드 조회 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()
