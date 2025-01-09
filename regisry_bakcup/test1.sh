#!/bin/bash

BACKUP_POD="registry-backup"
BACKUP_DIR="/backup/var/lib/registry/docker/registry/v2/repositories/sewio/uwb"
IMAGES="core phpmyadmin redis rtls-io sewiodb"

for IMAGE in $IMAGES; do
    echo "Processing $IMAGE..."
    
    # 매니페스트 파일 찾기
    MANIFEST_FILE=$(kubectl exec $BACKUP_POD -n ark -- find $BACKUP_DIR/$IMAGE -name "current" -type f)
    
    if [ -z "$MANIFEST_FILE" ]; then
        echo "Manifest file not found for $IMAGE. Skipping..."
        continue
    fi
    
    # 매니페스트 내용 가져오기
    MANIFEST=$(kubectl exec $BACKUP_POD -n ark -- cat $MANIFEST_FILE)
    
    # 레이어 정보 추출
    LAYERS=$(echo $MANIFEST | jq -r '.layers[].digest')
    
    # 임시 Dockerfile 생성
    echo "FROM scratch" > Dockerfile.tmp
    for LAYER in $LAYERS; do
        echo "ADD $LAYER /" >> Dockerfile.tmp
    done
    
    # Dockerfile을 사용하여 이미지 빌드
    docker build -t sewio/uwb/$IMAGE:reconstructed -f Dockerfile.tmp .
    
    echo "Image sewio/uwb/$IMAGE:reconstructed has been created."
done

echo "All images have been processed."