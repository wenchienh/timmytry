// 初始化：监听提交按钮点击事件
document.getElementById('submit-btn').addEventListener('click', async function () {
    const inputText = document.getElementById('inputtext').value.trim();

    // 验证用户是否输入内容
    if (!inputText) {
        alert('请先输入内容！');
        return;
    }

    // 显示加载动画
    const loadingIndicator = document.getElementById('loading');
    loadingIndicator.style.display = 'block';

    try {
        // 向后端发送请求
        const response = await fetch('https://timmytry.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: inputText }),
        });

        // 检查请求是否成功
        if (!response.ok) {
            throw new Error(`服务器返回错误: ${response.status} ${response.statusText}`);
        }

        // 解析后端返回的 JSON 数据
        const data = await response.json();

        // 隐藏加载动画
        loadingIndicator.style.display = 'none';

        // 显示结果或错误信息
        if (data.error) {
            updateResultError(data.error);
        } else {
            updateResult(data);
        }
    } catch (error) {
        // 隐藏加载动画
        loadingIndicator.style.display = 'none';
        console.error('请求失败:', error.message);
        alert(`请求失败，请稍后重试！错误信息：${error.message}`);
    }
});

// 更新分析结果到页面
function updateResult(data) {
    const resultSection = document.getElementById('result');
    const resultText = document.getElementById('result-text');
    const resultTimestamp = document.getElementById('result-timestamp');

    // 更新结果内容
    resultText.innerHTML = `
        <strong>分析结果：</strong> ${data.category === 'fake' ? '假消息' : '真消息'}<br>
        <strong>假消息概率：</strong> ${(data.probabilities.fake * 100).toFixed(2)}%<br>
        <strong>真消息概率：</strong> ${(data.probabilities.real * 100).toFixed(2)}%<br>
        <strong>相关标题：</strong> ${data.matched_title || '无匹配标题'}<br>
        <strong>内容摘要：</strong> ${data.database_entry?.content || '无匹配内容'}
    `;

    // 显示查询时间戳
    const currentTime = new Date().toLocaleString();
    resultTimestamp.textContent = `查询时间：${currentTime}`;

    // 显示结果区域
    resultSection.style.display = 'block';
}

// 更新错误信息到页面
function updateResultError(errorMessage) {
    const resultSection = document.getElementById('result');
    const resultText = document.getElementById('result-text');
    const resultTimestamp = document.getElementById('result-timestamp');

    // 显示错误信息
    resultText.innerHTML = `<strong>错误：</strong>${errorMessage}`;

    // 显示当前时间戳
    const currentTime = new Date().toLocaleString();
    resultTimestamp.textContent = `查询时间：${currentTime}`;

    // 显示结果区域
    resultSection.style.display = 'block';
}

// 平滑滚动功能
function smoothScroll(target) {
    const element = document.querySelector(target);
    element.scrollIntoView({ behavior: 'smooth' });
}

// 重置结果区域的内容
function resetResult() {
    const resultSection = document.getElementById('result');
    const resultText = document.getElementById('result-text');
    const resultTimestamp = document.getElementById('result-timestamp');

    // 清空内容
    resultText.innerHTML = '';
    resultTimestamp.textContent = '';

    // 隐藏结果区域
    resultSection.style.display = 'none';
}

// 监听重置按钮点击事件
document.querySelector('button[type="reset"]').addEventListener('click', resetResult);


var textarea = document.querySelector('textarea');
        
textarea.addEventListener('input', (e) => {
    textarea.style.height = '230px';
    textarea.style.height = e.target.scrollHeight + 'px';
});
