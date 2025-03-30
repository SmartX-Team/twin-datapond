# 현재 사용중인 스파크 기반 이미지 베이스에 델타레이크 포맷 사용을 위한 도커 파일

FROM apache/spark:3.5.3

# Spark 버전이랑 호환성 체크한다고 로컬에서 다운받았는데 ADD로 바뀌도 상관 없음
#COPY spark-sql-kafka-0-10_2.12-3.5.1.jar /opt/spark/jars/
#COPY kafka-clients-3.5.2.jar /opt/spark/jars/
#COPY commons-pool2-2.11.1.jar /opt/spark/jars/
#COPY spark-token-provider-kafka-0-10_2.12-3.5.1.jar /opt/spark/jars/
#COPY delta-core_2.12-2.1.0.jar /opt/spark/jars/
#COPY delta-spark_2.12-3.2.0.jar /opt/spark/jars/
#COPY delta-storage-3.2.0.jar /opt/spark/jars/

# Add Delta Lake JAR
# --- Delta Lake 3.5.0 ---
ADD https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/io/delta/delta-storage/3.3.0/delta-storage-3.3.0.jar /opt/spark/jars/  
ADD https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.0/delta-spark_2.12-3.3.0.jar /opt/spark/jars/ 
    # --- Kafka Connectors (Assuming they are compatible with your Kafka brokers) ---
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar /opt/spark/jars/

ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.2/kafka-clients-3.5.2.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar /opt/spark/jars/

# 파이썬 라이브러리들 추가 설치

USER root


#delta 라이브러리 설치
RUN pip install delta-spark boto3 pandas pyarrow uuid botocore Pillow
#RUN chown -R spark:spark /home/spark/.cache

# MinIO 연동에 필요한 라이브러리

#ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.2.0/hadoop-aws-3.2.0.jar /opt/spark/jars/
#ADD https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.375/aws-java-sdk-bundle-1.11.375.jar /opt/spark/jars/
COPY hadoop-aws-3.3.4.jar /opt/spark/jars/
COPY aws-java-sdk-bundle-1.12.262.jar /opt/spark/jars/

RUN chmod -R 755 /opt/spark/jars/

USER spark