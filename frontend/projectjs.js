// 初始化：監聽提交按鈕點擊事件
document.getElementById('submit-btn').addEventListener('click', async function () {
    const inputText = document.getElementById('inputtext').value.trim();

    if (!inputText) {
        alert('請輸入有疑慮的假消息！');
        return;
    }

    if (inputText.length > 200) {
        alert('輸入內容過長，請縮短到200字以內！');
        return;
    }

    const sanitizedInput = inputText.replace(/['"]/g, '');
    const isEnglish = /^[A-Za-z0-9\s]+$/.test(sanitizedInput);
    const language = isEnglish ? 'en' : 'zh';

    document.getElementById('loading').style.display = 'block';

    try {
        const response = await fetch('https://timmytry.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: sanitizedInput, language }),
        });

        const data = await response.json();
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            alert(`錯誤：${data.error}`);
        } else {
            updateResult(data.category);
        }
    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        alert('無法處理請求，請稍後再試。');
    }
});

function updateResult(category) {
    const resultHistory = document.getElementById('result-history');
    const resultEntry = document.createElement('div');
    resultEntry.textContent = `分析結果：${category}`;
    resultHistory.appendChild(resultEntry);
}

// 平滑滾動功能
function smoothScroll(target) {
    const element = document.querySelector(target);
    element.scrollIntoView({ behavior: 'smooth' });
}

// 開啟新窗口（目前不必要，預留用作其他功能）
function openNewWindow() {
    console.log('此功能未實現，僅為佔位。');
}
