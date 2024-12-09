
window.onload = function() {
    showSection('health');
};
//需放在最前面，確保網頁載入後就馬上顯示內容

var textarea = document.querySelector('textarea');
        
textarea.addEventListener('input', (e) => {
    textarea.style.height = '230px';
    textarea.style.height = e.target.scrollHeight + 'px';
});
//根據使用者輸入內容調整文字框高度


 function smoothScroll(target) {
 const headerHeight = document.querySelector('header').offsetHeight;
 const element = document.querySelector(target);
 const offsetPosition = element.offsetTop - headerHeight;
      window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
      });
  }
 let currentPage = 0;
//首頁點let's start的下移動畫



function showSection(category) {    
    const articles = {
        health: [
            { title: "健康產業的轉型：挑戰與機遇", content: "人們對健康的關注不斷增加，促使健康產業迎來轉型。" },
            { title: "健康與生活：醫療科技的嶄新時代", content: "醫療科技的發展正在改變人們對健康的看法和生活方式。" },
            {title:"健康風暴！知名製藥公司被爆造假藥品", content: "驚人的揭露！某知名製藥公司被揭發生產的藥品存在嚴重的品質問題。" },
            {title:"健康危機！某健身中心爆發嚴重感染事件", content: "令人震驚的消息！某知名健身中心被曝出嚴重的感染事件。" }
        ],
        politics: [
            { title: "政府推動下的社會變革：挑戰與機遇", content: "政府在推動社會變革方面扮演著關鍵角色。" },
            { title: "政治風波！知名台灣政治人物涉嫌貪腐醜聞曝光", content: "近日，消息指稱知名政治人物涉嫌卷入大規模貪腐醜聞。" }
        ],
        commerce: [
            { title: "新光景下的商業策略：創新與數據驅動", content: "在數字化時代，企業必須不斷創新。" },
            { title: "商業環境的轉變：挑戰與機遇", content: "全球化、技術革命等因素塑造了當今商業環境。" }
        ]
    };

    // 清空文章顯示區域
    const articlesSection = document.getElementById('articles');
    articlesSection.innerHTML = '';

    // 只顯示所選分類的文章
    if (articles[category]) {
        articles[category].forEach((article, index) => {
            const articleId = `${category}-article-${index}`;
            const counterId = `counter-${articleId}`;
            const articleDiv = document.createElement('div');
            articleDiv.id = articleId;

             // 從 localStorage 中獲取初始點擊次數
             const viewCount = localStorage.getItem(articleId) || 0;

             articleDiv.innerHTML = `

             <section class=part-of-articles>
        <h2 onclick="ViewCount('${counterId}', '${articleId}')">
            <a href="#${articleId}">${article.title}</a>
        </h2>
        <p>${article.content}</p>
        <section class="articles-info">
            <img src="image/view.png" alt="" width="15px" height="15px">
            <p id="${counterId}">${viewCount}</p>
        </section>
    </section>
         `;
            articlesSection.appendChild(articleDiv);
        });
    }

    // 移除所有選項的 'active' 類
    const allLinks = document.querySelectorAll('.categories .type a');
    allLinks.forEach(link => {
        link.classList.remove('active');
    });

    // 為點擊的選項添加 'active' 類
    const selectedLink = document.querySelector(`.categories .type a[onclick="showSection('${category}')"]`);
    if (selectedLink) {
        selectedLink.classList.add('active');
    }
}

//在不同裝置打開會從0開始 可能會拔掉這個功能
function ViewCount(counterId, articleId) {
    // 獲取當前的點擊次數，默認為 0
    let viewCount = parseInt(localStorage.getItem(articleId)) || 0;

    // 更新計數並保存到 localStorage
    viewCount++;
    localStorage.setItem(articleId, viewCount);

    // 更新網頁顯示的點擊次數
    updateDisplay(viewCount, counterId);
    
}

function updateDisplay(val, counterId) {
    document.getElementById(counterId).innerHTML = val;
}


function updatePage() {
    const articlesSection = document.getElementById('articles');
    const articles = articlesSection.children;
    const pageWidth = articlesSection.offsetWidth;
    const offset = currentPage * pageWidth;
    articlesSection.style.transform = `translateX(-${offset}px)`;
}



// homepage.html 輸入文字傳遞到API??  Id對應到html id='' 裡面的文字
document.getElementById('submit').addEventListener('click', (event) => {
    event.preventDefault(); // 避免刷新頁面

    const inputText = document.getElementById('inputtext').value;

    fetch('http://127.0.0.1:5000/predict', {  // Flask API 的 URL (不確定是不是這樣)
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: inputText }) // 傳遞用戶輸入的文字
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            // 將結果存進 Local Storage
            localStorage.setItem('predictionResult', data.result);

            // 進到 outcome.html
            window.location.href = 'outcome.html';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('出錯了，請稍後再試。');
    });
});

// 在 outcome.html 顯示結果
if (window.location.pathname.includes('outcome.html')) {
    const result = localStorage.getItem('predictionResult'); // 從 Local Storage 讀取結果

    if (result) {
        document.getElementById('percentage-num').innerText = result; // 更新頁面文字
    } else {
        document.getElementById('percentage-num').innerText = '沒有可用的結果。';
    }
}

    





