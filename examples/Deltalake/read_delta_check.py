# -*- coding: utf-8 -*-
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_utc_timestamp, to_utc_timestamp

# MinIO 설정 (사용 환경에 맞춰 변경)
MINIO_ENDPOINT = "http://10.79.1.0:9000"
MINIO_ACCESS_KEY = "YYFfYYBbYyGREfMIU2oI"
MINIO_SECRET_KEY = "0ddqNkGrdKI46x5MYq5gEPYqfFgqsycAQiOBHH73"
MINIO_BUCKET_NAME = "twin-bucket"
DELTA_TABLE_PATH = f"s3a://{MINIO_BUCKET_NAME}/delta-stream-table"

def main():
    builder = (
        SparkSession.builder
        .appName("DeltaTableCheckTimezone")
        # S3 + Delta 연동용 설정
        .config("spark.jars.packages", ",".join([
            "org.apache.hadoop:hadoop-aws:3.3.4",
            "com.amazonaws:aws-java-sdk-bundle:1.12.262",
            "io.delta:delta-spark_2.12:3.3.0"
        ]))
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")  # http라면 false
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    session_tz = spark.conf.get("spark.sql.session.timeZone")
    print(f"[INFO] Current Spark session timeZone: {session_tz}")

    print(f"Reading Delta table from: {DELTA_TABLE_PATH} ...")
    df = spark.read.format("delta").load(DELTA_TABLE_PATH)

    print("[INFO] Printing schema:")
    df.printSchema()

    print("[INFO] Showing up to 30 rows (untruncated):")
    df.show(30, False)

    # df.dtypes 로도 확인 가능
    print("[INFO] dtypes:", df.dtypes)

    print("[INFO] Counting all rows:")
    total_count = df.count()
    print(f"Total rows in table: {total_count}")

    print("\n[DEBUG] Inspecting time zone interpretation for @timestamp ...")
    # from_utc_timestamp(ts, 'Asia/Seoul') -> ts가 "UTC 기준"이라고 가정하고 KST로 변환
    # to_utc_timestamp(ts, 'Asia/Seoul')   -> ts가 "KST(Asia/Seoul) 기준"이라고 가정하고 UTC로 변환
    tz_df = df.select(
        col("@timestamp").alias("raw_ts"),
        from_utc_timestamp(col("@timestamp"), "Asia/Seoul").alias("as_KST_if_raw_was_UTC"),
        to_utc_timestamp(col("@timestamp"), "Asia/Seoul").alias("as_UTC_if_raw_was_KST"),
    )
    tz_df.show(30, False)

    # 간단히 몇 건만 "1분 전보다 과거인지" 테스트
    # 주의: current_timestamp()는 세션 타임존 기준으로 잡히고,
    #       @timestamp는 내부적으로 UTC로 해석될 수도 있으므로, 결괏값이 예상과 다를 수 있음
    print("[DEBUG] Filtering for records older than (current_timestamp - 1 minute) ...")
    older_than_1m = df.where("`@timestamp` <= (current_timestamp() - interval 1 minute)")
    older_count = older_than_1m.count()
    print(f"Records older than 1 minute: {older_count}")
    older_than_1m.show(10, False)

    spark.stop()

if __name__ == "__main__":
    sys.exit(main())
