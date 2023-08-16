import re
import os
import json
import openai
import pinecone
import tiktoken
from tqdm import tqdm
import mysql.connector
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure Pinecone variables and initialize
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")


# Pinecone db name and upload batch size
index_name = "master"
upsert_batch_size = 2


# Configure OpenAI variables
embed_model = os.getenv('EMBED_MODEL')
openai.api_key = os.getenv('OPENAI_API_KEY')


# OpenAI embedding and tokenizer models
titoken_encoding_model = "cl100k_base"
max_tokens_model = 8191


pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(index_name)


def get_embedding(embed_data):
    return openai.Embedding.create(
        model=embed_model,
        input=embed_data
    )

# def get_embedding(embed_data):
#    return openai.Embedding.create(input=embed_data, model=embed_model)['data']


# Hàm chuyển đổi đối tượng date thành chuỗi có định dạng
def date_converter(o):
    return str(o.strftime("%Y-%m-%d"))


def get_daily_report_data():
    # Thay đổi các thông tin sau để phù hợp với cấu hình MySQL của bạn
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')

    # Kết nối đến cơ sở dữ liệu
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=3306
    )
    cursor = connection.cursor()

    # Thực hiện truy vấn để lấy dữ liệu từ bảng tasks
    query = "SELECT dr.id AS daily_report_id, dr.report_date AS report_date, t.content, u.username FROM daily_reports dr JOIN tasks t ON dr.id = t.daily_report_id JOIN users u ON dr.user_id = u.id ORDER BY dr.report_date DESC LIMIT 10"
    cursor.execute(query)

    # Lấy tất cả các dòng dữ liệu từ kết quả truy vấn
    daily_report_data = cursor.fetchall()

    # In dữ liệu lấy được
    new_data = []
    for row in daily_report_data:
        id, report_date, content, username = row
        new_data.append({
            "id": id,
            "report_date": report_date,
            "content": content,
            "username": username
        })

    # Đóng kết nối sau khi hoàn thành công việc
    connection.close()
    return daily_report_data

daily_report_data = get_daily_report_data()


# Create embeddings and upsert the vectors to Pinecone
print(f"Creating embeddings and uploading vectors to database")
for i in tqdm(range(0, len(daily_report_data), upsert_batch_size)):
    # process source text in batches
    i_end = min(len(daily_report_data), i+upsert_batch_size)
    meta_batch = daily_report_data[i:i_end]
    # meta_batch = json.dumps(meta_batch, default=date_converter)

    # print("\n\n\n\n")
    # print("LEN:::", len(meta_batch), i, i_end)
    texts = []
    ids_batch = []
    for meta_data in meta_batch:
        strId = 'daily-report-' + str(meta_data[0])
        text = strId + ' in ' + date_converter(meta_data[1]) + ' had content: ' + meta_data[2] + ' write by ' + meta_data[3]
        ids_batch.append(strId)
        texts.append(text)

    embedding = get_embedding(texts)
    embeds = []
    for record in embedding['data']:
        embeds.append(record['embedding'])

    # print("\n\n\n\n\n\n\n\n\texts:: ", texts)

    # print("\n\n\n\n\n\n\n\n\nembed:: ", embedding)

    # clean metadata before upserting
    new_meta_batch = []
    for meta_data in meta_batch:
        strId = 'daily-report-' + str(meta_data[0])
        text = strId + ' in ' + date_converter(meta_data[1]) + ' had content: ' + meta_data[2] + ' write by ' + meta_data[3]
        new_meta_batch.append({
            'id': strId,
            'text': text,
            'source': 'rs-data-daily-report-' + str(meta_data[0]),
        })

    # print("\n\n\n\n")
    # print("LEN:::", i_end)

    # upsert vectors
    to_upsert = list(zip(ids_batch, embeds, meta_batch))
    # to_upsert = 
    index.upsert(vectors=to_upsert)

# Print final vector count
# vector_count = index.describe_index_stats()['total_vector_count']
# print(f"Database contains {vector_count} vectors.")
