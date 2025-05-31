# 기본 이미지: Apache Spark 3.5.3
FROM apache/spark:3.5.3

# 작업 디렉토리 설정 (선택 사항)
WORKDIR /opt/spark

# 필요한 JAR 파일들을 /opt/spark/jars/ 디렉토리에 추가합니다.
# 이 JAR들은 SparkApplication YAML의 spec.deps.jars에도 local:/// 경로로 반영되어야 합니다.

# 1. Delta Lake JAR (Spark 3.5.3과 호환되는 Delta Lake 3.3.1 사용)
# 이전 버전 및 충돌 가능성 있는 Delta JAR들은 모두 제거하고, 호환되는 단일 버전 세트만 사용합니다.
# Delta Lake 3.3.1 (io.delta:delta-spark_2.12:3.3.1)
# 이 JAR 하나가 필요한 delta-storage 등을 포함하거나 의존성으로 가져옵니다.
# Spark 3.5.x용 Delta Lake 3.3.1 (Scala 2.12)
ADD https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.1/delta-spark_2.12-3.3.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.1/delta-spark_2.12-3.3.1.jar /opt/spark/jars/
# delta-storage.jar 추가 (delta-spark의 필수 의존성)
ADD https://repo1.maven.org/maven2/io/delta/delta-storage/3.3.1/delta-storage-3.3.1.jar /opt/spark/jars/

# 2. Kafka Connector JARs (Spark 3.5.3 용)
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.2/kafka-clients-3.5.2.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar /opt/spark/jars/

# 3. MinIO/S3 연동을 위한 Hadoop AWS JARs (Hadoop 3.3.x 호환)
# !!!!!! 로컬에 미리 다운로드 받아 COPY 하는 방식을 유지했는데, 나중에 새로 빌드할때 수정헤야함!!!!!!~
COPY hadoop-aws-3.3.4.jar /opt/spark/jars/
COPY aws-java-sdk-bundle-1.12.262.jar /opt/spark/jars/

# USER를 root로 변경하여 Python 라이브러리 설치 및 권한 변경
USER root

# 필요한 Python 라이브러리 설치
# - delta-spark 버전은 추가한 JAR 버전과 일치 (3.3.1)
# - boto3, pandas, pyarrow, botocore, Pillow는 애플리케이션 필요에 따라 설치
# - uuid는 Python 표준 라이브러리이므로 pip로 설치할 필요 없음
# - --no-cache-dir 옵션으로 이미지 크기 최적화
RUN pip install --no-cache-dir \
    delta-spark==3.3.1 \
    boto3 \
    pandas \
    pyarrow \
    botocore \
    Pillow

# JAR 파일 권한 설정 (선택 사항, 기본 이미지 권한으로 충분할 수 있음)
RUN chmod -R 755 /opt/spark/jars/

# USER를 다시 spark로 변경 (보안 모범 사례)
USER spark

# 애플리케이션 실행을 위한 기본 작업 디렉토리 (선택 사항)
# WORKDIR /opt/spark/work-dir