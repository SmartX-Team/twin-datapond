FROM apache/spark:3.5.0

# Spark 버전이랑 호환성 체크한다고 로컬에서 다운받았는데 ADD로 바뀌도 상관 없음
COPY spark-sql-kafka-0-10_2.12-3.5.1.jar /opt/spark/jars/
COPY kafka-clients-3.5.2.jar /opt/spark/jars/
COPY commons-pool2-2.11.1.jar /opt/spark/jars/
COPY spark-token-provider-kafka-0-10_2.12-3.5.1.jar /opt/spark/jars/

# Add Delta Lake JAR
ADD https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.1.0/delta-core_2.12-2.1.0.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/2.1.0/delta-spark_2.12-2.1.0.jar /opt/spark/jars/