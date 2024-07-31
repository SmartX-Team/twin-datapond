from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# SparkSession 생성
spark = SparkSession.builder \
    .appName("KafkaSparkStructuredStreaming") \
    .getOrCreate()

# 메시지의 스키마 정의
schema = StructType([
    StructField("id", IntegerType()),
    StructField("type", StringType()),
    StructField("confidence", DoubleType())
])

# Kafka에서 스트리밍 데이터 읽기
kafkaDF = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "10.80.0.3:9094") \
    .option("subscribe", "spark-test") \
    .load()

# Kafka 데이터는 기본적으로 key와 value가 바이너리로 제공됩니다.
# 이들을 문자열로 변환하고 JSON으로 파싱합니다. From ChatGpt
parsedDF = kafkaDF.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

# 데이터 변환 및 처리 (예시처럼: confidence가 0.9 이상인 데이터 필터링)
filteredDF = parsedDF.filter(col("confidence") >= 0.9)

# 테스트 용으로 콘솔에 데이터를 출력한다.
# 에제에서는 콘솔에 출력하고 데이터를 버린다.
# 기본 Default 설정으로는 500ms 마다 스트리밍으로 수집한 데이터를 처리한다. 해당 옵션으로 배치 처리 주기를 조절할 수 있다. 
# .trigger(processingTime='1 second') \
query = filteredDF.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
