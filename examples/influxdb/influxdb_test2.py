import pandas as pd
from influxdb_client import InfluxDBClient
# from influxdb_client.client.write_api import SYNCHRONOUS # 분석에는 쓰기 API 불필요
from datetime import timedelta, datetime, timezone # 시간 관련 임포트

# --- InfluxDB 설정 ---
# 데이터를 수집하는 스크립트와 동일한 정보 사용
# 단, TOKEN은 해당 버킷에 대한 읽기(Read) 권한만 있어도 충분합니다.
INFLUX_URL = "http://10.79.1.9:8086" 
INFLUX_TOKEN = "f2BxCKixuq79cFQjz9RO2X_jUG5BCBsye31GPKFDJ8o9gwwEa99mEHsLU2VSIHB4T3GznqpD8BzpNXA1HHt7dg=="  # <--- 실제 Token으로 변경! (읽기 권한 필요)
INFLUX_ORG = "GIST"      # <--- 실제 Org 이름으로 변경!
INFLUX_BUCKET = "SV4000#2"  # <--- 실제 Bucket 이름으로 변경!
# ---------------------

# <<--- 수정 시작 --->>

# 1. 기준 시간 설정 (UTC 기준)
#    실제 실험을 시작하거나 종료한 시점의 정확한 타임스탬프를 입력합니다.
#    예시: 'YYYY-MM-DD HH:MM:SS' 형식. InfluxDB는 UTC를 사용하므로 UTC 시간 권장.
#1. reference_time_str_kst = '2025-04-02 14:26:30'  # <--- 실제 실험의 '한국 시간'으로 변경하세요! (예: KST 오전 11시 47분 43초)
reference_time_str_kst = '2025-04-02 15:01:10'

try:
    # 한국 시간(KST, UTC+9) 타임존 정보 생성
    kst = timezone(timedelta(hours=9), name='KST')
    
    # 입력된 한국 시간 문자열을 datetime 객체로 변환하고, KST 타임존 정보를 명시적으로 부여
    reference_dt_kst = datetime.strptime(reference_time_str_kst, '%Y-%m-%d %H:%M:%S').replace(tzinfo=kst)
    
    # KST 시간을 UTC 시간으로 변환
    reference_dt_utc = reference_dt_kst.astimezone(timezone.utc)
    
    # 사용자 확인용 출력 (입력한 KST와 변환된 UTC)
    print(f"Input KST time: {reference_dt_kst.isoformat()}")
    print(f"Converted UTC time for query: {reference_dt_utc.isoformat()}") 

except ValueError:
    print(f"Error: Invalid date format for reference_time_str_kst: '{reference_time_str_kst}'. Use 'YYYY-MM-DD HH:MM:SS'.")
    exit()

# 2. 조회할 시간 범위 계산 (변환된 UTC 시간 기준 datetime 객체 사용)
# 시나리오 1: 기준 시간(UTC)부터 + 5분 (예: 접속 후 5분간 활발히 사용한 데이터)
print(f"Analyzing data for 5 minutes starting from {reference_dt_utc.isoformat()}...")
time_range_start_dt = reference_dt_utc
time_range_stop_dt = reference_dt_utc + timedelta(minutes=1)

# 시나리오 2: 기준 시간(UTC) - 5분부터 기준 시간(UTC)까지 (예: 종료 전 5분간 활발히 사용한 데이터)
# print(f"Analyzing data for 5 minutes ending at {reference_dt_utc.isoformat()}...")
# time_range_start_dt = reference_dt_utc - timedelta(minutes=5)
# time_range_stop_dt = reference_dt_utc 
# <<--- 수정 끝 --->>


# --- 이하 코드는 동일 ---
# Flux 쿼리용 시간 포맷 (RFC3339)
time_range_start = time_range_start_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
time_range_stop = time_range_stop_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')

# 조회할 호스트 이름 (특정 호스트만 보려면 설정, 모든 호스트 데이터는 None)
target_host = "netai" # 'netai' 호스트 데이터만 조회
# target_host = None # 모든 호스트 데이터 조회
# ---------------------

def query_network_data(client: InfluxDBClient, bucket: str, org: str, start: str, stop: str, host: str = None):
    """InfluxDB에서 네트워크 트래픽 데이터를 조회하여 DataFrame으로 반환"""
    query_api = client.query_api()

    # Flux 쿼리 작성
    flux_query = f'''
    from(bucket: "{bucket}")
      |> range(start: {start}, stop: {stop})
      |> filter(fn: (r) => r["_measurement"] == "network_traffic")
      |> filter(fn: (r) => r["_field"] == "rx_mibps" or r["_field"] == "tx_mibps")
    '''
    if host:
        flux_query += f' |> filter(fn: (r) => r["host"] == "{host}")'

    # 피벗: _field 값을 컬럼으로 변환 (rx_mibps, tx_mibps 컬럼 생성)
    flux_query += '''
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> keep(columns: ["_time", "host", "interfaces", "rx_mibps", "tx_mibps"]) 
      |> yield(name: "results")
    '''

    print("--- Executing Flux Query ---")
    print(flux_query)
    print("-----------------------------")

    try:
        # DataFrame으로 결과 받기
        df = query_api.query_data_frame(query=flux_query, org=org)
        
        # 시간 컬럼(_time)을 DataFrame 인덱스로 설정 (datetime 타입 변환 포함)
        if not df.empty and '_time' in df.columns:
            df['_time'] = pd.to_datetime(df['_time'])
            df = df.set_index('_time')
            # 필요시 로컬 시간대로 변환: 
            # df.index = df.index.tz_convert('Asia/Seoul') 
        
        return df
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return pd.DataFrame() # 오류 시 빈 DataFrame 반환

def analyze_data(df: pd.DataFrame):
    """DataFrame을 받아 간단한 분석 수행"""
    if df.empty:
        print("No data found for the specified parameters.")
        return

    print("\n--- Data Summary ---")
    print(f"Total records fetched: {len(df)}")
    if not df.index.empty:
        print(f"Time range in data: {df.index.min()} to {df.index.max()}")
    
    print("\n--- First 5 Records ---")
    print(df.head())

    # 기본 통계
    print("\n--- Basic Statistics (MiBps) ---")
    try:
        # .loc[:,슬라이싱]을 사용하여 숫자형 컬럼만 안전하게 선택
        numeric_df = df.loc[:, ['rx_mibps', 'tx_mibps']] 
        print(numeric_df.describe())
    except KeyError:
        print("Could not find numeric columns 'rx_mibps' or 'tx_mibps'.")
    except Exception as e:
        print(f"Error during describe(): {e}")

    # 평균값
    print("\n--- Average Traffic (MiBps) ---")
    try:
        numeric_df = df.loc[:, ['rx_mibps', 'tx_mibps']]
        print(numeric_df.mean())
    except KeyError:
         print("Could not find numeric columns 'rx_mibps' or 'tx_mibps'.")
    except Exception as e:
        print(f"Error during mean(): {e}")
        
    # 최대값
    print("\n--- Maximum Traffic (MiBps) ---")
    try:
        numeric_df = df.loc[:, ['rx_mibps', 'tx_mibps']]
        print(numeric_df.max())
    except KeyError:
         print("Could not find numeric columns 'rx_mibps' or 'tx_mibps'.")
    except Exception as e:
        print(f"Error during max(): {e}")

    # 여기에 추가 분석 로직 구현 가능
    # 예: 시간대별 집계 (df.resample('1Min').mean()), 시각화 (matplotlib 사용) 등

if __name__ == "__main__":
    # InfluxDB 클라이언트 초기화
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

    # 데이터 조회
    traffic_df = query_network_data(influx_client, INFLUX_BUCKET, INFLUX_ORG, 
                                     time_range_start, time_range_stop, target_host)

    # 데이터 분석
    analyze_data(traffic_df)

    # 클라이언트 종료
    influx_client.close()
    print("\nAnalysis complete.")