import json
from influxdb_client import InfluxDBClient
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, List

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaMetricsViewer:
    def __init__(self, config_path: str = "/Users/inyong/twin-datapond/examples/config.json"):
        """설정 파일을 로드하여 InfluxDB 클라이언트 초기화"""
        self.config = self.load_config(config_path)
        self.client = InfluxDBClient(
            url=self.config["INFLUXDB_URL"],
            token=self.config["INFLUXDB_TOKEN"],
            org=self.config["INFLUXDB_ORG"]
        )
        self.bucket = self.config["INFLUXDB_BUCKET"]
        self.query_api = self.client.query_api()

    @staticmethod
    def load_config(config_path: str) -> Dict:
        """설정 파일 로드"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def get_recent_metrics(self, hours: int = 1) -> pd.DataFrame:
        """최근 N시간 동안의 모든 메트릭 조회"""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "kafka_metrics")
            |> pivot(rowKey:["_time"], columnKey: ["metric"], valueColumn: "_value")
        '''
        try:
            result = self.query_api.query_data_frame(query)
            if isinstance(result, list):
                result = pd.concat(result)
            logger.info(f"Successfully retrieved metrics for the last {hours} hours")
            return result
        except Exception as e:
            logger.error(f"Error querying recent metrics: {e}")
            return pd.DataFrame()

    def get_metric_statistics(self, metric_name: str, hours: int = 1) -> Dict:
        """특정 메트릭의 통계 정보 조회"""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "kafka_metrics")
            |> filter(fn: (r) => r["metric"] == "{metric_name}")
            |> yield(name: "raw")
        '''
        try:
            result = self.query_api.query_data_frame(query)
            if isinstance(result, list):
                result = pd.concat(result)
            
            if result.empty:
                return {}

            stats = {
                "mean": result["_value"].mean(),
                "min": result["_value"].min(),
                "max": result["_value"].max(),
                "std": result["_value"].std(),
                "count": len(result),
                "last_value": result["_value"].iloc[-1] if not result.empty else None,
                "timestamp_range": f"{result['_time'].min()} to {result['_time'].max()}"
            }
            
            logger.info(f"Successfully calculated statistics for {metric_name}")
            return stats
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def get_rate_of_change(self, metric_name: str, minutes: int = 5) -> float:
        """메트릭의 변화율 계산 (특히 _total 메트릭에 유용)"""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{minutes}m)
            |> filter(fn: (r) => r["_measurement"] == "kafka_metrics")
            |> filter(fn: (r) => r["metric"] == "{metric_name}")
            |> first()
        '''
        try:
            first = self.query_api.query_data_frame(query)
            
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{minutes}m)
                |> filter(fn: (r) => r["_measurement"] == "kafka_metrics")
                |> filter(fn: (r) => r["metric"] == "{metric_name}")
                |> last()
            '''
            last = self.query_api.query_data_frame(query)
            
            if isinstance(first, list):
                first = pd.concat(first)
            if isinstance(last, list):
                last = pd.concat(last)
            
            if not first.empty and not last.empty:
                time_diff = (last['_time'].iloc[0] - first['_time'].iloc[0]).total_seconds()
                value_diff = last['_value'].iloc[0] - first['_value'].iloc[0]
                rate = value_diff / time_diff if time_diff > 0 else 0
                logger.info(f"Successfully calculated rate of change for {metric_name}")
                return rate
            return 0
        except Exception as e:
            logger.error(f"Error calculating rate of change: {e}")
            return 0

def main():
    viewer = KafkaMetricsViewer()

    # 1. 최근 메트릭 조회
    print("\n=== Recent Metrics (Last Hour) ===")
    recent_metrics = viewer.get_recent_metrics(hours=1)
    print(recent_metrics.tail())

    # 2. 주요 메트릭들의 통계 정보 출력
    important_metrics = [
        'kafka_server_brokertopicmetrics_messagesin_total',
        'kafka_server_replicamanager_partitioncount',
        'kafka_server_replicamanager_underreplicatedpartitions'
    ]

    print("\n=== Metric Statistics ===")
    for metric in important_metrics:
        stats = viewer.get_metric_statistics(metric)
        print(f"\nStatistics for {metric}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    # 3. 변화율 계산 (특히 _total 메트릭에 대해)
    print("\n=== Rates of Change (per second) ===")
    rate = viewer.get_rate_of_change('kafka_server_brokertopicmetrics_messagesin_total')
    print(f"Messages in rate: {rate:.2f} messages/second")

if __name__ == "__main__":
    main()