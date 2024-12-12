// 初始化：監聽提交按鈕點擊事件
document.getElementById('submit-btn').addEventListener('click', async function () {
    const inputText = document.getElementById('inputtext').value.trim();

    if (!inputText) {
        alert('請輸入有疑慮的假消息！');
        return;
    }

    // 顯示等待動畫
    document.getElementById('loading').style.display = 'block';

    try {
        // 向後端發送請求
        const response = await fetch('https://timmytry.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: inputText }),
        });

        const data = await response.json();

        // 隱藏等待動畫
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            alert(`錯誤：${data.error}`);
        } else {
            const timestamp = new Date().toLocaleString(); // 當前時間
            const resultContainer = document.getElementById('result-container');

            // 清空舊結果（可選，根據需求保留歷史記錄則註釋掉此行）
            resultContainer.innerHTML = '';

            // 插入新結果
            const resultHTML = `
                <div class="result-item">
                    <p><strong>結果時間：</strong>${timestamp}</p>
                    <p><strong>查詢標題：</strong>${data.input_title}</p>
                    <p><strong>匹配標題：</strong>${data.matched_title}</p>
                    <p><strong>分類：</strong>${data.category}</p>
                </div>
            `;
            resultContainer.innerHTML = resultHTML;

            // 確保結果區域可見
            document.getElementById('result').style.display = 'block';

            // 新結果高亮顯示
            const resultItem = document.querySelector('.result-item');
            resultItem.classList.add('highlight');
            setTimeout(() => resultItem.classList.remove('highlight'), 2000);
        }
    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        console.error('請求失敗:', error);
        alert('無法處理請求，請稍後再試。');
    }
});

// 平滑滾動功能
function smoothScroll(target) {
    const element = document.querySelector(target);
    element.scrollIntoView({ behavior: 'smooth' });
}

// 開啟新窗口（目前不必要，預留用作其他功能）
function openNewWindow() {
    console.log("此功能未實現，僅為佔位。");
}
