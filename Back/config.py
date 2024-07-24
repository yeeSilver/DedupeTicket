import os

class Config:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', 'https://sqs.ap-northeast-2.amazonaws.com/590183883984/ticketMessage.fifo')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'mydatabase')
