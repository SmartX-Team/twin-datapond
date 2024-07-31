#!/bin/bash

#Configure Directories
JAR_DIR="."

# 만약 디렉터리가 존재하지 않으면 생성
mkdir -p $JAR_DIR


# Prehibit errors
set -e -o pipefail

# 의존성 jar file list
JAR_FILES=(
    "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar"
    "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/2.4.1/kafka-clients-2.4.1.jar"
    "https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar"
)

for JAR_URL in "${JAR_FILES[@]}"; do
    JAR_FILE="$JAR_DIR/$(basename $JAR_URL)"
    if [ -f "$JAR_FILE" ]; then
        echo "파일이 이미 존재합니다: $JAR_FILE, 다운로드를 패스합니다."
    else
        wget -P $JAR_DIR $JAR_URL
        echo "다운로드 완료: $JAR_FILE"
    fi
done