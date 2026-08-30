const API_BASE = "http://localhost:8000";

let currentCategory = "";
let currentCaseId = null;
let currentGuaDisk = null;
let chatHistory = [];
let currentMode = "normal";

// ===== Navigation =====
function showPanel(id) {
    document.querySelectorAll(".step-panel").forEach(p => p.style.display = "none");
    const panel = document.getElementById(id);
    if (panel) {
        panel.style.display = "block";
        setTimeout(() => panel.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    }
}

function backToHome() {
    document.querySelectorAll(".step-panel").forEach(p => p.style.display = "none");
    currentCaseId = null;
    currentCategory = "";
    currentGuaDisk = null;
    chatHistory = [];
    document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("question-input").value = "";
    document.getElementById("calibrate-result").style.display = "none";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ===== Action Buttons =====
document.querySelectorAll(".action-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const mode = btn.dataset.mode;
        currentMode = mode;
        if (mode === "ai-assist") { showPanel("panel-ai-assist"); return; }
        if (mode === "normal" || mode === "xiang") {
            showPanel("panel-category");
        } else if (mode === "trend") {
            showPanel("panel-history");
            loadGuaList();
        } else if (mode === "history") {
            showPanel("panel-history");
            loadGuaList();
        }
    });
});

// ===== Category Selection =====
document.querySelectorAll(".cat-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentCategory = btn.dataset.cat;
    });
});

// ===== Submit Question =====
document.getElementById("submit-question").addEventListener("click", async () => {
    const question = document.getElementById("question-input").value.trim();
    if (!question || question.length < 5) {
        alert("请输入至少5个字的具体问题");
        return;
    }
    if (!currentCategory) {
        alert("请先选择占事分类");
        return;
    }
    const btn = document.getElementById("submit-question");
    btn.disabled = true;
    btn.textContent = "校准中...";
    try {
        const res = await fetch(API_BASE + "/api/gua/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, category: currentCategory, method: "coin" })
        });
        const data = await res.json();
        showCalibrateResult(data);
    } catch (e) {
        alert("请求失败: " + e.message);
    }
    btn.disabled = false;
    btn.textContent = "校准问题并起卦";
});

function showCalibrateResult(data) {
    const box = document.getElementById("calibrate-result");
    box.style.display = "block";
    if (data.success && data.data && data.data.calibrate_info.need_refine) {
        box.className = "calibrate-box invalid";
        const suggestions = (data.data.calibrate_info.refine_suggestions || []).map(s => "<li>" + escapeHtml(s) + "</li>").join("");
        box.innerHTML = "<p><strong>问题需要细化：</strong></p><ul>" + suggestions + "</ul>" +
            "<p style='margin-top:8px'>清晰度评分: " + data.data.calibrate_info.clarity_score.toFixed(2) + "</p>" +
            "<button class=\"btn-primary\" style='margin-top:10px;padding:8px 16px;font-size:0.85em' onclick='this.parentElement.style.display=\"none\"'>重新输入</button>";
    } else if (data.success && data.data) {
        box.className = "calibrate-box valid";
        box.innerHTML = "<p><strong>问题已通过校准</strong></p>" +
            "<p>清晰度: " + data.data.calibrate_info.clarity_score.toFixed(2) +
            " | 有具体事件: " + (data.data.calibrate_info.has_specific_event ? "是" : "否") +
            " | 有决策目标: " + (data.data.calibrate_info.has_decision_goal ? "是" : "否") + "</p>" +
            "<button class=\"btn-primary\" style='margin-top:10px;padding:8px 16px;font-size:0.85em' onclick='goToMethod()'>继续起卦</button>";
        currentCaseId = data.data.case_id;
        currentGuaDisk = data.data.gua_disk;
    }
}

function goToMethod() {
    showPanel("panel-method");
}

// ===== Method Selection =====
document.querySelectorAll(".method-card").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".method-card").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const isNumber = btn.dataset.method === "number";
        document.getElementById("number-area").style.display = isNumber ? "flex" : "none";
    });
});

document.getElementById("confirm-number").addEventListener("click", async () => {
    const num = parseInt(document.getElementById("number-input").value);
    if (!num || num < 1) { alert("请输入有效正整数"); return; }
    await doDivination("number", { input_num: num });
});

// Auto-coin and time
document.querySelectorAll(".method-card").forEach(btn => {
    if (btn.dataset.method !== "number" && !btn.dataset.handled) {
        btn.dataset.handled = "1";
        btn.addEventListener("click", () => {
            const method = btn.dataset.method === "coin-auto" ? "coin" : btn.dataset.method;
            doDivination(method, {});
        });
    }
});

// ===== Divination =====
async function doDivination(method, params) {
    const activeBtn = document.querySelector(".method-card.active");
    if (activeBtn) activeBtn.disabled = true;

    if (!currentCaseId) {
        const question = document.getElementById("question-input").value.trim();
        const res = await fetch(API_BASE + "/api/gua/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, category: currentCategory, method, params })
        });
        const data = await res.json();
        if (!data.success || data.code !== 200) {
            alert("创建卦例失败: " + (data.message || "未知错误"));
            if (activeBtn) activeBtn.disabled = false;
            return;
        }
        currentCaseId = data.data.case_id;
        currentGuaDisk = data.data.gua_disk;
    }

    // Show coin animation
    showCoinAnimation();

    setTimeout(async () => {
        hideCoinAnimation();
        showPanel("panel-result");
        renderGuaDisk(currentGuaDisk);
        await analyzeGua(currentCaseId);
        if (activeBtn) activeBtn.disabled = false;
    }, 2500);
}

// ===== Coin Animation =====
function showCoinAnimation() {
    const overlay = document.getElementById("coin-overlay");
    overlay.style.display = "flex";
    const coins = [document.getElementById("c1"), document.getElementById("c2"), document.getElementById("c3")];
    coins.forEach((c, i) => {
        c.className = "coin";
        void c.offsetWidth;
        c.className = "coin flip" + (i + 1);
    });
    document.getElementById("anim-yao").textContent = "";
}

function hideCoinAnimation() {
    document.getElementById("coin-overlay").style.display = "none";
}

// ===== Render Gua Disk =====
function renderGuaDisk(disk) {
    const container = document.getElementById("gua-display");
    if (!disk || !disk.yao_details) { container.innerHTML = ""; return; }

    const yaoNames = ["初", "二", "三", "四", "五", "上"];
    const yaoLabels = ["初六","初九","二六","二九","三六","三九","四六","四九","五六","五九","上六","上九"];

    let html = '<div class="gua-name">' + escapeHtml(disk.gua_name || "卦盘") + '</div>';
    html += '<div class="gua-meta">';
    if (disk.upper_gua) html += '<span>上卦: ' + escapeHtml(disk.upper_gua) + '</span>';
    if (disk.lower_gua) html += '<span>下卦: ' + escapeHtml(disk.lower_gua) + '</span>';
    if (disk.palace) html += '<span>' + escapeHtml(disk.palace) + '</span>';
    html += '</div>';

    html += '<div class="gua-lines">';
    // Render from top (yao 6) to bottom (yao 1)
    const details = disk.yao_details || [];
    for (let i = 5; i >= 0; i--) {
        const y = details[i] || {};
        const isYang = y.yang_yin === "阳";
        const isMoving = y.moving;
        const label = yaoNames[5 - i];
        html += '<div class="gua-line ' + (isYang ? "" : "yin") + (isMoving ? " moving" : "") + '">';
        html += '<span class="gua-line-label">' + label + '</span>';
        html += '<div class="gua-line-bar"></div>';
        if (isMoving) html += '<span class="gua-line-moving">动</span>';
        html += '</div>';
    }
    html += '</div>';

    if (disk.trend) {
        html += '<div class="gua-meta"><span>趋势: ' + escapeHtml(disk.trend) + '</span></div>';
    }

    container.innerHTML = html;
}

// ===== Analyze Gua =====
async function analyzeGua(caseId) {
    const loading = document.getElementById("analysis-loading");
    const result = document.getElementById("analysis-result");
    loading.style.display = "block";
    result.style.display = "none";

    // Progress animation
    let progress = 0;
    const fill = document.getElementById("progress-fill");
    const timer = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        fill.style.width = progress + "%";
    }, 300);

    try {
        const res = await fetch(API_BASE + "/api/gua/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: caseId })
        });
        const data = await res.json();
        clearInterval(timer);
        fill.style.width = "100%";

        setTimeout(() => {
            loading.style.display = "none";
            if (data.success && data.data) {
                displayAnalysisResult(data.data.analysis_result, data.data.gua_disk);
            } else {
                result.style.display = "block";
                result.innerHTML = "<p style='color:#c85050'>解析失败: " + escapeHtml(data.message || "未知错误") + "</p>";
            }
        }, 500);
    } catch (e) {
        clearInterval(timer);
        loading.style.display = "none";
        result.style.display = "block";
        result.innerHTML = "<p style='color:#c85050'>解析失败: " + escapeHtml(e.message) + "</p>";
    }
}

function displayAnalysisResult(analysis, guaDisk) {
    const result = document.getElementById("analysis-result");
    result.style.display = "block";
    const g = guaDisk || {};
    const trend = analysis.step7_trend || "平";
    const trendIcon = trend === "吉" ? "sun" : trend === "需留意" ? "warning" : "circle";
    const trendColor = trend === "吉" ? "#4ade80" : trend === "需留意" ? "#f87171" : "#fbbf24";
    const confidence = Math.round((analysis.confidence || 0.5) * 100);

    let html = "";
    html += '<div class="trend-banner" style="text-align:center;padding:12px 0;margin-bottom:12px;border-bottom:1px solid rgba(200,168,78,0.2)">';
    html += '<span style="font-size:1.4em">' + (trend === "吉" ? "&#9728;" : trend === "需留意" ? "&#9888;" : "&#9898;") + "</span> ";
    html += '<span style="font-size:1.1em;color:' + trendColor + ';font-weight:600">趋势：' + escapeHtml(trend) + "</span> ";
    html += '<span style="color:var(--text-dim);font-size:0.85em">置信度 ' + confidence + "%</span>";
    html += "</div>";

    const steps = [
        ["step1_yong_shen", "取用神"],
        ["step2_shi_ying", "察世应"],
        ["step3_moving", "观动爻"],
        ["step4_wang_shuai", "断旺衰"],
        ["step5_pattern", "看格局"],
        ["step6_rag_ref", "参RAG"],
    ];

    for (const [key, title] of steps) {
        const val = analysis[key];
        if (!val) continue;
        html += '<div class="step-card">';
        html += '<div class="step-title">&#128161; ' + escapeHtml(title) + "</div>";
        html += '<div class="step-content">' + escapeHtml(val) + "</div>";
        html += "</div>";
    }

    if (analysis.step8_advice) {
        html += '<div class="step-card advice">';
        html += '<div class="step-title">&#128221; 建议参考</div>';
        html += '<div class="step-content">' + escapeHtml(analysis.step8_advice) + "</div>";
        html += "</div>";
    }

    if (analysis.disclaimer) {
        html += '<div class="disclaimer">' + escapeHtml(analysis.disclaimer) + "</div>";
    }

    html += '<div class="analysis-meta">';
    html += "<span>卦名: " + escapeHtml(g.gua_name || "") + "</span>";
    html += "<span>上卦: " + escapeHtml(g.upper_gua || "") + "</span>";
    html += "<span>下卦: " + escapeHtml(g.lower_gua || "") + "</span>";
    html += "<span>趋势: " + escapeHtml(g.trend || "") + "</span>";
    html += "</div>";

    result.innerHTML = html;
    document.getElementById("chat-section").style.display = "block";
}

// ===== Case Chat =====
document.getElementById("case-chat-send").addEventListener("click", sendCaseChat);
document.getElementById("case-chat-input").addEventListener("keypress", e => {
    if (e.key === "Enter") sendCaseChat();
});

async function sendCaseChat() {
    const input = document.getElementById("case-chat-input");
    const message = input.value.trim();
    if (!message || !currentCaseId) return;
    input.value = "";
    appendChatMessage("user", message, "case-chat-history");

    const sendBtn = document.getElementById("case-chat-send");
    sendBtn.disabled = true;

    try {
        const resp = await fetch(API_BASE + "/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: currentCaseId, message })
        });
        const reader = resp.body.getReader();
        const dec = new TextDecoder();
        let buf = "", fullText = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            let idx;
            while ((idx = buf.indexOf("\n")) !== -1) {
                const line = buf.substring(0, idx).trim();
                buf = buf.substring(idx + 1);
                if (line.startsWith("data: ")) {
                    try {
                        const d = JSON.parse(line.substring(6));
                        if (d.token) fullText += d.token;
                        else if (d.text) fullText = d.text;
                    } catch(e) {}
                }
            }
        }
        if (fullText) appendChatMessage("assistant", fullText, "case-chat-history");
    } catch (e) {
        appendChatMessage("assistant", "回复失败，请稍后重试", "case-chat-history");
    }
    sendBtn.disabled = false;
}

// ===== Quick Chat =====
document.getElementById("quick-send").addEventListener("click", sendQuickChat);
document.getElementById("quick-input").addEventListener("keypress", e => {
    if (e.key === "Enter") sendQuickChat();
});
document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
        document.getElementById("quick-input").value = chip.dataset.q;
        sendQuickChat();
    });
});

async function sendQuickChat() {
    const input = document.getElementById("quick-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    appendChatMessage("user", message, "chat-messages");

    const sendBtn = document.getElementById("quick-send");
    sendBtn.disabled = true;

    try {
        const resp = await fetch(API_BASE + "/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: null, message })
        });
        const reader = resp.body.getReader();
        const dec = new TextDecoder();
        let buf = "", fullText = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            let idx;
            while ((idx = buf.indexOf("\n")) !== -1) {
                const line = buf.substring(0, idx).trim();
                buf = buf.substring(idx + 1);
                if (line.startsWith("data: ")) {
                    try {
                        const d = JSON.parse(line.substring(6));
                        if (d.token) fullText += d.token;
                        else if (d.text) fullText = d.text;
                    } catch(e) {}
                }
            }
        }
        if (fullText) appendChatMessage("assistant", fullText, "chat-messages");
    } catch (e) {
        appendChatMessage("assistant", "回复失败，请稍后重试", "chat-messages");
    }
    sendBtn.disabled = false;
}

function appendChatMessage(role, text, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const div = document.createElement("div");
    div.className = "chat-msg " + role;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ===== Gua List =====
async function loadGuaList() {
    const list = document.getElementById("gua-list");
    list.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:20px">加载中...</p>';
    try {
        const res = await fetch(API_BASE + "/api/gua/list?page=1&size=20");
        const data = await res.json();
        if (data.success && data.data && data.data.items.length > 0) {
            list.innerHTML = data.data.items.map(item =>
                '<div class="gua-item" onclick="loadGuaCase(\'' + item.case_id + '\')">' +
                '<div class="qi">' + escapeHtml(item.question) + '</div>' +
                '<div class="meta">' + escapeHtml(item.gua_name || "") + ' · ' + escapeHtml(item.category || "") + ' · ' + (item.created_at || "").substring(0, 10) + '</div>' +
                '</div>'
            ).join("");
        } else {
            list.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:20px">暂无卦例记录</p>';
        }
    } catch (e) {
        list.innerHTML = '<p style="color:#c85050;text-align:center;padding:20px">加载失败</p>';
    }
}

async function loadGuaCase(caseId) {
    try {
        const res = await fetch(API_BASE + "/api/gua/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: caseId })
        });
        const data = await res.json();
        if (data.success) {
            currentCaseId = caseId;
            currentGuaDisk = data.data.gua_disk || { yao_details: [], gua_name: "未知" };
            showPanel("panel-result");
            renderGuaDisk(currentGuaDisk);
            displayAnalysisResult(data.data.analysis_result, data.data.gua_disk);
        }
    } catch (e) {
        alert("加载失败: " + e.message);
    }
}

// ===== Utils =====
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ===== Bagua Ring Symbols =====
(function() {
    const symbols = ["\u2630","\u2631","\u2632","\u2633","\u2634","\u2635","\u2636","\u2637"];
    ["bagua-outer", "bagua-mid", "bagua-inner"].forEach((id, ri) => {
        const el = document.getElementById(id);
        if (!el) return;
        const count = ri === 0 ? 8 : ri === 1 ? 6 : 4;
        const radius = ri === 0 ? 88 : ri === 1 ? 62 : 38;
        for (let i = 0; i < count; i++) {
            const span = document.createElement("span");
            span.textContent = symbols[i % 8];
            span.style.cssText = "position:absolute;font-size:" + (ri === 0 ? "12" : ri === 1 ? "10" : "8") + "px;color:rgba(200,168,78," + (0.15 + ri * 0.1) + ");top:50%;left:50%;transform-origin:0 0;";
            const angle = (i / count) * Math.PI * 2;
            const px = Math.cos(angle) * radius;
            const py = Math.sin(angle) * radius;
            span.style.transform = "translate(-50%,-50%) translate(" + px + "px," + py + "px)";
            el.appendChild(span);
        }
    });
})();

// ===== Y ao Preview Animation =====
(function() {
    const rows = document.querySelectorAll(".yao-row .yao-char");
    const symbols = ["\u268a","\u268b"];
    let idx = 0;
    setInterval(() => {
        rows.forEach((r, i) => {
            r.textContent = symbols[Math.floor(Math.random() * 2)];
            r.style.opacity = 0.3 + Math.random() * 0.5;
        });
        idx++;
    }, 2000);
})();
