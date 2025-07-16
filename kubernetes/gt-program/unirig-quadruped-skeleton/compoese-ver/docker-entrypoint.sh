#!/bin/bash

# UniRig 서비스 엔트리포인트 스크립트
set -e

echo "UniRig Automatic Rigging Service 시작 중..."

# GPU 사용 가능 여부 확인
if command -v nvidia-smi &> /dev/null; then
    echo "GPU 정보:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
else
    echo "GPU를 사용할 수 없습니다. CPU 모드로 실행됩니다."
fi

# CUDA 환경 확인
echo "CUDA 환경:"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-'not set'}"
python -c "import torch; print(f'PyTorch 버전: {torch.__version__}'); print(f'CUDA 사용 가능: {torch.cuda.is_available()}'); print(f'CUDA 디바이스 수: {torch.cuda.device_count()}')" 2>/dev/null || echo "PyTorch CUDA 체크 실패"

# 필요한 디렉토리가 존재하는지 확인
echo "디렉토리 확인 중..."
for dir in "/app/models" "/app/temp" "/app/static" "/app/logs"; do
    if [ ! -d "$dir" ]; then
        echo "$dir 생성 중..."
        mkdir -p "$dir"
    fi
done

# UniRig 소스코드 확인
if [ ! -d "/app/unirig" ]; then
    echo "UniRig 소스코드를 찾을 수 없습니다."
    exit 1
fi

# UniRig inference 스크립트 확인
if [ ! -f "/app/unirig/inference.py" ]; then
    echo "UniRig inference.py를 찾을 수 없습니다."
    exit 1
fi

# 기본 모델 파일 확인
if [ ! -f "/app/models/unirig.pth" ]; then
    echo "기본 UniRig 모델 파일이 없습니다."
    echo "모델을 다운로드하거나 볼륨 마운트를 통해 제공해주세요."
    echo "   예시: docker run -v /path/to/model:/app/models ..."
fi

# 로그 디렉토리 권한 설정
chmod -R 755 /app/logs /app/temp

# 환경 변수 설정
export PYTHONPATH="/app/unirig:$PYTHONPATH"

echo "초기화 완료!"
echo "서비스가 http://0.0.0.0:8000 에서 실행됩니다."
echo "API 문서는 http://localhost:8000/docs 에서 확인하세요."

# 전달받은 명령어 실행
exec "$@"