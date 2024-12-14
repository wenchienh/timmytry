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

# 模型及数据路径
MODEL_PATH = os.getenv("MODEL_PATH", "FNCwithLSTM.h5")
WORD_INDEX_PATH = os.getenv("WORD_INDEX_PATH", "word_index.json")

# 数据库连接配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "35.185.148.251"),
    "user": os.getenv("DB_USER", "tps"),
    "password": os.getenv("DB_PASSWORD", "0423"),
    "database": os.getenv("DB_NAME", "fake_news_db")
}

# 数据库连接
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
    model_load_start = time.time()
    model = kr.models.load_model(MODEL_PATH)
    logging.info(f"Model loaded successfully. Time taken: {time.time() - model_load_start:.4f} seconds")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    model = None

# 加载 Tokenizer
try:
    tokenizer_load_start = time.time()
    with open(WORD_INDEX_PATH, 'r', encoding='utf-8') as f:
        word_index = json.load(f)
    tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=10000)
    tokenizer.word_index = word_index
    tokenizer.index_word = {index: word for word, index in word_index.items()}
    logging.info(f"Tokenizer restored successfully. Time taken: {time.time() - tokenizer_load_start:.4f} seconds")
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    tokenizer = None

# 分词函数
def jieba_tokenizer(text):
    return [word for word, flag in pseg.cut(text) if flag != 'x']

# 模型预测
def predict_category(input_title, database_title):
    if model is None:
        raise ValueError("Model is not loaded.")
    input_processed = tokenizer.texts_to_sequences([" ".join(jieba_tokenizer(input_title))])
    db_processed = tokenizer.texts_to_sequences([" ".join(jieba_tokenizer(database_title))])
    x_test = kr.preprocessing.sequence.pad_sequences(input_processed, maxlen=MAX_SEQUENCE_LENGTH)
    db_test = kr.preprocessing.sequence.pad_sequences(db_processed, maxlen=MAX_SEQUENCE_LENGTH)
    return model.predict([x_test, db_test])

# BM25 匹配
def get_best_match_bm25(input_title):
    connection = get_database_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, title, content, classification FROM cleaned_file LIMIT 100"
        query_start = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        logging.info(f"Database query time: {time.time() - query_start:.4f} seconds")

        bm25_start = time.time()
        corpus = [jieba_tokenizer(row["title"] + " " + row["content"]) for row in results]
        bm25 = BM25Okapi(corpus)
        input_tokens = jieba_tokenizer(input_title)
        scores = bm25.get_scores(input_tokens)
        logging.info(f"BM25 processing time: {time.time() - bm25_start:.4f} seconds")

        best_index = np.argmax(scores)
        best_score = scores[best_index]
        if best_score >= SIMILARITY_THRESHOLD:
            best_match = results[best_index]
            best_match["bm25_score"] = best_score
            return best_match
        return None
    finally:
        cursor.close()
        connection.close()

# API 路由
@app.route('/predict', methods=['POST'])
def predict():
    try:
        start_time = time.time()
        data = request.json
        input_title = data.get('title', '').strip()

        if not input_title:
            return jsonify({'error': '標題為必填項'}), 400
        if len(input_title) < 3:
            return jsonify({'error': '標題長度過短'}), 400

        best_match = get_best_match_bm25(input_title)
        if not best_match:
            return jsonify({'error': '無法找到相似數據'}), 404

        prediction_start = time.time()
        probabilities = predict_category(input_title, best_match["title"])
        logging.info(f"Model prediction time: {time.time() - prediction_start:.4f} seconds")

        category_index = np.argmax(probabilities)
        categories = ["無關", "一致", "不一致"]
        category = categories[category_index]

        response = {
            'input_title': input_title,
            'matched_title': best_match["title"],
            'matched_content': best_match["content"],
            'bm25_score': best_match["bm25_score"],
            'category': category,
            'probabilities': {categories[i]: float(probabilities[0][i]) for i in range(3)},
            'database_entry': best_match
        }
        logging.info(f"Total API processing time: {time.time() - start_time:.4f} seconds")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
