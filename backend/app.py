import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify
from flask_cors import CORS  # 新增 CORS

# 設定 Flask 應用
app = Flask(__name__)
CORS(app)  # 啟用 CORS 支持

# 全局參數
MAX_SEQUENCE_LENGTH = 20
MODEL_PATH = os.getenv("MODEL_PATH", "FNCwithLSTM.h5")
WORD_INDEX_PATH = os.getenv("WORD_INDEX_PATH", "word_index.json")

# 加載模型
model = kr.models.load_model(MODEL_PATH)

# 加載詞彙索引
with open(WORD_INDEX_PATH, 'r') as f:
    word_index = json.load(f)

tokenizer = tf.keras.preprocessing.text.Tokenizer()
tokenizer.word_index = word_index
tokenizer.index_word = {index: word for word, index in word_index.items()}

# 預測標籤
label_to_index = {'unrelated': 0, 'agreed': 1, 'disagreed': 2}
index_to_label = {v: k for k, v in label_to_index.items()}

# 分詞函數
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return ' '.join([word for word, flag in words if flag != 'x'])

# 預處理
def preprocess_text(title):
    tokenized_title = jieba_tokenizer(title)
    sequence = tokenizer.texts_to_sequences([tokenized_title])
    padded_sequence = kr.preprocessing.sequence.pad_sequences(sequence, maxlen=MAX_SEQUENCE_LENGTH)
    return padded_sequence

# 預測函數
def predict_category(title):
    processed_title = preprocess_text(title)
    prediction = model.predict(processed_title)
    category_index = np.argmax(prediction, axis=1)[0]
    return index_to_label[category_index]

# API 路徑
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        title = data.get('title')

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        category = predict_category(title)
        return jsonify({'category': category})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
