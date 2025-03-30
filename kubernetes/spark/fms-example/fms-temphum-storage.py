""""

K8S 환경에서 

FMS 서버로부터 센서 데이터를 카프카를 통해 스트리밍받고 -> 델타레이크 포맷으로 MinIO 에 축적하는 예제 코드
몇일동안  정상 동작하는거 확인

25.03.30 송인용

"""



from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
import uuid
import logging
import json
from io import BytesIO
import boto3
from botocore.client import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config.json 파일에서 설정 읽기
config_path = '/mnt/ceph-pvc/config.json'

try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

        # MinIO 설정
        minio_config = config['minio']
        minio_endpoint_url = minio_config['endpoint_url']
        minio_access_key = minio_config['access_key']
        minio_secret_key = minio_config['secret_key']
        minio_bucket_name = minio_config['bucket_name']

        # Kafka 설정
        kafka_config = config['kafka']
        kafka_bootstrap_servers = kafka_config['bootstrap.servers']
        kafka_topic = kafka_config['topic_name']

        # Delta Lake 설정 (MinIO 경로)
        delta_config = config['delta']
        delta_table_path = f"s3a://{minio_bucket_name}/delta-stream-table"
        checkpoint_path = f"s3a://{minio_bucket_name}/checkpoints"
except Exception as e:
    logger.error("Failed to load config file: %s", e)
    raise

# MinIO 연결 정보 설정
minio_endpoint = minio_endpoint_url
use_ssl = minio_endpoint_url.startswith("https://")

###################################
# 1. SparkSession 생성
###################################
try:
    builder = SparkSession.builder \
        .appName("KafkaSparkStructuredStreamingSensorData") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.access.key", minio_access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key) \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(use_ssl).lower()) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.trust-all-certificates", "true") \

    spark = builder.getOrCreate() 

    spark.sparkContext.setLogLevel("INFO")
    # Delta Lake 자동 스키마 병합 (필요 시)
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    logger.info("SparkSession created successfully")
except Exception as e:
    logger.error("Failed to create SparkSession: %s", e)
    raise

###################################
# 2. Delta 테이블 초기화 (스키마 정의)
###################################
# 센서 데이터 스키마
delta_schema = StructType([
    StructField("@timestamp", TimestampType(), True),
    StructField("objId", IntegerType(), True),
    StructField("rsctypeId", StringType(), True),
    StructField("TEMPERATURE", DoubleType(), True),
    StructField("TEMPERATURE1", DoubleType(), True),
    StructField("HUMIDITY", DoubleType(), True),
    StructField("HUMIDITY1", DoubleType(), True),
])

try:
    # Delta 테이블이 해당 경로에 이미 존재하는지 확인
    delta_table_exists = DeltaTable.isDeltaTable(spark, delta_table_path)
    
    if not delta_table_exists:
        # Delta 테이블 초기화
        empty_df = spark.createDataFrame([], delta_schema)
        empty_df.write.format("delta") \
            .mode("overwrite") \
            .save(delta_table_path)
        logger.info("Initialized Delta table with sensor data schema.")
    else:
        logger.info("Delta table already exists.")
except Exception as e:
    logger.error(f"Failed to initialize Delta table: {e}")
    raise

###################################
# 3. Kafka에서 스트리밍 데이터 읽기
###################################
try:
    kafkaDF = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "latest") \
        .load()
    logger.info("Successfully started reading from Kafka topic: %s", kafka_topic)
except Exception as e:
    logger.error("Failed to read streaming data from Kafka: %s", e)
    raise

###################################
# 4. foreachBatch 함수 정의
###################################
def parse_and_write_delta(batch_df, batch_id):
    """
    Kafka에서 가져온 JSON 메시지를 파싱하여 TimestampType으로 변환 후 Delta Lake에 저장
    """
    from pyspark.sql.functions import from_json, col, to_timestamp # to_timestamp 추가
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType # TimestampType 추가

    # 센서 데이터 스키마 (TimestampType으로 수정)
    sensor_schema = StructType([
        # '@timestamp'는 JSON에서 문자열로 오지만, 최종 Delta 테이블에는 Timestamp로 저장할 것임
        StructField("@timestamp", StringType(), True), # 원본 문자열 필드명 변경 (옵션)
        StructField("objId", IntegerType(), True),
        StructField("rsctypeId", StringType(), True),
        StructField("TEMPERATURE", DoubleType(), True),
        StructField("TEMPERATURE1", DoubleType(), True),
        StructField("HUMIDITY", DoubleType(), True),
        StructField("HUMIDITY1", DoubleType(), True),
    ])

    # Kafka value 파싱 (원본 스키마 사용)
    parsed_df = batch_df.select(
        from_json(col("value").cast("string"), sensor_schema).alias("data")
    ).select("data.*")

    # 실제 데이터가 있을 때만 처리
    if not parsed_df.rdd.isEmpty():
        # Timestamp 변환 및 최종 컬럼 선택
        final_df = parsed_df.withColumn(
            "@timestamp", # 최종 Delta 테이블에 저장될 컬럼명
            # ISO 8601 형식 ('yyyy-MM-dd'T'HH:mm:ss.SSS'Z') 문자열을 Timestamp로 변환
            to_timestamp(col("@timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
        ).select(
            "@timestamp", # 변환된 Timestamp 컬럼
            "objId",
            "rsctypeId",
            "TEMPERATURE",
            "TEMPERATURE1",
            "HUMIDITY",
            "HUMIDITY1"
            # 필요없는 @timestamp_str 컬럼은 제외
        )

        # Delta Lake에 적재 (append 모드)
        final_df.write.format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .option("checkpointLocation", checkpoint_path) \
            .save(delta_table_path)
        logger.info(f"[Batch {batch_id}] Wrote sensor data to Delta Lake with correct timestamp type.")
    else:
        logger.info(f"[Batch {batch_id}] No valid data in this batch.")

###################################
# 5. 스트리밍 쿼리 실행
###################################
try:
    query = kafkaDF.writeStream \
        .foreachBatch(parse_and_write_delta) \
        .start()
    logger.info("Started writing streaming sensor data to Delta Lake on MinIO")
except Exception as e:
    logger.error("Failed to start streaming query: %s", e)
    raise

###################################
# 6. 스트리밍 대기 (종료 방지)
###################################
try:
    query.awaitTermination()
except Exception as e:
    logger.error("Error during streaming query execution: %s", e)
    raise
