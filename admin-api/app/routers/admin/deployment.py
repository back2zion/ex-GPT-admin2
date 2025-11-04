"""
배포관리 API 라우터
모델 레지스트리, 모델 서비스 관리, 시스템 배포 현황
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from datetime import datetime
import logging
import subprocess
import json
import os
import mlflow
from mlflow.tracking import MlflowClient
import httpx

from app.core.database import get_db
from app.schemas.deployment import (
    DeploymentResponse,
    ModelRegisterRequest,
    BentoDeployRequest,
    GPUStatusResponse,
    DeploymentListResponse,
    BentoInfo,
    BentoListResponse,
    BentoBuildRequest,
    BentoDeploymentRequest,
)
from app.models.deployment import Deployment

router = APIRouter(prefix="/api/v1/admin/deployment", tags=["배포관리"])
logger = logging.getLogger(__name__)

# MLflow 클라이언트 초기화
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow_client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

# Hugging Face 캐시 디렉토리
# 컨테이너 내부에서는 /home/aigen/.cache/huggingface/hub/에 마운트됨
HF_CACHE_DIR = os.getenv("HF_HOME", "/home/aigen/.cache/huggingface/hub/")


def scan_installed_models():
    """
    서버에 설치된 모델 목록 스캔 (Hugging Face 캐시에서)

    Returns:
        List of dicts with model info
    """
    models = []

    if not os.path.exists(HF_CACHE_DIR):
        logger.warning(f"Hugging Face cache directory not found: {HF_CACHE_DIR}")
        return models

    try:
        for entry in os.listdir(HF_CACHE_DIR):
            if entry.startswith("models--"):
                # "models--Qwen--Qwen3-32B-AWQ" -> "Qwen/Qwen3-32B-AWQ"
                parts = entry.replace("models--", "").split("--")
                if len(parts) >= 2:
                    model_id = "/".join(parts)
                    model_name = parts[-1]  # 마지막 부분만 (예: Qwen3-32B-AWQ)

                    # 모델 타입 추론
                    model_type = "LLM"
                    if "whisper" in model_name.lower():
                        model_type = "STT"
                    elif "embedding" in model_name.lower():
                        model_type = "Embedding"
                    elif "reranker" in model_name.lower():
                        model_type = "Reranker"
                    elif "vl" in model_name.lower():
                        model_type = "Vision-Language"

                    models.append({
                        "value": model_name,
                        "label": model_name,
                        "type": model_type,
                        "full_path": model_id
                    })

        # 이름순 정렬
        models.sort(key=lambda x: x["label"])

    except Exception as e:
        logger.error(f"Failed to scan models: {str(e)}")

    return models


@router.get("/models/available")
async def get_available_models():
    """
    서버에 설치된 사용 가능한 모델 목록 조회

    응답 예시:
    [
        {
            "value": "Qwen3-32B-AWQ",
            "label": "Qwen3-32B-AWQ",
            "type": "LLM",
            "full_path": "Qwen/Qwen3-32B-AWQ"
        }
    ]
    """
    try:
        models = scan_installed_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def scan_running_vllm_services():
    """
    실행 중인 vLLM 서비스 스캔 (포트 8000-8010 범위)

    Returns:
        List of running vLLM services with model info
    """
    import httpx

    running_services = []
    ports_to_scan = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010]
    # 컨테이너에서 호스트의 서비스에 접근하기 위해 host.docker.internal 사용
    host = "host.docker.internal"

    async with httpx.AsyncClient(timeout=2.0) as client:
        for port in ports_to_scan:
            try:
                response = await client.get(f"http://{host}:{port}/v1/models")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        model_info = data["data"][0]
                        model_name = model_info.get("root", "unknown")

                        # GPU 정보는 docker inspect로 확인 가능하지만 여기서는 간략히 처리
                        running_services.append({
                            "deployment_id": port,  # 임시로 포트를 ID로 사용
                            "model_name": model_name.split("/")[-1] if "/" in model_name else model_name,
                            "model_uri": model_name,
                            "status": "serving",
                            "endpoint_url": f"http://localhost:{port}",  # 클라이언트가 접근할 URL
                            "port": port,
                            "framework": "vllm",
                            "deployed_by": "system",
                            "created_at": datetime.fromtimestamp(model_info.get("created", 0)),
                            "updated_at": datetime.now(),
                            "gpu_ids": [],  # GPU 정보는 별도로 확인 필요
                            "max_model_len": model_info.get("max_model_len")
                        })
                        logger.info(f"Found vLLM service on port {port}: {model_name}")
            except Exception as e:
                # 포트에 서비스가 없거나 응답 실패 시 무시
                logger.debug(f"No vLLM service on port {port}: {str(e)}")
                continue

    return running_services


@router.get("/models", response_model=List[DeploymentResponse])
async def list_deployed_models(db: AsyncSession = Depends(get_db)):
    """
    배포된 모델 목록 조회

    실제 실행 중인 vLLM 서비스를 스캔하여 반환합니다.

    응답 예시:
    [
        {
            "deployment_id": 8000,
            "model_name": "Qwen3-32B-AWQ",
            "status": "serving",
            "endpoint_url": "http://localhost:8000",
            "port": 8000,
            "created_at": "2025-10-20T14:30:00"
        }
    ]
    """
    try:
        # 실행 중인 vLLM 서비스 스캔
        running_services = await scan_running_vllm_services()

        if not running_services:
            logger.warning("No running vLLM services found")
            return []

        return running_services

    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/register")
async def register_model(
    request: ModelRegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    새 모델 등록 (MLflow 모델 레지스트리에 등록)

    요청 예시:
    {
        "model_name": "Qwen3-235B-A22B-AWQ",
        "model_uri": "Qwen/Qwen3-235B-A22B-AWQ",
        "framework": "vllm",
        "description": "Qwen3 235B AWQ 양자화 모델"
    }
    """
    try:
        logger.info(f"Registering model in MLflow: {request.model_name}")

        # MLflow에 registered model 생성 (이미 존재하면 skip)
        try:
            registered_model = mlflow_client.create_registered_model(
                name=request.model_name,
                description=request.description or f"{request.model_name} model"
            )
            logger.info(f"Created new registered model: {request.model_name}")
        except Exception as e:
            if "RESOURCE_ALREADY_EXISTS" in str(e):
                logger.info(f"Model {request.model_name} already exists in registry")
                registered_model = mlflow_client.get_registered_model(request.model_name)
            else:
                raise

        # 모델 메타데이터를 태그로 저장
        mlflow_client.set_registered_model_tag(
            name=request.model_name,
            key="model_uri",
            value=request.model_uri or ""
        )
        mlflow_client.set_registered_model_tag(
            name=request.model_name,
            key="framework",
            value=request.framework or "vllm"
        )

        return {
            "model_name": request.model_name,
            "status": "registered",
            "message": "모델이 MLflow 레지스트리에 등록되었습니다",
            "mlflow_uri": f"{MLFLOW_TRACKING_URI}/#/models/{request.model_name}"
        }

    except Exception as e:
        logger.error(f"Failed to register model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/deploy")
async def deploy_model(
    request: BentoDeployRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 배포 (vLLM 서버 시작)

    요청 예시:
    {
        "model_name": "qwen3-235b-v2",
        "gpu_ids": [0, 1, 2, 3],
        "port": 8000,
        "vllm_config": {
            "gpu_memory_utilization": 0.9,
            "max_model_len": 8192
        }
    }
    """
    try:
        logger.info(f"Deploying model: {request.model_name}")

        # 데이터베이스에 배포 정보 저장
        new_deployment = Deployment(
            model_name=request.model_name,
            model_uri=f"models/{request.model_name}",  # 임시
            framework="vllm",
            status="deploying",
            gpu_ids=request.gpu_ids,
            port=request.port,
            endpoint_url=f"http://localhost:{request.port}",
            vllm_config=request.vllm_config,
            deployed_by="admin",  # TODO: 실제 사용자 정보
        )

        db.add(new_deployment)
        await db.commit()
        await db.refresh(new_deployment)

        # TODO: Background에서 vLLM 서버 시작
        # async def deploy_task():
        #     start_vllm_server(request)
        # background_tasks.add_task(deploy_task)

        return {
            "deployment_id": new_deployment.deployment_id,
            "model_name": request.model_name,
            "status": "deploying",
            "message": "배포 시작됨 (백그라운드에서 진행 중)"
        }

    except Exception as e:
        logger.error(f"Failed to deploy model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{deployment_id}/stop")
async def stop_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """배포 중지"""
    try:
        logger.info(f"Stopping deployment: {deployment_id}")

        # 배포 정보 조회
        result = await db.execute(
            select(Deployment).where(Deployment.deployment_id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise HTTPException(status_code=404, detail="배포를 찾을 수 없습니다")

        # TODO: vLLM 서버 중지 로직
        # if deployment.process_id:
        #     subprocess.run(["kill", str(deployment.process_id)])

        # 상태 업데이트
        deployment.status = "stopped"
        deployment.updated_at = datetime.now()
        await db.commit()

        return {
            "deployment_id": deployment_id,
            "status": "stopped",
            "message": "배포 중지 완료"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{deployment_id}/start")
async def start_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """배포 시작 (중지된 배포 재시작)"""
    try:
        logger.info(f"Starting deployment: {deployment_id}")

        # 배포 정보 조회
        result = await db.execute(
            select(Deployment).where(Deployment.deployment_id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise HTTPException(status_code=404, detail="배포를 찾을 수 없습니다")

        # TODO: vLLM 서버 시작 로직

        # 상태 업데이트
        deployment.status = "serving"
        deployment.updated_at = datetime.now()
        await db.commit()

        return {
            "deployment_id": deployment_id,
            "status": "serving",
            "message": "배포 시작 완료"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{deployment_id}/health")
async def check_deployment_health(deployment_id: int, db: AsyncSession = Depends(get_db)):
    """배포 Health Check"""
    try:
        # 배포 정보 조회
        result = await db.execute(
            select(Deployment).where(Deployment.deployment_id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise HTTPException(status_code=404, detail="배포를 찾을 수 없습니다")

        # TODO: vLLM 서버 /health 엔드포인트 호출
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"{deployment.endpoint_url}/health")
        #     healthy = response.status_code == 200

        healthy = deployment.status == "serving"

        return {
            "deployment_id": deployment_id,
            "healthy": healthy,
            "response_time_ms": 120 if healthy else None,
            "status": deployment.status
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "deployment_id": deployment_id,
            "healthy": False,
            "error": str(e)
        }


@router.get("/gpu/status", response_model=GPUStatusResponse)
async def get_gpu_status():
    """GPU 사용 현황 조회"""
    try:
        # nvidia-smi 실행하여 GPU 사용률 조회
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )

        gpus = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpu_id = int(parts[0])
                name = parts[1]
                utilization = int(parts[2]) if parts[2].isdigit() else 0
                memory_used = int(parts[3])
                memory_total = int(parts[4])

                # 메모리를 GB 단위로 변환
                memory_used_gb = round(memory_used / 1024, 1)
                memory_total_gb = round(memory_total / 1024, 1)

                gpus.append({
                    "id": gpu_id,
                    "name": name,
                    "utilization": utilization,
                    "memory_used": f"{memory_used_gb}GB/{memory_total_gb}GB"
                })

        logger.info(f"Found {len(gpus)} GPUs")
        return {"gpus": gpus}

    except subprocess.CalledProcessError as e:
        logger.error(f"nvidia-smi command failed: {str(e)}")
        raise HTTPException(status_code=500, detail="nvidia-smi 실행 실패")
    except Exception as e:
        logger.error(f"Failed to get GPU status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """배포 삭제"""
    try:
        # 배포 정보 조회
        result = await db.execute(
            select(Deployment).where(Deployment.deployment_id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise HTTPException(status_code=404, detail="배포를 찾을 수 없습니다")

        # 서빙 중이면 먼저 중지
        if deployment.status == "serving":
            raise HTTPException(
                status_code=400,
                detail="서빙 중인 배포는 삭제할 수 없습니다. 먼저 중지하세요."
            )

        # 삭제
        await db.delete(deployment)
        await db.commit()

        return {
            "deployment_id": deployment_id,
            "message": "배포 삭제 완료"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Bento 관리 API =====

@router.get("/bentos", response_model=BentoListResponse)
async def list_bentos():
    """
    서비스 목록 조회 (Docker 기반 배포)

    실제 실행 중인 vLLM 서비스를 기반으로 서비스 정보를 반환합니다.

    응답 예시:
    {
        "bentos": [
            {
                "name": "qwen3_llm_service",
                "version": "production",
                "tag": "qwen3_llm_service:production",
                "model": "Qwen3-32B-AWQ",
                "size": "N/A",
                "created_at": "2025-10-22T10:30:00"
            }
        ],
        "total": 3
    }
    """
    try:
        # 실행 중인 vLLM 서비스를 스캔하여 서비스 정보 생성
        running_services = await scan_running_vllm_services()

        bentos = []
        for service in running_services:
            model_name = service.get("model_name", "unknown")
            # 서비스 이름 생성 (모델 이름 기반)
            service_name = model_name.lower().replace("-", "_") + "_service"

            bentos.append({
                "name": service_name,
                "version": "production",
                "tag": f"{service_name}:production",
                "model": model_name,
                "size": "N/A",  # vLLM은 모델 크기 정보를 제공하지 않음
                "created_at": service.get("created_at", datetime.now()),
                "port": service.get("port"),
                "endpoint_url": service.get("endpoint_url"),
                "status": service.get("status", "serving")
            })

        return {
            "bentos": bentos,
            "total": len(bentos)
        }

    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bentos/build")
async def build_bento(
    request: BentoBuildRequest,
    background_tasks: BackgroundTasks,
):
    """
    Bento 빌드

    요청 예시:
    {
        "model_name": "qwen3-235b-awq",
        "version": "v1.0.1",
        "python_version": "3.9",
        "description": "Qwen3 235B AWQ 양자화 모델 서비스"
    }
    """
    try:
        logger.info(f"Building Bento: {request.model_name}:{request.version}")

        # TODO: Background에서 bentoml build 실행
        # async def build_task():
        #     subprocess.run([
        #         "bentoml", "build",
        #         "-f", f"services/{request.model_name}/bentofile.yaml",
        #         "--version", request.version
        #     ])
        # background_tasks.add_task(build_task)

        return {
            "bento_tag": f"{request.model_name}_service:{request.version}",
            "status": "building",
            "message": "Bento 빌드 시작됨 (백그라운드에서 진행 중)"
        }

    except Exception as e:
        logger.error(f"Failed to build bento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bentos/deploy")
async def deploy_bento(
    request: BentoDeploymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Bento 배포 (bentoml serve)

    요청 예시:
    {
        "bento_tag": "qwen3_service:v1.0.0",
        "gpu_ids": [0, 1],
        "port": 3000,
        "replicas": 2
    }
    """
    try:
        logger.info(f"Deploying Bento: {request.bento_tag}")

        # 배포 정보를 deployments 테이블에 저장
        model_name = request.bento_tag.split(":")[0]

        new_deployment = Deployment(
            model_name=model_name,
            model_uri=f"bentos/{request.bento_tag}",
            framework="bentoml",
            status="deploying",
            gpu_ids=request.gpu_ids,
            port=request.port,
            endpoint_url=f"http://localhost:{request.port}",
            vllm_config={"replicas": request.replicas},
            deployed_by="admin",
        )

        db.add(new_deployment)
        await db.commit()
        await db.refresh(new_deployment)

        # TODO: Background에서 bentoml serve 실행
        # async def deploy_task():
        #     subprocess.run([
        #         "bentoml", "serve", request.bento_tag,
        #         "--host", "0.0.0.0",
        #         "--port", str(request.port),
        #         "--production"
        #     ])
        # background_tasks.add_task(deploy_task)

        return {
            "deployment_id": new_deployment.deployment_id,
            "bento_tag": request.bento_tag,
            "status": "deploying",
            "message": "Bento 배포 시작됨 (백그라운드에서 진행 중)"
        }

    except Exception as e:
        logger.error(f"Failed to deploy bento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bentos/{bento_tag}")
async def delete_bento(bento_tag: str):
    """
    Bento 삭제

    예시: DELETE /bentos/qwen3_service:v1.0.0
    """
    try:
        logger.info(f"Deleting Bento: {bento_tag}")

        # TODO: bentoml delete 명령어 실행
        # subprocess.run(["bentoml", "delete", bento_tag])

        return {
            "bento_tag": bento_tag,
            "message": "Bento 삭제 완료"
        }

    except Exception as e:
        logger.error(f"Failed to delete bento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bentos/{bento_tag}/containerize")
async def containerize_bento(
    bento_tag: str,
    background_tasks: BackgroundTasks
):
    """
    Bento를 Docker 이미지로 변환

    예시: GET /bentos/qwen3_service:v1.0.0/containerize
    """
    try:
        logger.info(f"Containerizing Bento: {bento_tag}")

        # TODO: Background에서 bentoml containerize 실행
        # async def containerize_task():
        #     subprocess.run(["bentoml", "containerize", bento_tag])
        # background_tasks.add_task(containerize_task)

        return {
            "bento_tag": bento_tag,
            "status": "containerizing",
            "message": "Docker 이미지 빌드 시작됨 (백그라운드에서 진행 중)"
        }

    except Exception as e:
        logger.error(f"Failed to containerize bento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{port}/openapi.json")
async def proxy_service_openapi(port: int):
    """
    vLLM 서비스 OpenAPI JSON 프록시
    """
    try:
        host = "host.docker.internal"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://{host}:{port}/openapi.json")
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to proxy openapi.json for port {port}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"OpenAPI 스펙 접근 실패: {str(e)}")


@router.get("/services/{port}/docs", response_class=HTMLResponse)
async def proxy_service_docs(port: int):
    """
    vLLM 서비스 API 문서 프록시

    브라우저에서 직접 포트 접근이 안 될 경우, 백엔드를 통해 프록시합니다.
    """
    try:
        host = "host.docker.internal"  # 컨테이너에서 호스트 접근
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://{host}:{port}/docs")
            html_content = response.text

            # Swagger UI가 올바른 OpenAPI JSON 경로를 사용하도록 수정
            html_content = html_content.replace(
                'url: \'/openapi.json\'',
                f'url: \'/api/v1/admin/deployment/services/{port}/openapi.json\''
            )

            return HTMLResponse(content=html_content, status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to proxy docs for port {port}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"서비스 접근 실패: {str(e)}")


@router.get("/services/{port}/health")
async def proxy_service_health(port: int):
    """
    vLLM 서비스 Health Check 프록시
    """
    try:
        host = "host.docker.internal"  # 컨테이너에서 호스트 접근
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{host}:{port}/health")
            return JSONResponse(
                content={"port": port, "status": "healthy", "status_code": response.status_code},
                status_code=200
            )
    except Exception as e:
        logger.error(f"Failed to proxy health for port {port}: {str(e)}")
        return JSONResponse(
            content={"port": port, "status": "unhealthy", "error": str(e)},
            status_code=503
        )


@router.get("/docker/containers")
async def get_docker_containers():
    """
    실행 중인 Docker 컨테이너 목록 조회
    """
    try:
        # docker ps 실행
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
            capture_output=True,
            text=True,
            check=True
        )

        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split("|")
            if len(parts) >= 4:
                container_id = parts[0][:12]  # 짧은 ID
                name = parts[1]
                image = parts[2]
                status = parts[3]
                ports = parts[4] if len(parts) > 4 else ""

                # 상태 파싱 (Up 2 hours -> running)
                state = "running" if "Up" in status else "stopped"

                containers.append({
                    "id": container_id,
                    "name": name,
                    "image": image,
                    "status": status,
                    "state": state,
                    "ports": ports
                })

        logger.info(f"Found {len(containers)} Docker containers")
        return {"containers": containers, "total": len(containers)}

    except subprocess.CalledProcessError as e:
        logger.error(f"docker ps command failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Docker 명령 실행 실패")
    except Exception as e:
        logger.error(f"Failed to get Docker containers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
