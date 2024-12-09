from flask import Flask, request, jsonify
from flask_cors import CORS
import time  # 模擬模型處理時間
import random  # 模擬模型結果

# 創建 Flask 應用
app = Flask(__name__)
CORS(app)  # 啟用跨域支持，允許前端訪問

# 模擬加載的機器學習模型
def load_model():
    print("加載模型中...")
    # 模擬模型加載
    time.sleep(2)  # 假設加載需要2秒
    return "FakeModel"  # 返回模型對象（這裡是占位符）

# 加載模型
model = load_model()

# 模型推理函數
def run_model(input_text):
    """
    模擬模型的推理邏輯
    """
    time.sleep(1)  # 模擬模型處理耗時
    # 模擬返回結果
    result = random.choice(["正面", "負面", "中立"])  # 模擬情緒分析結果
    return {"input": input_text, "prediction": result}

# 路由：處理用戶輸入問題並返回結果
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 接收前端傳來的 JSON 數據
        data = request.json
        user_input = data.get('question', '')  # 提取用戶輸入的問題

        if not user_input:
            return jsonify({'error': '輸入問題不可為空！'}), 400

        # 使用模型處理問題
        prediction_result = run_model(user_input)

        # 返回結果
        return jsonify({'result': prediction_result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 啟動 Flask 應用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
