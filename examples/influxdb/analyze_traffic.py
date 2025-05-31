import pandas as pd
from influxdb_client import InfluxDBClient
from datetime import timedelta, datetime, timezone
import csv # CSV 모듈 임포트
import os  # 파일 존재 여부 확인 위해 임포트

# --- InfluxDB 설정 ---
# (이전과 동일)
INFLUX_URL = "http://10.79.1.9:8086" 
INFLUX_TOKEN = "f2BxCKixuq79cFQjz9RO2X_jUG5BCBsye31GPKFDJ8o9gwwEa99mEHsLU2VSIHB4T3GznqpD8BzpNXA1HHt7dg=="
INFLUX_ORG = "GIST"      
INFLUX_BUCKET = "SV4000#2"  
# ---------------------

# --- 분석 파라미터 ---
# <<--- 수정 시작 --->>
# 1. 실험 조건 설정 (실행할 때마다 변경)
experiment_label = "HD_Active_Run3" # 예: 실험 구분용 라벨
resolution = "Full-HD"                  # 예: 해상도 정보 ("4K" 또는 "FHD")

# 2. 기준 시간 설정 (한국 시간 KST, UTC+9 기준)
reference_time_str_kst = '2025-04-02 15:19:50'  # <--- 실험 시작 또는 종료 시간 (KST)
analysis_duration_minutes = 1 # 예: 분석할 시간(분)

output_csv_filepath = "/Users/inyong/twin-datapond/examples/influxdb/my_experiment_results_hd.csv"
# <<--- 수정 끝 --->>

try:
    kst = timezone(timedelta(hours=9), name='KST')
    reference_dt_kst = datetime.strptime(reference_time_str_kst, '%Y-%m-%d %H:%M:%S').replace(tzinfo=kst)
    reference_dt_utc = reference_dt_kst.astimezone(timezone.utc)
    print(f"Input KST time: {reference_dt_kst.isoformat()}")
    print(f"Converted UTC time for query: {reference_dt_utc.isoformat()}")
except ValueError:
    print(f"Error: Invalid date format for reference_time_str_kst: '{reference_time_str_kst}'. Use 'YYYY-MM-DD HH:MM:SS'.")
    exit()

# 3. 조회할 시간 범위 계산 (시작 시간 기준 + duration) - 필요시 로직 수정 가능
print(f"Analyzing data for {analysis_duration_minutes} minutes starting from {reference_dt_utc.isoformat()}...")
time_range_start_dt = reference_dt_utc
time_range_stop_dt = reference_dt_utc + timedelta(minutes=analysis_duration_minutes)

# Flux 쿼리용 시간 포맷 변환
time_range_start = time_range_start_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
time_range_stop = time_range_stop_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')

target_host = "netai" 
# ---------------------

# === 함수 정의 시작 ===

def query_network_data(client: InfluxDBClient, bucket: str, org: str, start: str, stop: str, host: str = None):
    """InfluxDB에서 네트워크 트래픽 데이터를 조회하여 DataFrame으로 반환"""
    query_api = client.query_api()
    flux_query = f'''
    from(bucket: "{bucket}")
      |> range(start: {start}, stop: {stop})
      |> filter(fn: (r) => r["_measurement"] == "network_traffic")
      |> filter(fn: (r) => r["_field"] == "rx_mibps" or r["_field"] == "tx_mibps")
    '''
    if host:
        flux_query += f' |> filter(fn: (r) => r["host"] == "{host}")'
    flux_query += '''
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> keep(columns: ["_time", "host", "interfaces", "rx_mibps", "tx_mibps"]) 
      |> yield(name: "results")
    '''
    print("--- Executing Flux Query ---")
    print(flux_query)
    print("-----------------------------")
    try:
        df = query_api.query_data_frame(query=flux_query, org=org)
        if not df.empty and '_time' in df.columns:
            df['_time'] = pd.to_datetime(df['_time'], errors='coerce') 
            df = df.dropna(subset=['_time'])
            if not df.empty:
                 df = df.set_index('_time')
        return df
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return pd.DataFrame() 

def analyze_data(df: pd.DataFrame) -> dict:
    """DataFrame을 받아 간단한 분석 수행하고 결과 딕셔너리 반환"""
    results = { 
        "total_records": 0, "time_range_start": None, "time_range_end": None,
        "avg_rx_mibps": None, "avg_tx_mibps": None, "max_rx_mibps": None,
        "max_tx_mibps": None, "std_tx_mibps": None,
    }
    if df.empty:
        print("No data found for the specified parameters.")
        return results 
    results["total_records"] = len(df)
    if not df.index.empty:
        results["time_range_start"] = df.index.min()
        results["time_range_end"] = df.index.max()
    print("\n--- Data Summary ---")
    print(f"Total records fetched: {len(df)}")
    if results["time_range_start"]:
        print(f"Time range in data: {results['time_range_start']} to {results['time_range_end']}")
    print("\n--- First 5 Records ---")
    print(df.head())
    try:
        numeric_cols = [col for col in ['rx_mibps', 'tx_mibps'] if col in df.columns]
        if not numeric_cols:
             print("Numeric columns 'rx_mibps' or 'tx_mibps' not found.")
             return results
        numeric_df = df[numeric_cols] 
        print("\n--- Basic Statistics (MiBps) ---")
        print(numeric_df.describe())
        avg_traffic = numeric_df.mean()
        max_traffic = numeric_df.max()
        std_traffic = numeric_df.std()
        results.update({
            "avg_rx_mibps": avg_traffic.get('rx_mibps'), "avg_tx_mibps": avg_traffic.get('tx_mibps'),
            "max_rx_mibps": max_traffic.get('rx_mibps'), "max_tx_mibps": max_traffic.get('tx_mibps'),
            "std_tx_mibps": std_traffic.get('tx_mibps')
        })
        print("\n--- Average Traffic (MiBps) ---"); print(avg_traffic)
        print("\n--- Maximum Traffic (MiBps) ---"); print(max_traffic)
        print("\n--- Std Dev Traffic (MiBps) ---"); print(std_traffic)
    except Exception as e:
        print(f"Error during analysis: {e}")
    return results 

def save_results_to_csv(filepath: str, experiment_info: dict, analysis_results: dict):
    """분석 결과를 CSV 파일에 추가"""
    file_exists = os.path.exists(filepath)
    fieldnames = ['experiment_label', 'resolution', 'reference_time_kst', 'duration_minutes', 
                  'query_start_utc', 'query_end_utc', 'actual_data_start', 'actual_data_end', 
                  'total_records', 'avg_rx_mibps', 'avg_tx_mibps', 'max_rx_mibps', 'max_tx_mibps', 'std_tx_mibps']
    row_data = {
        'experiment_label': experiment_info.get('label'),
        'resolution': experiment_info.get('resolution'),
        'reference_time_kst': experiment_info.get('ref_time_kst'),
        'duration_minutes': experiment_info.get('duration'),
        'query_start_utc': experiment_info.get('query_start').isoformat(timespec='seconds') if experiment_info.get('query_start') else None,
        'query_end_utc': experiment_info.get('query_end').isoformat(timespec='seconds') if experiment_info.get('query_end') else None,
        'actual_data_start': analysis_results.get('time_range_start').isoformat(timespec='seconds') if analysis_results.get('time_range_start') else None,
        'actual_data_end': analysis_results.get('time_range_end').isoformat(timespec='seconds') if analysis_results.get('time_range_end') else None,
        'total_records': analysis_results.get('total_records'),
        'avg_rx_mibps': analysis_results.get('avg_rx_mibps'),
        'avg_tx_mibps': analysis_results.get('avg_tx_mibps'),
        'max_rx_mibps': analysis_results.get('max_rx_mibps'),
        'max_tx_mibps': analysis_results.get('max_tx_mibps'),
        'std_tx_mibps': analysis_results.get('std_tx_mibps'),
    }
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True) 
        with open(filepath, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader() 
            writer.writerow(row_data) 
        print(f"\nResults saved to {filepath}")
    except Exception as e:
        print(f"Error writing to CSV file {filepath}: {e}")

# === 함수 정의 끝 ===

# === 메인 실행 블록 ===
if __name__ == "__main__":
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    traffic_df = query_network_data(influx_client, INFLUX_BUCKET, INFLUX_ORG, 
                                     time_range_start, time_range_stop, target_host)
    results = analyze_data(traffic_df)
    influx_client.close()
    
    if results and results.get("total_records", 0) > 0: 
        # csv_filepath = "network_experiment_results.csv" # 이전 코드
        csv_filepath = output_csv_filepath # <--- 수정된 변수 사용
        experiment_info = {
            "label": experiment_label, "resolution": resolution,
            "ref_time_kst": reference_time_str_kst, "duration": analysis_duration_minutes,
            "query_start": time_range_start_dt, "query_end": time_range_stop_dt,
        }
        save_results_to_csv(csv_filepath, experiment_info, results) 

    print("\nAnalysis complete.")
# === 메인 실행 블록 끝 ===