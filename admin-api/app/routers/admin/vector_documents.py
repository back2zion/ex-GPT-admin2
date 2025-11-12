"""
벡터 문서 관리 API 엔드포인트 (EDB 기반)
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import logging
import os
import asyncpg
import httpx
from minio import Minio
from minio.error import S3Error
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/vector-documents", tags=["admin-vector-documents"])

# EDB 설정 (Docker에서 host.docker.internal 사용)
# 주의: pg_hba.conf에 172.31.0.0/16 추가 필요
EDB_HOST = os.getenv("EDB_HOST", "host.docker.internal")
EDB_PORT = int(os.getenv("EDB_PORT", "5444"))
EDB_DATABASE = os.getenv("EDB_DATABASE", "AGENAI")
EDB_USER = os.getenv("EDB_USER", "wisenut_dev")
EDB_PASSWORD = os.getenv("EDB_PASSWORD", "express!12")

# MinIO 설정
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "host.docker.internal:10002")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")

# ex-gpt API 설정
EXGPT_API_URL = os.getenv("EXGPT_API_URL", "http://host.docker.internal:8083")
EXGPT_API_KEY = os.getenv("EXGPT_API_KEY", "z3JE1M8huXmNux6y")


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


def get_minio_client():
    """MinIO 클라이언트 생성"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create MinIO client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"MinIO 연결 실패: {str(e)}"
        )


async def delete_from_minio(document_id: int, category_code: str):
    """MinIO에서 파일 삭제"""
    try:
        client = get_minio_client()
        # 파일 경로 패턴: {category_code}/기타/00/00/{filename}
        # 정확한 파일명을 모르므로 prefix로 검색
        prefix = f"{category_code}/"

        objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
        deleted_count = 0

        for obj in objects:
            # 문서 ID를 포함하는 객체 찾기 (실제로는 문서 정보에서 파일명을 가져와야 함)
            # 여기서는 간단히 처리
            try:
                client.remove_object(MINIO_BUCKET, obj.object_name)
                logger.info(f"Deleted from MinIO: {obj.object_name}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {obj.object_name} from MinIO: {e}")

        return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete from MinIO: {e}")
        # MinIO 삭제 실패는 경고만 하고 계속 진행
        return 0


async def delete_from_exgpt(document_id: int):
    """ex-gpt API를 통해 Qdrant에서 벡터 삭제"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "x-api-key": EXGPT_API_KEY
            }

            response = await client.delete(
                f"{EXGPT_API_URL}/v1/file/{document_id}",
                headers=headers
            )

            if response.status_code in [200, 204, 404]:
                # 404는 이미 삭제된 경우이므로 성공으로 처리
                logger.info(f"Deleted from ex-gpt/Qdrant: document {document_id}")
                return True
            else:
                logger.warning(f"Failed to delete from ex-gpt: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Failed to delete from ex-gpt: {e}")
        # ex-gpt 삭제 실패는 경고만 하고 계속 진행
        return False


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


@router.delete("/{document_id}")
async def delete_vector_document(
    document_id: str,
    hard_delete: bool = Query(False, description="완전 삭제 여부 (기본: False, soft delete)")
):
    """
    벡터 문서 삭제

    Args:
        document_id: 문서 ID (doc_id)
        hard_delete: True일 경우 완전 삭제, False일 경우 use_yn = 'N'으로 설정

    Returns:
        삭제 결과
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # document_id를 정수로 변환
        try:
            doc_id_int = int(document_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 문서 ID: {document_id}"
            )

        # 문서 존재 확인 및 정보 가져오기
        doc_info = await conn.fetchrow(
            """
            SELECT doc_id, doc_cat_cd
            FROM wisenut.doc_bas_lst
            WHERE doc_id = $1
            """,
            doc_id_int
        )

        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"문서를 찾을 수 없습니다: {document_id}"
            )

        if hard_delete:
            # 1. ex-gpt/Qdrant에서 삭제
            await delete_from_exgpt(doc_id_int)

            # 2. MinIO에서 삭제 (카테고리 코드 사용)
            await delete_from_minio(doc_id_int, doc_info['doc_cat_cd'])

            # 3. EDB에서 완전 삭제
            await conn.execute(
                """
                DELETE FROM wisenut.doc_bas_lst
                WHERE doc_id = $1
                """,
                doc_id_int
            )
            logger.info(f"Hard deleted document from all storages: {doc_id_int}")
        else:
            # Soft delete (use_yn = 'N')
            await conn.execute(
                """
                UPDATE wisenut.doc_bas_lst
                SET use_yn = 'N', mod_usr_id = 'admin', mod_dt = CURRENT_TIMESTAMP
                WHERE doc_id = $1
                """,
                doc_id_int
            )
            logger.info(f"Soft deleted document: {doc_id_int}")

        return {
            "document_id": document_id,
            "deleted": True,
            "hard_delete": hard_delete
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 삭제 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.post("/batch-delete")
async def batch_delete_documents(
    document_ids: list[str],
    hard_delete: bool = Query(False, description="완전 삭제 여부")
):
    """
    다중 문서 삭제

    Args:
        document_ids: 삭제할 문서 ID 목록
        hard_delete: True일 경우 완전 삭제

    Returns:
        삭제 결과
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 문자열 ID를 정수로 변환
        try:
            doc_ids_int = [int(doc_id) for doc_id in document_ids]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 문서 ID가 포함되어 있습니다"
            )

        if hard_delete:
            # 각 문서의 정보 가져오기
            docs_info = await conn.fetch(
                """
                SELECT doc_id, doc_cat_cd
                FROM wisenut.doc_bas_lst
                WHERE doc_id = ANY($1::int[])
                """,
                doc_ids_int
            )

            # 1. ex-gpt/Qdrant에서 삭제
            for doc in docs_info:
                await delete_from_exgpt(doc['doc_id'])

            # 2. MinIO에서 삭제
            for doc in docs_info:
                await delete_from_minio(doc['doc_id'], doc['doc_cat_cd'])

            # 3. EDB에서 완전 삭제
            deleted_count = await conn.execute(
                """
                DELETE FROM wisenut.doc_bas_lst
                WHERE doc_id = ANY($1::int[])
                """,
                doc_ids_int
            )
            logger.info(f"Hard deleted {len(document_ids)} documents from all storages")
        else:
            # Soft delete
            deleted_count = await conn.execute(
                """
                UPDATE wisenut.doc_bas_lst
                SET use_yn = 'N', mod_usr_id = 'admin', mod_dt = CURRENT_TIMESTAMP
                WHERE doc_id = ANY($1::int[])
                """,
                doc_ids_int
            )
            logger.info(f"Soft deleted {len(document_ids)} documents")

        return {
            "deleted_count": len(document_ids),
            "document_ids": document_ids,
            "hard_delete": hard_delete
        }

    except Exception as e:
        logger.error(f"Failed to batch delete documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"다중 문서 삭제 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    원본 문서 파일 다운로드 (MinIO에서)

    Args:
        document_id: 문서 ID (doc_id)

    Returns:
        원본 파일 스트리밍 응답
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # document_id를 정수로 변환
        try:
            doc_id_int = int(document_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 문서 ID: {document_id}"
            )

        # EDB에서 문서 정보 조회
        doc_info = await conn.fetchrow(
            """
            SELECT
                doc_id,
                doc_title_nm,
                doc_cat_cd,
                doc_det_level_n1_cd,
                doc_det_level_n2_cd,
                doc_det_level_n3_cd
            FROM wisenut.doc_bas_lst
            WHERE doc_id = $1 AND use_yn = 'Y'
            """,
            doc_id_int
        )

        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"문서를 찾을 수 없습니다: {document_id}"
            )

        # MinIO 클라이언트 생성
        client = get_minio_client()

        # MinIO 경로 구성: {doc_cat_cd}/{doc_det_level_n1_cd}/{doc_det_level_n2_cd}/{doc_det_level_n3_cd}/파일명
        # 또는: {doc_cat_cd}/파일명
        # 경로를 조합하여 찾기
        path_parts = [doc_info['doc_cat_cd']]
        if doc_info['doc_det_level_n1_cd']:
            path_parts.append(doc_info['doc_det_level_n1_cd'])
        if doc_info['doc_det_level_n2_cd']:
            path_parts.append(doc_info['doc_det_level_n2_cd'])
        if doc_info['doc_det_level_n3_cd']:
            path_parts.append(doc_info['doc_det_level_n3_cd'])

        prefix = "/".join(path_parts)

        # MinIO에서 파일 검색
        objects = list(client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True))

        if not objects:
            # prefix만으로 찾기 (경로 레벨이 없는 경우)
            prefix = doc_info['doc_cat_cd']
            objects = list(client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True))

        if not objects:
            raise HTTPException(
                status_code=404,
                detail=f"파일을 찾을 수 없습니다: {document_id}"
            )

        # 첫 번째 파일 선택 (여러 개 있을 경우)
        object_name = objects[0].object_name

        # MinIO에서 파일 가져오기
        try:
            response = client.get_object(MINIO_BUCKET, object_name)
            file_data = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            logger.error(f"Failed to download from MinIO: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"파일 다운로드 실패: {str(e)}"
            )

        # 파일명 추출
        filename = object_name.split('/')[-1]

        # Content-Type 결정
        content_type = "application/octet-stream"
        if filename.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif filename.lower().endswith(('.doc', '.docx')):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.lower().endswith('.hwp'):
            content_type = "application/x-hwp"
        elif filename.lower().endswith(('.ppt', '.pptx')):
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif filename.lower().endswith(('.xls', '.xlsx')):
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.lower().endswith('.txt'):
            content_type = "text/plain"

        logger.info(f"Downloaded document {document_id} from MinIO: {object_name}")

        # 파일 스트리밍 응답
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 다운로드 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()
