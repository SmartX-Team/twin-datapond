# 기존 코드에서 DeltaLake 통합까지 테스트용으로 사용한 예제 코드


from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from delta import configure_spark_with_delta_pip
import json
import logging
# DeltaLake 포함한 SparkSession 생성

# config.json 파일에서 나머지 설정 읽기
config_path = '/mnt/ceph-pvc/srv/config.json'

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

endpoint_url = ''
access_key = ''
secret_key = ''
bucket_name = ''
try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        endpoint_url = config['minio']['endpoint_url']
        access_key = config['minio']['access_key']
        secret_key = config['minio']['secret_key']
        bucket_name = config['minio']['bucket_name']
except Exception as e:
    logger.error("Failed to load config file: %s", e)
    raise

try:
    builder = SparkSession.builder \
        .appName("KafkaSparkStructuredStreaming") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.access.key", access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
        .config("spark.hadoop.fs.s3a.endpoint", endpoint_url) \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.trust-all-certificates", "true") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws-3.3.4,com.amazonaws:aws-java-sdk-bundle-1.12.262")

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    logger.info("SparkSession created successfully")
except Exception as e:
    logger.error("Failed to create SparkSession: %s", e)
    raise

# Define schema for messages
schema = StructType([
    StructField("id", IntegerType()),
    StructField("type", StringType()),
    StructField("confidence", DoubleType())
])

# Read streaming data from Kafka
try:
    kafkaDF = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "10.80.0.3:9094") \
        .option("subscribe", "spark-test") \
        .load()
except Exception as e:
    logger.error("Failed to read streaming data from Kafka: %s", e)
    raise

# Kafka 데이터는 기본적으로 key와 value가 바이너리로 제공됩니다.
# 이들을 문자열로 변환하고 JSON으로 파싱합니다. From ChatGpt
try:
    parsedDF = kafkaDF.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), schema).alias("data")) \
        .select("data.*")
    logger.info("Successfully parsed Kafka data")
except Exception as e:
    logger.error("Failed to parse Kafka data: %s", e)
    raise

# 데이터 변환 및 처리 (예시처럼: confidence가 0.9 이상인 데이터 필터링)
filteredDF = parsedDF.filter(col("confidence") >= 0.9)

# Delta Lake 테이블 경로 설정
delta_table_path = f"s3a://{bucket_name}/delta-stream-table"
checkpoint_path = f"s3a://{bucket_name}/checkpoints"

# Initialize Delta Lake table (using batch data)
try:
    if not spark._jsparkSession.catalog().tableExists("delta.`{}`".format(delta_table_path)):
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

# 테스트 용으로 콘솔에 데이터를 출력한다.
# 에제에서는 콘솔에 출력하고 데이터를 버린다.
# 기본 Default 설정으로는 500ms 마다 스트리밍으로 수집한 데이터를 처리한다. 해당 옵션으로 배치 처리 주기를 조절할 수 있다. 
# .trigger(processingTime='1 second') \
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

# Console output configuration
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