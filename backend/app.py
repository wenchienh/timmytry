import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from rank_bm25 import BM25Okapi
import logging
import time

# 初始化日志记录
logging.basicConfig(level=logging.INFO)

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 全局参数
MAX_SEQUENCE_LENGTH = 20
SIMILARITY_THRESHOLD = 1.5  # BM25 阈值

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
def get_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logging.info("Database connection established.")
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None

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
    tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=10000)  # 添加 num_words 参数
    tokenizer.word_index = word_index
    tokenizer.index_word = {index: word for word, index in word_index.items()}
    logging.info("Tokenizer restored successfully.")
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    tokenizer = None

# 分词函数
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return [word for word, flag in words if flag != 'x']

# 预处理函数
def preprocess_texts(title):
    if tokenizer is None:
        raise ValueError("Tokenizer is not initialized.")
    title_tokenized = jieba_tokenizer(title)
    x_test = tokenizer.texts_to_sequences([" ".join(title_tokenized)])
    x_test = kr.preprocessing.sequence.pad_sequences(x_test, maxlen=MAX_SEQUENCE_LENGTH)
    return x_test

# 模型预测
def predict_category(input_title, database_title):
    if model is None:
        raise ValueError("Model is not loaded.")
    input_processed = preprocess_texts(input_title)
    db_processed = preprocess_texts(database_title)

    logging.info(f"Input shape: {input_processed.shape}, DB shape: {db_processed.shape}")

    predictions = model.predict([input_processed, db_processed])

    logging.info(f"Predictions shape: {predictions.shape}, Predictions: {predictions}")

    if predictions.ndim != 2 or predictions.shape[1] != 2:  # 确保输出形状正确
        raise ValueError("Model output shape is incorrect. Expected [batch_size, 2].")

    return predictions

# 从数据库查找与输入标题最相似的记录（使用 BM25）
def get_best_match_bm25(input_title):
    connection = get_database_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, title, content, classification
        FROM cleaned_file
        LIMIT 100
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # 分词处理
        corpus = [jieba_tokenizer(row["title"] + " " + row["content"]) for row in results]
        bm25 = BM25Okapi(corpus)

        # 计算 BM25 分数
        input_tokens = jieba_tokenizer(input_title)
        scores = bm25.get_scores(input_tokens)

        # 找到最高分的记录
        best_index = np.argmax(scores)
        best_score = scores[best_index]
        if best_score >= SIMILARITY_THRESHOLD:
            best_match = results[best_index]
            best_match["bm25_score"] = best_score
            return best_match
        else:
            return None  # 如果最高分低于阈值，则认为没有足够匹配的数据
    finally:
        cursor.close()
        connection.close()

# API 路由
@app.route('/predict', methods=['POST'])
def predict():
    try:
        start_time = time.time()
        data = request.json
        logging.info(f"Received request data: {data}")
        input_title = data.get('title', '').strip()

        if not input_title:
            return jsonify({'error': 'Title is required'}), 400

        if len(input_title) < 3:
            return jsonify({'error': 'Title is too short'}), 400

        # 计时：数据库查询
        db_query_start = time.time()
        best_match = get_best_match_bm25(input_title)
        db_query_end = time.time()
        logging.info(f"Database query time: {db_query_end - db_query_start:.4f} seconds")

        if not best_match:
            return jsonify({'error': 'No sufficiently similar data found in the database'}), 404

        # 计时：模型预测
        model_predict_start = time.time()
        probabilities = predict_category(input_title, best_match["title"])
        model_predict_end = time.time()
        logging.info(f"Model prediction time: {model_predict_end - model_predict_start:.4f} seconds")

        # 总耗时
        end_time = time.time()
        logging.info(f"Total API execution time: {end_time - start_time:.4f} seconds")

        category_index = np.argmax(probabilities)
        category = "fake" if category_index == 1 else "real"

        response = {
            'input_title': input_title,
            'matched_title': best_match["title"],
            'matched_content': best_match["content"],
            'bm25_score': best_match["bm25_score"],
            'category': category,
            'probabilities': {
                'fake': float(probabilities[0][1]),
                'real': float(probabilities[0][0])
            },
            'database_entry': best_match
        }
        logging.info(f"Response data: {response}")
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
