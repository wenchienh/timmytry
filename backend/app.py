import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
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
    "host": os.getenv("DB_HOST", "35.185.148.251"),  # 替换为你的数据库地址
    "user": os.getenv("DB_USER", "tps"),             # 替换为你的数据库用户名
    "password": os.getenv("DB_PASSWORD", "0423"),    # 替换为你的数据库密码
    "database": os.getenv("DB_NAME", "fake_news_db"),# 替换为你的数据库名称
}

# 加载已训练的模型
try:
    model = kr.models.load_model(MODEL_PATH)
    logging.info("模型加载成功！")
except Exception as e:
    logging.error(f"模型加载失败：{e}")
    model = None

# 加载 word_index.json 并还原 Tokenizer
try:
    with open(WORD_INDEX_PATH, 'r', encoding='utf-8') as f:
        word_index = json.load(f)
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.word_index = word_index
    tokenizer.index_word = {index: word for word, index in word_index.items()}
    logging.info("Tokenizer 加载成功！")
except Exception as e:
    logging.error(f"Tokenizer 加载失败：{e}")
    tokenizer = None

# 建立数据库连接
def get_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logging.info("数据库连接成功！")
        return connection
    except mysql.connector.Error as err:
        logging.error(f"数据库连接错误：{err}")
        return None

# 分词函数
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return ' '.join([word for word, flag in words if flag != 'x'])

# 预处理函数
def preprocess_texts(title):
    if tokenizer is None:
        raise ValueError("Tokenizer 未初始化。")
    title_tokenized = jieba_tokenizer(title)
    x_test = tokenizer.texts_to_sequences([title_tokenized])
    x_test = kr.preprocessing.sequence.pad_sequences(x_test, maxlen=MAX_SEQUENCE_LENGTH)
    return x_test

# 模型预测
def predict_category(input_title, database_title):
    if model is None:
        raise ValueError("模型未加载。")
    input_processed = preprocess_texts(input_title)
    db_processed = preprocess_texts(database_title)
    predictions = model.predict([input_processed, db_processed])
    return np.argmax(predictions, axis=1)[0]  # 返回预测类别索引

# 从数据库查找与输入标题最相似的记录
def get_closest_match_from_database(input_title):
    connection = get_database_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        # 使用全文搜索匹配，需要在 title 字段上创建 FULLTEXT 索引
        query = """
        SELECT id, title, content, classification
        FROM cleaned_file
        WHERE MATCH(title) AGAINST(%s IN NATURAL LANGUAGE MODE)
        LIMIT 1
        """
        logging.info(f"执行 SQL 查询：{query}，参数：{input_title}")
        cursor.execute(query, (input_title,))
        result = cursor.fetchone()
        logging.info(f"查询结果：{result}")
        return result
    except mysql.connector.Error as e:
        logging.error(f"数据库查询错误：{e}")
        return None
    finally:
        cursor.close()
        connection.close()

# API 路由
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        logging.info(f"收到请求数据：{data}")
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
        logging.info(f"响应数据：{response}")
        return jsonify(response)

    except Exception as e:
        logging.error(f"发生错误：{e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 测试数据库连接
    test_connection = get_database_connection()
    if test_connection is not None:
        test_connection.close()
    else:
        logging.error("无法连接到数据库，程序退出。")
        exit(1)

    # 确保模型已加载
    if model is None or tokenizer is None:
        logging.error("模型或 Tokenizer 加载失败，程序退出。")
        exit(1)

    app.run(host='0.0.0.0', port=5000, debug=False)
    
