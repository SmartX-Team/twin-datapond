# UniRig Automatic Rigging Service Dockerfile
# GPU 지원을 위한 NVIDIA CUDA 베이스 이미지 사용
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 메타데이터
LABEL maintainer="UniRig Service"
LABEL description="AI-powered automatic rigging service using UniRig"
LABEL version="1.0.0"

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV GPU_DEVICE_ID=0

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 기본 명령어를 python3.10으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 디렉토리 생성
RUN mkdir -p /app/models /app/temp /app/static /app/logs /app/resources/templates /app/resources/static/css /app/resources/static/js

# UniRig 소스코드 클론
RUN git clone https://github.com/VAST-AI-Research/UniRig.git /app/unirig

# PyTorch 및 기본 의존성 설치 (CUDA 12.1 호환)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# UniRig 의존성 설치
WORKDIR /app/unirig
# bpy 버전 호환성 문제 해결
RUN sed -i 's/bpy==4.2/bpy==4.0.0/g' requirements.txt
# flash_attn 빌드를 위한 추가 의존성 설치
RUN pip install --no-cache-dir packaging wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# 추가 CUDA 관련 패키지 설치
RUN pip install --no-cache-dir \
    torch-scatter \
    torch-sparse \
    torch-cluster \
    torch-spline-conv \
    torch-geometric \
    -f https://data.pyg.org/whl/torch-2.1.0+cu121.html

# FastAPI 및 웹 서비스 의존성 설치
RUN pip install --no-cache-dir \
    fastapi[all] \
    uvicorn[standard] \
    python-multipart \
    aiofiles \
    jinja2

# 작업 디렉토리를 /app으로 다시 변경
WORKDIR /app

# 애플리케이션 파일들 복사
COPY api.py /app/
COPY docker-entrypoint.sh /app/
COPY resources/ /app/resources/

# static 파일들을 올바른 위치로 복사
RUN cp -r /app/resources/static/* /app/static/ 2>/dev/null || true

# 엔트리포인트 스크립트 실행 권한 부여
RUN chmod +x /app/docker-entrypoint.sh

# 기본 UniRig 모델 다운로드 (선택사항)
# 주석 해제하여 기본 모델을 이미지에 포함시킬 수 있습니다
# RUN wget -O /app/models/unirig.pth "https://huggingface.co/VAST-AI/UniRig/resolve/main/unirig.pth"

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 볼륨 마운트 포인트 설정
VOLUME ["/app/models", "/app/temp", "/app/logs"]

# 엔트리포인트 설정
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# 기본 명령어
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]