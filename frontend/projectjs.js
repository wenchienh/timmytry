<script>
    // JavaScript 代码
    // 初始化：監聽提交按鈕點擊事件
    document.getElementById('submit-btn').addEventListener('click', async function () {
        const inputText = document.getElementById('inputtext').value.trim();

        // 驗證用戶是否輸入內容
        if (!inputText) {
            alert('請輸入有疑慮的假消息！');
            return;
        }

        // 顯示等待動畫
        const loadingIndicator = document.getElementById('loading');
        loadingIndicator.style.display = 'block';

        try {
            // 向後端發送請求
            const response = await fetch('https://timmytry.onrender.com/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: inputText }),
            });

            // 解析後端返回的 JSON 數據
            const data = await response.json();

            // 隱藏等待動畫
            loadingIndicator.style.display = 'none';

            if (data.error) {
                alert(`錯誤：${data.error}`);
            } else {
                updateResult(data);
            }
        } catch (error) {
            // 隱藏等待動畫
            loadingIndicator.style.display = 'none';
            console.error('請求失敗:', error);
            alert('無法處理請求，請稍後再試。');
        }
    });

    // 更新分析結果到頁面
    function updateResult(data) {
        const resultSection = document.getElementById('result');
        const resultText = document.getElementById('result-text');
        const resultTimestamp = document.getElementById('result-timestamp');

        // 更新結果文字
        resultText.innerHTML = `
            <strong>分析結果：</strong> ${data.category} <br>
            <strong>假消息概率：</strong> ${(data.probabilities.fake * 100).toFixed(2)}% <br>
            <strong>真消息概率：</strong> ${(data.probabilities.real * 100).toFixed(2)}% <br>
            <strong>相關資料庫標題：</strong> ${data.matched_title} <br>
            <strong>內容摘要：</strong> ${data.database_entry.content}
        `;

        // 更新時間戳
        const currentTime = new Date().toLocaleString();
        resultTimestamp.textContent = `查詢時間：${currentTime}`;

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

    // 重置結果區域的內容
    function resetResult() {
        const resultSection = document.getElementById('result');
        const resultText = document.getElementById('result-text');
        const resultTimestamp = document.getElementById('result-timestamp');

        // 清空結果區域內容
        resultText.innerHTML = '';
        resultTimestamp.textContent = '';

        // 隱藏結果區域
        resultSection.style.display = 'none';
    }

    // 監聽重置按鈕的點擊事件
    document.querySelector('button[type="reset"]').addEventListener('click', resetResult);
</script>
