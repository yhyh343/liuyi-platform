# AI六爻决策控制台

传统六爻命理问卦平台，基于 FastAPI + SQLite +  vanilla HTML/CSS/JS

## 功能
- 自由聊天问卦（SSE流式响应）
- 六爻起卦（铜钱/时间/数字起卦）
- 卦象AI深度解析（8步流程）
- 多轮追问对话
- 卦例历史记录

## 技术栈
- 后端：Python 3.14 + FastAPI + SQLite
- 前端：原生 HTML/CSS/JS
- AI：DeepSeek API

## 本地运行
```bash
cd backend
pip install -r ../requirements.txt
python start_server.py
```
访问 http://127.0.0.1:8000
