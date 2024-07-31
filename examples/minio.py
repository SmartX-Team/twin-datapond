# MinIO 클라이언트를 사용한 버킷 생성, 파일 업로드/다운로드, 파일 목록 조회 예제 테스트
# S3 접속에 흔히 사용되는 boto3 라이브러리로 간단하게 테스트 해보는 코드이다.

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import json

# MinIO Tenant 정보
endpoint_url = ''
access_key = ''
secret_key = ''

# config.json 파일에서 나머지 설정 읽기
config_path = '/home/netai/twin-datapond/config.json'

with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    endpoint_url = config['minio']['endpoint_url']
    access_key = config['minio']['access_key']
    secret_key = config['minio']['secret_key']

# MinIO 클라이언트 생성
s3_client = boto3.client(
    's3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    use_ssl=True,
    verify=False
)

# 버킷 생성 함수
def create_bucket(bucket_name):
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    except s3_client.exceptions.BucketAlreadyExists as e:
        print(f"Bucket '{bucket_name}' already exists.")
    except Exception as e:
        print(f"Error creating bucket: {e}")

# 파일 업로드 함수
def upload_file(file_name, bucket_name, object_name):
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        print(f"File '{file_name}' uploaded to bucket '{bucket_name}' as '{object_name}'.")
    except FileNotFoundError as e:
        print(f"File '{file_name}' not found.")
    except NoCredentialsError as e:
        print(f"Credentials not available: {e}")
    except PartialCredentialsError as e:
        print(f"Partial credentials provided: {e}")
    except Exception as e:
        print(f"Error uploading file: {e}")

# 파일 다운로드 함수
def download_file(bucket_name, object_name, file_name):
    try:
        s3_client.download_file(bucket_name, object_name, file_name)
        print(f"File '{object_name}' from bucket '{bucket_name}' downloaded as '{file_name}'.")
    except FileNotFoundError as e:
        print(f"File '{file_name}' not found.")
    except NoCredentialsError as e:
        print(f"Credentials not available: {e}")
    except PartialCredentialsError as e:
        print(f"Partial credentials provided: {e}")
    except Exception as e:
        print(f"Error downloading file: {e}")


def list_objects(bucket_name):
    try:
        continuation_token = None
        while True:
            if continuation_token:
                response = s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
            else:
                response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    print(obj['Key'])

            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break

    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Partial credentials provided.")
    except Exception as e:
        print(f"Error listing objects: {e}")


# 예제 사용법

# 1. 버킷 생성
#create_bucket('mybucket')

# 2. 파일 업로드
#upload_file('myfile.txt', 'mybucket', 'myfile.txt')

# 3. 파일 다운로드
#download_file('mybucket', 'myfile.txt', 'myfile_downloaded.txt')

list_objects('mybucket')