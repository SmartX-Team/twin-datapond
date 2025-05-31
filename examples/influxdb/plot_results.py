import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker # Y축 눈금 서식 설정을 위해 임포트
import os

# --- 설정 ---
# CSV 파일 경로 (analyze_traffic.py에서 저장한 경로)
CSV_FILEPATH = "/Users/inyong/twin-datapond/examples/influxdb/my_experiment_results.csv" # <--- 실제 CSV 파일 경로로 변경하세요!

# 그래프에 포함할 해상도 필터링 ("4K", "FHD", 또는 None: 모두 포함)
FILTER_RESOLUTION = "4K" # <--- 분석/시각화할 해상도 지정 ('4K' 또는 'FHD')

# 생성될 그래프 이미지 파일 경로 및 이름
OUTPUT_FIGURE_PATH = f"/Users/inyong/twin-datapond/examples/influxdb/traffic_plot_{FILTER_RESOLUTION if FILTER_RESOLUTION else 'all'}.png" # <--- 저장될 이미지 파일 경로/이름

# --- 설정 끝 ---

def plot_traffic_results(csv_filepath, filter_resolution=None, output_filepath="traffic_plot.png"):
    """ CSV 파일에서 실험 결과를 읽어 막대 그래프를 생성하고 저장합니다. """

    # CSV 파일 존재 여부 확인
    if not os.path.exists(csv_filepath):
        print(f"Error: CSV file not found - {csv_filepath}")
        return

    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_filepath)
        print("--- Loaded Data from CSV ---")
        print(df.head())

        # 지정된 해상도로 데이터 필터링 (대소문자 구분 없이)
        if filter_resolution:
            df_filtered = df[df['resolution'].astype(str).str.upper() == filter_resolution.upper()].copy()
            # 그래프 제목 (영문)
            plot_title = f'Average Tx Traffic ({filter_resolution} Streaming, 1-Min Active Tests)'
            if df_filtered.empty:
                print(f"Error: No data found for resolution '{filter_resolution}' in {csv_filepath}")
                return
        else:
            df_filtered = df.copy()
            # 그래프 제목 (영문)
            plot_title = 'Average Tx Traffic (1-Min Active Tests)'

        print(f"\n--- Data to Plot (Filtered by Resolution: {filter_resolution if filter_resolution else 'All'}) ---")
        print(df_filtered[['experiment_label', 'avg_tx_mibps', 'std_tx_mibps']])

        if df_filtered.empty:
             print("No data to plot.")
             return
             
        # 결측치 처리
        df_filtered = df_filtered.dropna(subset=['avg_tx_mibps']) 
        df_filtered['std_tx_mibps'] = df_filtered['std_tx_mibps'].fillna(0) 

        # --- 막대 그래프 생성 ---
        fig, ax = plt.subplots(figsize=(10, 7)) # Figure 크기 조절 (가로, 세로 인치)

        # X축 레이블 설정 (experiment_label 사용)
        x_labels = df_filtered['experiment_label']
        x_positions = range(len(x_labels)) # 막대 위치

        # Y축 데이터 및 에러바 데이터
        avg_tx = df_filtered['avg_tx_mibps']
        std_tx = df_filtered['std_tx_mibps']

        # 막대 그래프 그리기
        bars = ax.bar(x_positions, avg_tx, 
                      yerr=std_tx, 
                      capsize=5, 
                      color='skyblue',
                      label='Avg Tx Traffic (MiBps)') # 범례용 라벨 (영문)

        # --- 그래프 서식 설정 (영문) ---
        ax.set_ylabel('Average Tx Traffic (MiBps)') # Y축 레이블 (영문)
        ax.set_xlabel('Experiment Label')           # X축 레이블 (영문)
        ax.set_title(plot_title, fontsize=14)       # 제목 (영문), 폰트 크기 조절 가능
        
        ax.set_xticks(x_positions) 
        ax.set_xticklabels(x_labels, rotation=30, ha="right") # X축 레이블 회전하여 겹침 방지

        # Y축 눈금 서식 설정 (소수점 1자리까지 표시)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

        # Y축 범위 자동 조절 (하단은 0부터, 상단은 약간 여유있게)
        ax.autoscale(enable=True, axis='y', tight=False) 
        current_ylim = ax.get_ylim()
        ax.set_ylim(bottom=0, top=current_ylim[1] * 1.1) 

        # 그래프 배경에 가로 눈금선 추가
        ax.yaxis.grid(True, linestyle='--', alpha=0.6)

        # 각 막대 위에 평균값 텍스트 표시
        ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=9) 

        # 범례 표시 (필요시)
        # ax.legend()

        # 그래프 레이아웃 자동 조정 (라벨 잘림 방지)
        plt.tight_layout()

        # --- 그래프를 이미지 파일로 저장 ---
        try:
             # 저장 경로의 디렉토리 확인 및 생성
             output_dir = os.path.dirname(output_filepath)
             if output_dir and not os.path.exists(output_dir):
                  os.makedirs(output_dir)
                  print(f"Created output directory: {output_dir}")
             
             # 파일 저장 (bbox_inches='tight' 옵션으로 그림 요소 잘림 방지)
             plt.savefig(output_filepath, dpi=300, bbox_inches='tight') 
             print(f"\nFigure successfully saved to: {os.path.abspath(output_filepath)}") # 저장된 절대 경로 표시
        except Exception as e:
             print(f"Error saving figure to {output_filepath}: {e}")

        # 그래프 화면에 표시
        plt.show()

    except FileNotFoundError:
        print(f"Error: CSV file not found - {csv_filepath}")
    except KeyError as e:
        # 컬럼명 오류 시 CSV 헤더 출력하여 디버깅 도움
        try:
            temp_df = pd.read_csv(csv_filepath, nrows=0) # 헤더만 읽기
            print(f"Error: Required column not found in CSV - {e}. Available columns: {temp_df.columns.tolist()}")
        except Exception as read_e:
            print(f"Error: Required column not found in CSV - {e}. Could not read CSV headers: {read_e}")
            
    except Exception as e:
        print(f"An error occurred during plotting: {e}")


# === 메인 실행 블록 ===
if __name__ == "__main__":
    # 설정된 경로와 필터로 그래프 생성 함수 호출
    plot_traffic_results(CSV_FILEPATH, FILTER_RESOLUTION, OUTPUT_FIGURE_PATH)