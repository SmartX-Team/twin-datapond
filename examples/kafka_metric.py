import requests
import pandas as pd
from datetime import datetime

def get_kafka_metrics(metrics_url="http://localhost:9404/metrics"):
    try:
        response = requests.get(metrics_url)
        response.raise_for_status()

        metrics = []

        for line in response.text.splitlines():
            line = line.strip()
            # 주석(#)이거나 빈 줄은 스킵
            if not line or line.startswith('#'):
                continue

            # 메트릭 이름(라벨 포함)과 값 사이를 마지막 공백으로 분리
            parts = line.rsplit(' ', 1)
            if len(parts) != 2:
                continue

            metric_name, metric_value_str = parts
            metric_name = metric_name.strip()
            metric_value_str = metric_value_str.strip()

            # Prometheus 출력에서 종종 '-' 같은 비수치 문자가 들어올 수 있음
            if metric_value_str == '-':
                continue

            try:
                metric_value = float(metric_value_str)
            except ValueError:
                # float 변환 실패 시(예: 'NaN', '-', 문자열 등) 해당 라인 스킵
                continue

            metrics.append({
                'metric': metric_name,
                'value': metric_value,
                'timestamp': datetime.now()
            })

        df = pd.DataFrame(metrics)

        # 중요 메트릭 필터링
        important_metrics = [
            'kafka_server_brokertopicmetrics_messagesin_total',
            'kafka_server_brokertopicmetrics_bytesin_total',
            'kafka_server_brokertopicmetrics_bytesout_total',
            'kafka_server_replicamanager_partitioncount',
            'kafka_server_replicamanager_leadercount',
            'kafka_server_replicamanager_offlinereplicacount',
            'kafka_server_replicamanager_underreplicatedpartitions'
        ]

        # metric 컬럼에 위 키워드가 포함된(contains) 행만 필터
        filtered_df = df[df['metric'].str.contains('|'.join(important_metrics), regex=True)]

        return filtered_df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics: {e}")
        return None

def print_metrics_summary(df):
    if df is not None and not df.empty:
        print("\n=== Kafka Metrics Summary ===")
        for _, row in df.iterrows():
            print(f"{row['metric']}: {row['value']}")
    else:
        print("No metrics data available")

if __name__ == "__main__":
    # Kafka broker의 JMX Exporter 엔드포인트 URL
    METRICS_URL = "http://10.80.0.6:9404/metrics"  # 실제 URL로 변경
    
    metrics_df = get_kafka_metrics(METRICS_URL)
    print_metrics_summary(metrics_df)
