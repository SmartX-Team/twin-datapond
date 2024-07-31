# 실제 Spark-operator 로 생성한 SparkApplication 이 정상적으로 카프카 연동해서 스트리임 데이터 처리하고 배치 형태로 처리되는지 확인해볼려고 만든 테스트 코드이다.
# 기존 스키마는 정의된채 랜덤하게 값을 바꿔가면서 송신하는 코드로 그외 특별한 기능은 없다.

from kafka import KafkaProducer
import json
import time
import random

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers=['10.80.0.3:9094'],  # Kafka 브로커 주소
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # JSON으로 직렬화 및 UTF-8 인코딩
)

print("Kafka Producer is running...")

# 메시지 송신
while True:
    # 임의의 값을 생성
    result = {
        'id': random.randint(1, 100),
        'type': random.choice(['car', 'pedestrian', 'bicycle']),
        'confidence': round(random.uniform(0.5, 1.0), 2)
    }
    producer.send('spark-test', value=result)
    print(f"Sent detection result: {result}")
    time.sleep(0.1)  # 0.1초 대기

producer.flush()
producer.close()
