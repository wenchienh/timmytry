// 初始化：頁面載入時顯示默認分類文章
window.onload = function () {
    fetchAndShowArticles('health'); // 默認加載健康分類文章
};

// 動態顯示文章：根據選擇的分類從後端獲取文章數據
function fetchAndShowArticles(category) {
    const articlesSection = document.getElementById('articles');
    articlesSection.innerHTML = '載入中...';

    // 發送請求到後端獲取對應分類文章
    fetch(`https://your-backend-url.com/articles?category=${category}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('無法獲取文章數據');
            }
            return response.json();
        })
        .then(data => {
            articlesSection.innerHTML = ''; // 清空之前的內容

            if (data.length > 0) {
                data.forEach(article => {
                    const articleDiv = document.createElement('div');
                    articleDiv.classList.add('article');
                    articleDiv.innerHTML = `
                        <h2>${article.title}</h2>
                        <p>${article.content}</p>
                    `;
                    articlesSection.appendChild(articleDiv);
                });
            } else {
                articlesSection.innerHTML = `<p>目前沒有此分類的文章。</p>`;
            }
        })
        .catch(error => {
            console.error('錯誤:', error);
            articlesSection.innerHTML = `<p>無法加載文章，請稍後再試。</p>`;
        });
}

// 處理用戶輸入，將文字提交到後端 API
document.getElementById('submit').addEventListener('click', (event) => {
    event.preventDefault(); // 防止表單提交刷新頁面

    const inputText = document.getElementById('inputtext').value.trim();
    const resultSection = document.getElementById('result');

    if (!inputText) {
        resultSection.innerHTML = `<p>請輸入一些文字！</p>`;
        return;
    }

    resultSection.innerHTML = '分析中...';

    // 發送 POST 請求到後端 API
    fetch('https://your-backend-url.com/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('API 請求失敗');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                resultSection.innerHTML = `<p>錯誤：${data.error}</p>`;
            } else {
                // 顯示分析結果
                resultSection.innerHTML = `<p>預測結果：${data.result}</p>`;
            }
        })
        .catch(error => {
            console.error('錯誤:', error);
            resultSection.innerHTML = `<p>分析失敗，請稍後再試。</p>`;
        });
});

// 在 outcome.html 顯示之前的分析結果
if (window.location.pathname.includes('outcome.html')) {
    const previousResult = localStorage.getItem('predictionResult');
    const resultElement = document.getElementById('percentage-num');

    if (previousResult) {
        resultElement.innerText = previousResult;
    } else {
        resultElement.innerText = '沒有可用的分析結果。';
    }
}

// 點擊次數計數功能
function incrementViewCount(counterId, articleId) {
    let currentCount = parseInt(localStorage.getItem(articleId)) || 0;
    currentCount++;
    localStorage.setItem(articleId, currentCount);
    document.getElementById(counterId).innerText = currentCount;
}

// Smooth Scroll 功能
function smoothScroll(target) {
    const headerHeight = document.querySelector('header').offsetHeight;
    const element = document.querySelector(target);
    const offsetPosition = element.offsetTop - headerHeight;

    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
    });
}
