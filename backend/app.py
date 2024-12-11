import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# 初始化 Flask 應用
app = Flask(__name__)
CORS(app)

# 全局參數
MAX_SEQUENCE_LENGTH = 20

# 模型及資料的相對路徑
MODEL_PATH = os.getenv("MODEL_PATH", "FNCwithLSTM.h5")
WORD_INDEX_PATH = os.getenv("WORD_INDEX_PATH", "word_index.json")

# 資料庫連接配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "35.185.148.251"),  # 替換為你的資料庫地址
    "user": os.getenv("DB_USER", "tps"),
    "password": os.getenv("DB_PASSWORD", "0423"),
    "database": os.getenv("DB_NAME", "fake_news_db")
}

# 加載已訓練的模型
try:
    model = kr.models.load_model(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# 加載 word_index.json 並還原 Tokenizer
try:
    with open(WORD_INDEX_PATH, 'r') as f:
        word_index = json.load(f)
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.word_index = word_index
    tokenizer.index_word = {index: word for word, index in word_index.items()}
except Exception as e:
    print(f"Error loading word_index: {e}")
    tokenizer = None

# 建立資料庫連接
def get_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("Database connection established!")
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# 分詞函數
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return ' '.join([word for word, flag in words if flag != 'x'])

# 預處理函數
def preprocess_texts(title):
    if tokenizer is None:
        raise ValueError("Tokenizer not initialized.")
    title_tokenized = jieba_tokenizer(title)
    x_test = tokenizer.texts_to_sequences([title_tokenized])
    x_test = kr.preprocessing.sequence.pad_sequences(x_test, maxlen=MAX_SEQUENCE_LENGTH)
    return x_test

# 模型預測
def predict_category(input_title, database_title):
    input_processed = preprocess_texts(input_title)
    db_processed = preprocess_texts(database_title)
    predictions = model.predict([input_processed, db_processed])
    return np.argmax(predictions, axis=1)[0]  # 返回預測類別索引

# 從資料庫查找與輸入標題最相似的數據
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
    except Exception as e:
        print(f"Database query error: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

# API 路徑
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        input_title = data.get('title')

        if not input_title:
            return jsonify({'error': 'Title is required'}), 400

        # 從資料庫獲取匹配的標題
        matched_entry = get_closest_match_from_database(input_title)
        if not matched_entry:
            return jsonify({'error': 'No matching data found in the database'}), 404

        db_title = matched_entry["title"]

        # 使用模型進行預測
        category_index = predict_category(input_title, db_title)
        category = "fake" if category_index == 1 else "real"

        return jsonify({
            'input_title': input_title,
            'matched_title': db_title,
            'category': category,
            'database_entry': matched_entry  # 返回完整的數據庫記錄
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
