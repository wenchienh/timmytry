import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import logging

# 初始化日志记录
logging.basicConfig(level=logging.INFO)

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 全局参数
MAX_SEQUENCE_LENGTH = 20

# 模型及数据的相对路径
MODEL_PATH = os.getenv("MODEL_PATH", "FNCwithLSTM.h5")
WORD_INDEX_PATH = os.getenv("WORD_INDEX_PATH", "word_index.json")

# 数据库连接配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "35.185.148.251"),
    "user": os.getenv("DB_USER", "tps"),
    "password": os.getenv("DB_PASSWORD", "0423"),
    "database": os.getenv("DB_NAME", "fake_news_db")
}

# 数据库连接池
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        **DB_CONFIG
    )
    logging.info("Database connection pool initialized.")
except mysql.connector.Error as err:
    logging.error(f"Database connection pool initialization error: {err}")
    db_pool = None

# 加载已训练的模型
try:
    model = kr.models.load_model(MODEL_PATH)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    model = None

# 加载 word_index.json 并还原 Tokenizer
try:
    with open(WORD_INDEX_PATH, 'r', encoding='utf-8') as f:
        word_index = json.load(f)
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.word_index = word_index
    tokenizer.index_word = {index: word for word, index in word_index.items()}
    logging.info("Tokenizer restored successfully.")
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    tokenizer = None

# 建立数据库连接
def get_database_connection():
    try:
        if db_pool:
            connection = db_pool.get_connection()
            logging.info("Database connection established.")
            return connection
        else:
            logging.error("Database connection pool is not initialized.")
            return None
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None

# 分词函数
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return ' '.join([word for word, flag in words if flag != 'x'])

# 预处理函数
def preprocess_texts(title):
    if tokenizer is None:
        raise ValueError("Tokenizer is not initialized.")
    title_tokenized = jieba_tokenizer(title)
    sequences = tokenizer.texts_to_sequences([title_tokenized])
    
    # 過濾超出 num_words 的索引
    num_words = 10000  # 與模型中 Embedding 層的 input_dim 一致
    filtered_sequences = [
        [index for index in seq if index < num_words]
        for seq in sequences
    ]
    print(f"Filtered sequences: {filtered_sequences}")  # 用於調試

    x_test = kr.preprocessing.sequence.pad_sequences(filtered_sequences, maxlen=MAX_SEQUENCE_LENGTH)
    return x_test


# 模型预测
def predict_category(input_title, database_title):
    if model is None:
        raise ValueError("Model is not loaded.")
    input_processed = preprocess_texts(input_title)
    db_processed = preprocess_texts(database_title)
    predictions = model.predict([input_processed, db_processed])
    if predictions.shape[0] == 0:
        raise ValueError("No predictions returned from the model.")
    return np.argmax(predictions, axis=1)[0]

# 从数据库查找与输入标题最相似的记录
def get_closest_match_from_database(input_title):
    connection = get_database_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, title, content, classification
        FROM cleaned_file
        WHERE title LIKE %s
        LIMIT 1
        """
        cursor.execute(query, (f"%{input_title}%",))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        connection.close()

# API 路由
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        logging.info(f"Received request data: {data}")
        input_title = data.get('title', '').strip()

        if not input_title:
            return jsonify({'error': 'Title is required'}), 400

        if len(input_title) < 3:
            return jsonify({'error': 'Title is too short'}), 400

        # 从数据库获取匹配的标题
        matched_entry = get_closest_match_from_database(input_title)
        if not matched_entry:
            return jsonify({'error': 'No matching data found in the database'}), 404

        db_title = matched_entry["title"]

        # 使用模型进行预测
        category_index = predict_category(input_title, db_title)
        category = "fake" if category_index == 1 else "real"

        response = {
            'input_title': input_title,
            'matched_title': db_title,
            'category': category,
            'database_entry': matched_entry  # 返回完整的数据库记录
        }
        logging.info(f"Response data: {response}")
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 确保数据库连接池和模型已正确加载
    if db_pool is None or model is None or tokenizer is None:
        logging.error("Initialization failed. Exiting application.")
        exit(1)

    app.run(host='0.0.0.0', port=5000, debug=False)
