import requests
import pandas as pd
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import logging
import json
from typing import Optional, List, Dict
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaMetricsCollector:
    def __init__(
        self,
        kafka_metrics_url: str,
        influxdb_url: str,
        influxdb_token: str,
        org: str,
        bucket: str
    ):
        self.kafka_metrics_url = kafka_metrics_url
        self.client = InfluxDBClient(
            url=influxdb_url,
            token=influxdb_token,
            org=org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        self.org = org
        
        # 중요 메트릭 리스트
        self.important_metrics = [
            'kafka_server_brokertopicmetrics_messagesin_total',
            'kafka_server_brokertopicmetrics_bytesin_total',
            'kafka_server_brokertopicmetrics_bytesout_total',
            'kafka_server_replicamanager_partitioncount',
            'kafka_server_replicamanager_leadercount',
            'kafka_server_replicamanager_offlinereplicacount',
            'kafka_server_replicamanager_underreplicatedpartitions'
        ]

    def get_kafka_metrics(self) -> Optional[pd.DataFrame]:
        """Kafka 메트릭을 수집하여 DataFrame으로 반환"""
        try:
            response = requests.get(self.kafka_metrics_url)
            response.raise_for_status()

            metrics = []
            current_time = datetime.utcnow()

            for line in response.text.splitlines():
                if not line or line.startswith('#'):
                    continue

                try:
                    metric_name, value_str = line.rsplit(' ', 1)
                    metric_name = metric_name.strip()
                    
                    # 중요 메트릭만 필터링
                    if not any(important in metric_name for important in self.important_metrics):
                        continue
                    
                    try:
                        value = float(value_str)
                    except ValueError:
                        continue

                    metrics.append({
                        'metric': metric_name,
                        'value': value,
                        'timestamp': current_time
                    })

                except ValueError:
                    continue

            return pd.DataFrame(metrics)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Kafka metrics: {e}")
            return None

    def prepare_influxdb_points(self, df: pd.DataFrame) -> List[Point]:
        """DataFrame을 InfluxDB Point 객체로 변환"""
        points = []
        
        for _, row in df.iterrows():
            point = Point("kafka_metrics") \
                .field("value", row['value']) \
                .tag("metric", row['metric']) \
                .time(row['timestamp'])
            points.append(point)
            
        return points

    def write_to_influxdb(self, points: List[Point]) -> None:
        """데이터를 InfluxDB에 저장"""
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"Successfully wrote {len(points)} points to InfluxDB")
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def collect_and_store(self) -> None:
        """메트릭 수집 및 저장 실행"""
        df = self.get_kafka_metrics()
        
        if df is not None and not df.empty:
            points = self.prepare_influxdb_points(df)
            self.write_to_influxdb(points)
        else:
            logger.warning("No metrics data available")

    def run_collection_loop(self, interval_seconds: int = 60) -> None:
        """주기적으로 메트릭 수집 및 저장"""
        logger.info(f"Starting metrics collection loop with {interval_seconds}s interval")
        
        while True:
            try:
                self.collect_and_store()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Stopping metrics collection")
                break
            except Exception as e:
                logger.error(f"Unexpected error in collection loop: {e}")
                time.sleep(interval_seconds)

def load_config(config_path: str = "/data/config.json") -> Dict:
    """설정 파일 로드"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("Successfully loaded config file")
            return config
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        raise

def main():
    # 설정 파일 로드
    config = load_config()
    
    collector = KafkaMetricsCollector(
        kafka_metrics_url=config["KAFKA_METRICS_URL"],
        influxdb_url=config["INFLUXDB_URL"],
        influxdb_token=config["INFLUXDB_TOKEN"],
        org=config["INFLUXDB_ORG"],
        bucket=config["INFLUXDB_BUCKET"]
    )

    collector.run_collection_loop(config.get("COLLECTION_INTERVAL", 60))

if __name__ == "__main__":
    main()