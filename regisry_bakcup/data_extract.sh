#!/bin/bash

REGISTRY_POD=$(kubectl get pods -n ark -l app=docker-registry -o jsonpath="{.items[0].metadata.name}")
BACKUP_POD="registry-backup"
REGISTRY_DATA="/var/lib/registry/docker/registry/v2/repositories/sewio/uwb"
BACKUP_DIR="/backup"

# 1. Registry 파드에서 데이터 추출 및 backup 파드로 전송
echo "Transferring data from registry pod to backup pod..."
kubectl exec $REGISTRY_POD -n ark -- tar czf - $REGISTRY_DATA | kubectl exec -i $BACKUP_POD -n ark -- tar xzf - -C $BACKUP_DIR

echo "Data transfer complete. Verifying transferred data..."

# 2. Backup 파드에서 전송된 데이터 확인
kubectl exec $BACKUP_POD -n ark -- ls -R $BACKUP_DIR/var/lib/registry/docker/registry/v2/repositories/sewio/uwb

echo "Data transfer and verification complete."