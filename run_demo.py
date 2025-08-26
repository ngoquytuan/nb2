#!/usr/bin/env python3
"""
Script khởi tạo demo Spam Filter
"""

import os
import sys
import subprocess
import json

def check_requirements():
    """Kiểm tra và cài đặt requirements"""
    print("🔍 Checking requirements...")
    
    try:
        import flask
        import sklearn
        import pandas
        import numpy
        print("✅ All Python packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("📦 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def create_directories():
    """Tạo thư mục cần thiết"""
    print("📁 Creating directories...")
    
    dirs = ['database', 'models', 'static', 'data']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   ✅ {dir_name}/")

def create_training_data():
    """Tạo file training data nếu chưa có"""
    data_file = 'data/training_data.json'
    
    if os.path.exists(data_file):
        print("✅ Training data already exists")
        return
    
    print("📊 Creating training data...")
    
    training_data = {
        "legitimate": [
            "Xin chào, tôi muốn hỏi về sản phẩm của công ty",
            "Cảm ơn bạn đã hỗ trợ tôi hôm qua",
            "Khi nào có meeting tiếp theo?",
            "Báo cáo tháng này đã hoàn thành",
            "Chúc mừng sinh nhật! Chúc bạn nhiều sức khỏe",
            "Tôi cần hỗ trợ về tài khoản của mình",
            "Lịch làm việc tuần này thế nào?",
            "Sản phẩm này có bảo hành không?",
            "Xin lỗi vì phản hồi muộn",
            "Có thể gửi thêm thông tin không?",
            "Tài liệu dự án đã gửi qua email",
            "Cảm ơn vì buổi họp hôm nay",
            "Deadline dự án là khi nào?",
            "Tôi sẽ hoàn thành công việc vào thứ Hai",
            "Chúc cuối tuần vui vẻ!"
        ],
        "spam": [
            "CHÚC MỪNG! Bạn đã trúng giải 100 triệu VND! Click link ngay",
            "Vay tiền nhanh 24/7, không cần thế chấp! Liên hệ ngay",
            "Khuyến mãi đặc biệt chỉ hôm nay! Giảm 90% tất cả sản phẩm",
            "Bạn có muốn kiếm 50 triệu/tháng tại nhà không?",
            "CẢNH BÁO! Tài khoản sẽ bị khóa nếu không xác thực ngay",
            "Nhấp vào đây để nhận iPhone 15 Pro Max miễn phí",
            "Đầu tư Forex với lợi nhuận 500% mỗi tháng",
            "Thuốc tăng cường sinh lý nam 100% từ thiên nhiên",
            "Mua 1 tặng 10! Cơ hội có 1 không 2!",
            "Xác thực thông tin ngân hàng để tránh bị hack",
            "Trúng số độc đắc 5 tỷ VND! Nhanh tay nhận thưởng",
            "Làm việc online kiếm 100k/giờ, không cần kinh nghiệm",
            "Ưu đãi sốc: Giảm giá 95% chỉ còn 5 phút",
            "Bí quyết làm giàu không ai biết! Download ngay",
            "Nhận 10 triệu miễn phí khi đăng ký tài khoản"
        ],
        "suspicious": [
            "Anh có thể chuyển khoản giúp em không? Em sẽ trả sau",
            "Link này hay lắm, bạn vào xem đi",
            "Tôi cần tiền gấp, bạn có thể giúp không?",
            "Nhấp vào đây để xem ảnh",
            "Bạn có tin tôi không? Đây là cơ hội đầu tư tốt",
            "Gửi mã OTP giúp tôi, tôi đang gặp khó khăn",
            "Tải app này để có tiền thưởng",
            "Bạn muốn làm giàu nhanh không?",
            "Chương trình ưu đãi đặc biệt cho bạn",
            "Xác nhận thông tin để nhận quà",
            "Bạn có thẻ ATM không? Cho mình mượn một chút",
            "Đầu tư với tôi, lãi suất cao, không rủi ro",
            "Bạn có muốn mua thẻ điện thoại giá rẻ không?",
            "Tôi có thông tin nội bộ về cổ phiếu này",
            "Bạn quan tâm đến việc làm thêm tại nhà không?"
        ]
    }
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Training data created")

def setup_config():
    """Hiển thị hướng dẫn cấu hình"""
    print("\n🔧 CONFIGURATION SETUP")
    print("=" * 50)
    print("Để sử dụng LLM analysis, bạn cần cấu hình API key:")
    print("")
    print("1. OpenAI API:")
    print("   export OPENAI_API_KEY='your-api-key'")
    print("")
    print("2. Groq API:")
    print("   export GROQ_API_KEY='your-api-key'")
    print("")
    print("3. OpenRouter API:")
    print("   export OPENROUTER_API_KEY='your-api-key'")
    print("")
    print("📝 Nếu không có API key, hệ thống sẽ dùng mock analysis để demo")
    print("=" * 50)

def main():
    print("🚀 Spam Filter Demo Setup")
    print("=" * 30)
    
    check_requirements()
    create_directories()
    create_training_data()
    setup_config()
    
    print("\n✅ Setup completed!")
    print("\n🏃‍♂️ To run the demo:")
    print("   python app.py")
    print("\n🌐 Then open: http://localhost:5000")
    print("\n📚 Features:")
    print("   • Send test messages")
    print("   • Real-time processing")
    print("   • Naive Bayes + LLM pipeline")
    print("   • Admin panel with logs")
    print("   • Export functionality")

if __name__ == "__main__":
    main()