# back/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 추가
import redis
import boto3
import pymysql
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 설정

# 환경 변수에서 설정 값 읽기
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PORT = os.getenv('DB_PORT')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# 필수 환경 변수 확인
required_env_vars = ['REDIS_HOST', 'SQS_QUEUE_URL', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
missing_vars = [var for var in required_env_vars if os.getenv(var) is None]

if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

# Redis 클라이언트 설정
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

# SQS 클라이언트 설정
sqs = boto3.client('sqs', region_name='ap-northeast-2')

# AuroraDB 클라이언트 설정
db_connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=int(DB_PORT)
)

@app.route('/process-payment', methods=['POST'])
def process_payment():
    data = request.json
    user_id = data.get('userId')
    amount = data.get('amount')
    description = data.get('description')

    if not user_id or not amount or not description:
        return jsonify({'message': 'Invalid request'}), 400

    # Redis에 요청 저장
    request_id = user_id
    if redis_client.setnx(request_id, 'pending'):
        redis_client.expire(request_id, 3600)

        # SQS 메시지 전송
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=f'{user_id},{amount},{description}',
            MessageDeduplicationId=request_id,
            MessageGroupId='payment-group'
        )

        return jsonify({'message': 'Payment request sent'}), 200
    else:
        return jsonify({'message': 'Request already exists'}), 400

@app.route('/process-sqs-messages', methods=['POST'])
def process_sqs_messages():
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )

    for message in response.get('Messages', []):
        body = message['Body']
        user_id, amount, description = body.split(',')

        # AuroraDB에 저장
        with db_connection.cursor() as cursor:
            sql = "INSERT INTO payments (user_id, amount, description) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, amount, description))
            db_connection.commit()

        # Redis에서 요청 ID 삭제
        redis_client.delete(user_id)

        # SQS 메시지 삭제
        sqs.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=message['ReceiptHandle']
        )

    return jsonify({'message': 'Messages processed'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=FLASK_PORT)
