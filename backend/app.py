import jieba  # 确保导入 jieba 模块
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os

# 初始化日志记录
logging.basicConfig(level=logging.INFO)

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 全局参数
MAX_SEQUENCE_LENGTH = 20
SIMILARITY_THRESHOLD = 0.5  # 相似度阈值

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
    return ' '.join([word for word, flag in words if flag != 'x'])

# 预处理函数
def preprocess_texts(title):
    if tokenizer is None:
        raise ValueError("Tokenizer is not initialized.")
    title_tokenized = jieba_tokenizer(title)
    x_test = tokenizer.texts_to_sequences([title_tokenized])
    x_test = kr.preprocessing.sequence.pad_sequences(x_test, maxlen=MAX_SEQUENCE_LENGTH)
    return x_test

# 模型预测
def predict_category(input_title, database_title):
    if model is None:
        raise ValueError("Model is not loaded.")
    input_processed = preprocess_texts(input_title)
    db_processed = preprocess_texts(database_title)
    predictions = model.predict([input_processed, db_processed])
    return predictions

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
        LIMIT 100
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # 将 title 和 content 拼接成一段文本
        for result in results:
            result["combined_text"] = result["title"] + " " + result["content"]
        return results
    finally:
        cursor.close()
        connection.close()

# 计算简单文本相似度
def compute_similarity(input_title, db_combined_text):
    input_words = set(jieba.lcut(input_title))
    db_words = set(jieba.lcut(db_combined_text))
    common_words = input_words.intersection(db_words)
    total_words = input_words.union(db_words)
    return len(common_words) / len(total_words)

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

        # 获取数据库中所有记录
        database_entries = get_closest_match_from_database(input_title)
        if not database_entries:
            return jsonify({'error': 'No matching data found in the database'}), 404

        # 遍历所有数据库记录，计算输入标题与拼接文本的相似度
        best_match = None
        best_similarity = 0
        for entry in database_entries:
            db_combined_text = entry["combined_text"]
            similarity = compute_similarity(input_title, db_combined_text)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry

        # 检查相似度是否超过阈值
        if best_similarity < SIMILARITY_THRESHOLD:
            return jsonify({
                'error': 'No sufficiently similar data found in the database',
                'similarity': best_similarity
            }), 404

        # 使用模型进行预测
        probabilities = predict_category(input_title, best_match["title"])
        category_index = np.argmax(probabilities)
        category = "fake" if category_index == 1 else "real"

        response = {
            'input_title': input_title,
            'matched_title': best_match["title"],
            'matched_content': best_match["content"],
            'similarity': best_similarity,
            'category': category,
            'probabilities': {
                'fake': float(probabilities[1]),
                'real': float(probabilities[0])
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
