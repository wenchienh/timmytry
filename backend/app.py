import os
import json
import keras as kr
import numpy as np
import tensorflow as tf
import jieba.posseg as pseg
from flask import Flask, request, jsonify

# 設定 Flask 應用及相關環境變數
app = Flask(__name__)

# 全局參數
MAX_SEQUENCE_LENGTH = 20

# 模型及資料的相對路徑（建議將模型和JSON放在應用目錄中）
MODEL_PATH = os.getenv("MODEL_PATH", "FNCwithLSTM.h5")
WORD_INDEX_PATH = os.getenv("WORD_INDEX_PATH", "models/word_index.json")

# 加載已訓練模型
model = kr.models.load_model(MODEL_PATH)

# 加載 word_index.json 並還原 Tokenizer
with open(WORD_INDEX_PATH, 'r') as f:
    word_index = json.load(f)

tokenizer = tf.keras.preprocessing.text.Tokenizer()
tokenizer.word_index = word_index
tokenizer.index_word = {index: word for word, index in word_index.items()}

# 標籤字典
label_to_index = {
    'unrelated': 0,
    'agreed': 1,
    'disagreed': 2
}
index_to_label = {v: k for k, v in label_to_index.items()}

# 分詞函數
def jieba_tokenizer(text):
    words = pseg.cut(text)
    return ' '.join([word for word, flag in words if flag != 'x'])

# 預處理函數
def preprocess_texts(title1, title2):
    title1_tokenized = jieba_tokenizer(title1)
    title2_tokenized = jieba_tokenizer(title2)
    
    x1_test = tokenizer.texts_to_sequences([title1_tokenized])
    x2_test = tokenizer.texts_to_sequences([title2_tokenized])
    
    x1_test = kr.preprocessing.sequence.pad_sequences(x1_test, maxlen=MAX_SEQUENCE_LENGTH)
    x2_test = kr.preprocessing.sequence.pad_sequences(x2_test, maxlen=MAX_SEQUENCE_LENGTH)
    
    return x1_test, x2_test

# 預測函數
def predict_category(title1, title2):
    x1_test, x2_test = preprocess_texts(title1, title2)
    predictions = model.predict([x1_test, x2_test])
    category_index = np.argmax(predictions, axis=1)[0]
    return index_to_label[category_index]

# 定義 API 路徑
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        title1 = data.get('title1')
        title2 = data.get('title2')
        
        if not title1 or not title2:
            return jsonify({'error': 'Both title1 and title2 are required'}), 400
        
        category = predict_category(title1, title2)
        return jsonify({'category': category})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 適合部署到生產環境的配置
    app.run(host='0.0.0.0', port=5000, debug=False)
