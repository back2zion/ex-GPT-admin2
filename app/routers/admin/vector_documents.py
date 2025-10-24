"""
벡터 문서 관리 API 엔드포인트 (EDB 기반)
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
import logging
import os
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/vector-documents", tags=["admin-vector-documents"])

# EDB 설정 (Docker에서 host.docker.internal 사용)
# 주의: pg_hba.conf에 172.31.0.0/16 추가 필요
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


@router.get("/stats")
async def get_vector_documents_stats():
    """
    벡터 문서 통계 조회 (doc_cat_cd별 문서 수)

    Returns:
        {"total": int, "by_doctype": {...}}
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 전체 문서 수
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM wisenut.doc_bas_lst WHERE use_yn = 'Y'"
        )

        # doc_cat_cd별 집계 (com_cd_lv2와 JOIN하여 카테고리명 가져오기)
        rows = await conn.fetch(
            """
            SELECT
                d.doc_cat_cd as category_code,
                COALESCE(c.level_n2_nm, d.doc_cat_cd, '기타') as category_name,
                COUNT(*) as count
            FROM wisenut.doc_bas_lst d
            LEFT JOIN wisenut.com_cd_lv2 c
                ON c.level_n1_cd = 'DOC_CAT_CD'
                AND c.level_n2_cd = d.doc_cat_cd
            WHERE d.use_yn = 'Y'
            GROUP BY d.doc_cat_cd, c.level_n2_nm
            ORDER BY count DESC
            """
        )

        # 응답 형식: {category_code: {name: category_name, count: count}}
        doctype_counts = {
            row['category_code']: {
                'name': row['category_name'],
                'count': row['count']
            } for row in rows
        }

        return {
            "total": total,
            "by_doctype": doctype_counts
        }

    except Exception as e:
        logger.error(f"Failed to get vector documents stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 통계 조회 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.get("")
async def list_vector_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = None,
    doctype: Optional[str] = None
):
    """
    벡터 문서 목록 조회 (EDB에서 실제 데이터 가져오기)

    Args:
        skip: 스킵할 문서 수
        limit: 가져올 문서 수 (최대 1000)
        search: 제목 검색어
        doctype: 문서 타입 필터 (doc_cat_cd)

    Returns:
        {"items": [...], "total": int}
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # WHERE 조건 구성 (테이블 alias d 명시)
        conditions = ["d.use_yn = 'Y'"]
        params = []
        param_count = 1

        if search:
            conditions.append(f"(d.doc_title_nm ILIKE ${param_count} OR d.doc_rep_title_nm ILIKE ${param_count})")
            params.append(f"%{search}%")
            param_count += 1

        if doctype:
            conditions.append(f"d.doc_cat_cd = ${param_count}")
            params.append(doctype)
            param_count += 1

        where_clause = " AND ".join(conditions)

        # 전체 개수 조회
        total_query = f"""
            SELECT COUNT(*)
            FROM wisenut.doc_bas_lst d
            WHERE {where_clause}
        """
        total = await conn.fetchval(total_query, *params)

        # 문서 목록 조회 (com_cd_lv2와 JOIN하여 카테고리명 가져오기)
        list_query = f"""
            SELECT
                d.doc_id,
                COALESCE(d.doc_rep_title_nm, d.doc_title_nm, '제목 없음') as title,
                d.doc_cat_cd as doctype,
                COALESCE(c.level_n2_nm, d.doc_cat_cd, '기타') as doctype_name,
                d.doc_det_level_n1_cd,
                d.doc_det_level_n2_cd,
                d.doc_det_level_n3_cd,
                COALESCE(LENGTH(d.doc_txt), 0) as token_count,
                d.use_yn,
                d.reg_dt as created_at
            FROM wisenut.doc_bas_lst d
            LEFT JOIN wisenut.com_cd_lv2 c
                ON c.level_n1_cd = 'DOC_CAT_CD'
                AND c.level_n2_cd = d.doc_cat_cd
            WHERE {where_clause}
            ORDER BY d.reg_dt DESC
            OFFSET ${param_count} LIMIT ${param_count + 1}
        """
        params.extend([skip, limit])

        rows = await conn.fetch(list_query, *params)

        # 응답 형식 변환 (프론트엔드 호환)
        formatted_docs = []
        for row in rows:
            # file_path는 detail level들을 조합
            file_path = []
            if row['doc_det_level_n1_cd']:
                file_path.append(row['doc_det_level_n1_cd'])
            if row['doc_det_level_n2_cd']:
                file_path.append(row['doc_det_level_n2_cd'])
            if row['doc_det_level_n3_cd']:
                file_path.append(row['doc_det_level_n3_cd'])

            formatted_docs.append({
                "id": str(row['doc_id']),
                "title": row['title'],
                "file_path": file_path,
                "metadata_uri": "",  # EDB에는 없음
                "doctype": row['doctype'] or "기타",
                "doctype_name": row['doctype_name'],  # 카테고리명 추가
                "token_count": row['token_count'],
                "is_active": row['use_yn'] == 'Y',
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            })

        logger.info(f"Returned {len(formatted_docs)} documents from EDB (total: {total})")

        return {
            "items": formatted_docs,
            "total": total
        }

    except Exception as e:
        logger.error(f"Failed to list vector documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 목록 조회 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/{document_id}")
async def get_vector_document(document_id: str):
    """
    벡터 문서 상세 조회

    Args:
        document_id: 문서 ID (doc_id)

    Returns:
        문서 상세 정보
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # EDB에서 doc_id로 문서 조회 (com_cd_lv2와 JOIN하여 카테고리명 가져오기)
        row = await conn.fetchrow(
            """
            SELECT
                d.doc_id,
                COALESCE(d.doc_rep_title_nm, d.doc_title_nm, '제목 없음') as title,
                d.doc_cat_cd as doctype,
                COALESCE(c.level_n2_nm, d.doc_cat_cd, '기타') as doctype_name,
                d.doc_det_level_n1_cd,
                d.doc_det_level_n2_cd,
                d.doc_det_level_n3_cd,
                COALESCE(LENGTH(d.doc_txt), 0) as token_count,
                d.use_yn,
                d.reg_dt as created_at,
                d.doc_txt
            FROM wisenut.doc_bas_lst d
            LEFT JOIN wisenut.com_cd_lv2 c
                ON c.level_n1_cd = 'DOC_CAT_CD'
                AND c.level_n2_cd = d.doc_cat_cd
            WHERE d.doc_id = $1
            """,
            int(document_id)
        )

        if not row:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

        # file_path는 detail level들을 조합
        file_path = []
        if row['doc_det_level_n1_cd']:
            file_path.append(row['doc_det_level_n1_cd'])
        if row['doc_det_level_n2_cd']:
            file_path.append(row['doc_det_level_n2_cd'])
        if row['doc_det_level_n3_cd']:
            file_path.append(row['doc_det_level_n3_cd'])

        return {
            "id": str(row['doc_id']),
            "title": row['title'],
            "file_path": file_path,
            "metadata_uri": "",  # EDB에는 없음
            "doctype": row['doctype'] or "기타",
            "doctype_name": row['doctype_name'],  # 카테고리명 추가
            "token_count": row['token_count'],
            "is_active": row['use_yn'] == 'Y',
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "content": row['doc_txt'][:1000] if row['doc_txt'] else "",  # 첫 1000자만
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vector document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 조회 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


# TODO: 벡터 문서 생성/수정/삭제는 별도의 문서 업로드 파이프라인을 통해 처리
# @router.post("")
# @router.put("/{document_id}")
# @router.delete("/{document_id}")
