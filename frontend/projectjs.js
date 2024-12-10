// 初始化：監聽提交按鈕點擊事件
document.getElementById('submit-btn').addEventListener('click', async function () {
    // 獲取用戶輸入的文字
    const inputText = document.getElementById('inputtext').value.trim();

    // 驗證用戶是否輸入內容
    if (!inputText) {
        alert('請輸入有疑慮的假消息！');
        return;
    }

    // 顯示處理中的提示（可選）
    console.log('正在處理用戶輸入...');

    try {
        // 向後端發送請求
        const response = await fetch('https://timmytry.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // 指定請求類型為 JSON
            },
            body: JSON.stringify({ title: inputText }), // 傳遞用戶輸入數據
        });

        // 解析後端返回的 JSON 數據
        const data = await response.json();

        // 處理後端返回的結果
        if (data.error) {
            alert(`錯誤：${data.error}`);
        } else {
            console.log('後端返回的結果:', data.category);

            // 動態更新結果到頁面
            updateResult(data.category);
        }
    } catch (error) {
        console.error('請求失敗:', error);
        alert('無法處理請求，請稍後再試。');
    }
});

// 更新分析結果到頁面
function updateResult(category) {
    const resultSection = document.getElementById('result');
    const resultText = document.getElementById('result-text');

    // 更新結果文字
    resultText.textContent = `分析結果：${category}`;

    // 確保結果區域可見
    resultSection.style.display = 'block';
}

// 平滑滾動功能
function smoothScroll(target) {
    const element = document.querySelector(target);
    element.scrollIntoView({ behavior: 'smooth' });
}

// 開啟新窗口（目前不必要，預留用作其他功能）
function openNewWindow() {
    console.log("此功能未實現，僅為佔位。");
}
