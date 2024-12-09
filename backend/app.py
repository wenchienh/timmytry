from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import json
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences

# 創建 Flask 應用
app = Flask(__name__)
CORS(app)  # 啟用跨域支持

# 加載模型和輔助文件
def load_model_and_resources():
    """
    加載 Keras 模型和詞彙表。
    """
    print("正在加載模型和詞彙表...")
    try:
        # 加載模型
        model = tf.keras.models.load_model("FNCwithLSTM.h5")
        print("模型加載成功！")

        # 加載詞彙表
        with open("word_index.json", "r", encoding="utf-8") as f:
            word_index = json.load(f)
        print("詞彙表加載成功！")

        return model, word_index
    except Exception as e:
        print(f"加載模型或詞彙表失敗：{e}")
        raise

# 加載模型和詞彙表
model, word_index = load_model_and_resources()

# 定義預處理函數
def preprocess_input(text, word_index, max_length=100):
    """
    將用戶輸入的文字轉換為數字數組，並進行填充。
    """
    try:
        # 將輸入分詞（假設以空格分詞）
        tokens = text.split()

        # 將詞轉換為索引
        sequences = [[word_index.get(word, 0) for word in tokens]]

        # 對序列進行填充
        padded_sequence = pad_sequences(sequences, maxlen=max_length, padding="post")
        return padded_sequence
    except Exception as e:
        print(f"預處理失敗：{e}")
        raise

# 定義推理函數
def run_model(input_text):
    """
    使用模型進行推理。
    """
    try:
        # 預處理輸入
        input_data = preprocess_input(input_text, word_index)

        # 運行模型
        prediction = model.predict(input_data)

        # 將結果格式化
        predicted_class = np.argmax(prediction, axis=-1)[0]  # 假設模型返回多分類結果
        confidence = np.max(prediction, axis=-1)[0]          # 最大概率值

        return {"predicted_class": int(predicted_class), "confidence": float(confidence)}
    except Exception as e:
        print(f"模型推理失敗：{e}")
        raise

# 定義 Flask 路由
@app.route('/predict', methods=['POST'])
def predict():
    """
    處理來自前端的請求，並返回模型結果。
    """
    try:
        # 獲取用戶輸入
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': '請求數據格式錯誤，缺少 "question" 字段'}), 400
        
        user_input = data['question']
        print(f"接收到的輸入：{user_input}")

        # 使用模型進行推理
        result = run_model(user_input)

        # 返回結果
        return jsonify({'result': result})
    except Exception as e:
        print(f"處理請求失敗：{e}")
        return jsonify({'error': str(e)}), 500

# 啟動 Flask 應用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
