from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from delta import configure_spark_with_delta_pip
import json
import logging

# DeltaLake 포함한 SparkSession 생성

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SparkSession 생성
try:
    builder = SparkSession.builder \
        .appName("KafkaSparkStructuredStreaming") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    logger.info("SparkSession created successfully")
except Exception as e:
    logger.error("Failed to create SparkSession: %s", e)
    raise

# 메시지의 스키마 정의
schema = StructType([
    StructField("id", IntegerType()),
    StructField("type", StringType()),
    StructField("confidence", DoubleType())
])

# Kafka에서 스트리밍 데이터 읽기
try:
    kafkaDF = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "10.80.0.3:9094") \
        .option("subscribe", "spark-test") \
        .load()
except Exception as e:
    logger.error("Failed to read streaming data from Kafka: %s", e)
    raise

# Kafka 데이터 파싱
try:
    parsedDF = kafkaDF.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), schema).alias("data")) \
        .select("data.*")
    logger.info("Successfully parsed Kafka data")
except Exception as e:
    logger.error("Failed to parse Kafka data: %s", e)
    raise

# 데이터 필터링 (예시: confidence가 0.9 이상인 데이터 필터링)
filteredDF = parsedDF.filter(col("confidence") >= 0.9)

# Delta Lake 테이블 경로 설정 (로컬 경로)
delta_table_path = '/mnt/ceph-pvc/srv/delta-stream-table'
checkpoint_path = '/mnt/ceph-pvc/srv/checkpoints'

# Delta Lake 테이블 초기화 (배치 데이터 사용)
try:
    # 경로가 이미 존재하는지 확인
    from pathlib import Path
    delta_table_dir = Path(delta_table_path)
    if not delta_table_dir.exists():
        # 임시 배치 데이터프레임 생성
        init_df = spark.createDataFrame([], schema)
        init_df.write.format("delta").mode("overwrite").save(delta_table_path)
        spark.sql("CREATE TABLE delta_table USING DELTA LOCATION '{}'".format(delta_table_path))
        logger.info("Delta Lake table initialized successfully")
    else:
        logger.info("Delta Lake table already exists")
except Exception as e:
    logger.error("Failed to initialize Delta Lake table: %s", e)
    raise

# Delta Lake에 스트리밍 데이터 쓰기 및 콘솔에 출력하기
try:
    query = filteredDF.writeStream \
        .outputMode("append") \
        .format("delta") \
        .option("checkpointLocation", checkpoint_path) \
        .option("path", delta_table_path) \
        .trigger(processingTime='1 second') \
        .start()
    logger.info("Started writing streaming data to Delta Lake")
except Exception as e:
    logger.error("Failed to write streaming data to Delta Lake: %s", e)
    raise

# 콘솔 출력 설정
try:
    console_query = filteredDF.writeStream \
        .outputMode("append") \
        .format("console") \
        .trigger(processingTime='1 second') \
        .start()
    logger.info("Started console output configuration")
except Exception as e:
    logger.error("Failed console output configuration: %s", e)
    raise

try:
    query.awaitTermination()
    console_query.awaitTermination()
except Exception as e:
    logger.error("Error during streaming query execution: %s", e)
    raise
