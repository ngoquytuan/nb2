# 🛡️ Spam Filter Demo - AI-Powered Anti-Scam Chat System

Demo hệ thống lọc spam/lừa đảo sử dụng Naive Bayes + LLM cho tin nhắn tiếng Việt.

## ✨ Tính năng chính

- **Real-time Processing**: Xử lý tin nhắn theo thời gian thực
- **AI Pipeline**: Naive Bayes → LLM Analysis → Decision
- **Multi-provider LLM**: OpenAI, Groq, OpenRouter
- **Admin Dashboard**: Theo dõi logs và thống kê
- **Export Data**: Xuất logs ra CSV
- **Responsive UI**: Giao diện đẹp, responsive

## 🏗️ Kiến trúc hệ thống
Client → Flask API → SQLite Queue → Naive Bayes → LLM → Decision → Inbox

## 🚀 Cài đặt và chạy

# Cài đặt numpy trước
pip install numpy

# Cài đặt scipy
pip install scipy

# Cài đặt scikit-learn
pip install scikit-learn

# Cài đặt các package còn lại
pip install Flask==2.3.3
pip install Flask-SocketIO==5.3.6
pip install pandas==2.0.3
pip install requests==2.31.0
pip install python-socketio==5.8.0

### 1. Clone project và setup

```bash
# Tạo thư mục và copy các file
mkdir spam_filter_demo
cd spam_filter_demo

# Copy tất cả các file theo cấu trúc đã cung cấp
# Hoặc tạo từng file theo hướng dẫn

# Chạy script setup
python run_demo.py
Cấu hình API Key (tuỳ chọn)
# OpenAI (khuyên dùng)
export OPENAI_API_KEY="your-openai-key"

# Hoặc Groq (nhanh, miễn phí)
export GROQ_API_KEY="your-groq-key"

# Hoặc OpenRouter
export OPENROUTER_API_KEY="your-openrouter-key"
Lưu ý: Nếu không có API key, hệ thống sẽ dùng mock analysis để demo.

3. Chạy ứng dụng
python app.py
Mở trình duyệt: http://localhost:5000

🎮 Cách sử dụng demo
Gửi tin nhắn test
Quick Test: Nhấn các nút Legitimate/Suspicious/Spam
Custom Message: Nhập tin nhắn tự do
Real-time: Xem kết quả xử lý theo thời gian thực
Xem kết quả
📥 Inbox: Tin nhắn hợp lệ
⚠️ Flagged: Tin nhắn nghi vấn
🚫 Blocked: Tin nhắn spam đã chặn
🔧 Admin: Xem tất cả + filter logs
Export dữ liệu
Click "Export Logs" để tải file CSV với đầy đủ thông tin xử lý.

📊 Ví dụ tin nhắn test
✅ Legitimate
"Xin chào, tôi muốn hỏi về sản phẩm"
"Cảm ơn bạn đã hỗ trợ"
"Khi nào có meeting tiếp theo?"
⚠️ Suspicious
"Anh chuyển khoản giúp em được không?"
"Link này hay lắm, vào xem đi"
"Gửi mã OTP giúp tôi"
❌ Spam
"CHÚC MỪNG! Trúng 100 triệu VND"
"Vay tiền nhanh không thế chấp"
"CẢNH BÁO! Tài khoản sẽ bị khóa"
🔧 Cấu hình
Chỉnh sửa config.py:

LLM_PROVIDER: 'openai', 'groq', hoặc 'openrouter'
NAIVE_BAYES_THRESHOLD: Ngưỡng confidence (0.7)
Database path: SQLite location
📁 Cấu trúc project
spam_filter_demo/
├── app.py                 # Flask app chính
├── config.py              # Cấu hình  
├── run_demo.py           # Script setup
├── requirements.txt       
├── models/
│   ├── naive_bayes.py     # NB classifier
│   └── llm_analyzer.py    # LLM calls
├── database/
│   └── db_manager.py      # SQLite operations
├── static/                # Frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
└── data/
    └── training_data.json # Training dataset
🎯 Workflow xử lý
Nhận message → Queue (SQLite)
Naive Bayes phân loại cơ bản
High confidence → Pass/Block ngay
Low confidence → Gửi LLM phân tích
Final decision → Inbox/Flag/Block
Real-time update → WebSocket to client
🛠️ Tech Stack
Backend: Flask, SQLite, scikit-learn
AI: Naive Bayes, OpenAI/Groq/OpenRouter
Frontend: Vanilla JS, WebSocket
Styling: CSS Grid, Flexbox, Responsive
📈 Mở rộng
Thêm training data từ thực tế
Integrate với email/SMS gateway
Fine-tune model với dữ liệu Việt Nam
Thêm rule-based filters
Database scaling (PostgreSQL)
Demo by: Spam Filter Team License: MIT

Bây giờ bạn có một hệ thống demo hoàn chỉnh! Để chạy:

Tạo thư mục và copy tất cả các file theo cấu trúc
Chạy setup: python run_demo.py
Chạy app: python app.py
Mở browser: http://localhost:5000