#!/bin/bash

# UniRig 자동 리깅 서비스 설정 스크립트
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "UniRig 자동 리깅 서비스 설정 시작"

# 필요한 도구들 설치 확인
check_requirements() {
    echo "필수 도구 확인 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker가 설치되어 있지 않습니다."
        echo "Docker 설치: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "ERROR: Docker Compose가 설치되어 있지 않습니다."
        echo "Docker Compose 설치: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # NVIDIA Docker 확인 (GPU 사용시)
    if command -v nvidia-smi &> /dev/null; then
        if ! docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            echo "WARNING: NVIDIA Container Toolkit이 설치되어 있지 않거나 설정되지 않았습니다."
            echo "설치 가이드: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
            echo "NOTE: CPU 모드로도 실행할 수 있습니다."
        else
            echo "OK: GPU 지원 환경 확인됨"
        fi
    else
        echo "INFO: GPU가 감지되지 않아 CPU 모드로 실행됩니다."
    fi
    
    echo "필수 도구 확인 완료"
}

# 프로젝트 디렉토리 구조 생성
setup_directories() {
    echo "디렉토리 구조 생성 중..."
    
    # 필요한 디렉토리들 생성
    mkdir -p models temp logs static
    
    echo "디렉토리 구조 생성 완료"
}

# UniRig 모델 다운로드
download_model() {
    echo "UniRig 모델 다운로드 중..."
    
    MODEL_PATH="./models/unirig.pth"
    
    if [ -f "$MODEL_PATH" ]; then
        echo "OK: 모델 파일이 이미 존재합니다: $MODEL_PATH"
        return 0
    fi
    
    echo "기본 UniRig 모델을 다운로드합니다..."
    echo "INFO: 모델은 약 1-2GB 크기입니다."
    
    # Hugging Face에서 모델 다운로드 (실제 URL은 UniRig 문서 확인 필요)
    MODEL_URL="https://huggingface.co/VAST-AI/UniRig/resolve/main/unirig.pth"
    
    if command -v wget &> /dev/null; then
        wget -O "$MODEL_PATH" "$MODEL_URL" || {
            echo "ERROR: 모델 다운로드 실패"
            echo "NOTE: 수동으로 다운로드하여 $MODEL_PATH 에 배치해주세요"
            return 1
        }
    elif command -v curl &> /dev/null; then
        curl -L -o "$MODEL_PATH" "$MODEL_URL" || {
            echo "ERROR: 모델 다운로드 실패"
            echo "NOTE: 수동으로 다운로드하여 $MODEL_PATH 에 배치해주세요"
            return 1
        }
    else
        echo "ERROR: wget 또는 curl이 필요합니다"
        echo "NOTE: 수동으로 다운로드하여 $MODEL_PATH 에 배치해주세요"
        return 1
    fi
    
    echo "OK: 모델 다운로드 완료"
}

# Docker 이미지 빌드
build_image() {
    echo "Docker 이미지 빌드 중..."
    
    if [ ! -f "Dockerfile" ]; then
        echo "ERROR: Dockerfile을 찾을 수 없습니다"
        exit 1
    fi
    
    docker build -t unirig-service:latest . || {
        echo "ERROR: Docker 이미지 빌드 실패"
        exit 1
    }
    
    echo "OK: Docker 이미지 빌드 완료"
}

# 서비스 시작
start_service() {
    echo "서비스 시작 중..."
    
    # 기존 컨테이너 정리
    docker-compose down 2>/dev/null || true
    
    # 서비스 시작
    docker-compose up -d || {
        echo "ERROR: 서비스 시작 실패"
        exit 1
    }
    
    echo "OK: 서비스가 시작되었습니다"
    echo "웹 인터페이스: http://localhost:8000"
    echo "API 문서: http://localhost:8000/docs"
    echo "헬스체크: http://localhost:8000/health"
}

# 서비스 상태 확인
check_service() {
    echo "서비스 상태 확인 중..."
    
    sleep 5  # 서비스 시작 대기
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "OK: 서비스가 정상적으로 실행 중입니다"
    else
        echo "WARNING: 서비스 헬스체크 실패"
        echo "로그 확인: docker-compose logs -f"
    fi
}

# 메인 실행 함수
main() {
    echo "======================================"
    echo "UniRig 자동 리깅 서비스 설정"
    echo "======================================"
    
    check_requirements
    setup_directories
    
    # 모델 다운로드 (선택사항)
    echo ""
    read -p "기본 모델을 다운로드하시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        download_model
    else
        echo "모델 다운로드를 건너뛰었습니다."
        echo "NOTE: ./models/unirig.pth 파일을 수동으로 배치해주세요"
    fi
    
    build_image
    start_service
    check_service
    
    echo ""
    echo "======================================"
    echo "설정 완료!"
    echo "======================================"
    echo "서비스 URL: http://localhost:8000"
    echo "로그 확인: docker-compose logs -f"
    echo "서비스 중지: docker-compose down"
    echo "======================================"
}

# 스크립트 실행
main "$@"