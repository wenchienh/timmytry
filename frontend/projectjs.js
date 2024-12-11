// 初始化：監聽提交按鈕點擊事件
document.getElementById('submit-btn').addEventListener('click', async function () {
    const inputText = document.getElementById('inputtext').value.trim();

    // 驗證用戶是否輸入內容
    if (!inputText) {
        alert('請輸入有疑慮的假消息！');
        return;
    }

    // 驗證輸入長度
    if (inputText.length > 200) {
        alert('輸入內容過長，請縮短到200字以內！');
        return;
    }

    // 輸入文字處理（去除特殊字符）
    const sanitizedInput = inputText.replace(/['"\\]/g, '');
    const isEnglish = /^[A-Za-z0-9\s]+$/.test(sanitizedInput);
    const language = isEnglish ? 'en' : 'zh';

    // 顯示等待動畫
    document.getElementById('loading').style.display = 'block';

    try {
        // 向後端發送請求
        const response = await fetch('https://timmytry.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: sanitizedInput, language }),
        });

        // 解析後端返回的 JSON 數據
        const data = await response.json();

        // 隱藏等待動畫
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            alert(`錯誤：${data.error}`);
        } else {
            updateResult(data.category);
        }
    } catch (error) {
        // 隱藏等待動畫
        document.getElementById('loading').style.display = 'none';
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
