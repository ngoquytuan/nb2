#!/usr/bin/env python3
"""
Script khởi tạo toàn diện cho demo Spam Filter
"""

import os
import sys
import subprocess
import json
import shutil # Thêm thư viện để di chuyển file
import platform # Thêm thư viện để kiểm tra hệ điều hành

# --- CẢI TIẾN: Import model để huấn luyện trước ---
from models.naive_bayes import NaiveBayesFilter

def print_header(title):
    print("\n" + "=" * 50)
    print(f"▶️  {title.upper()}")
    print("=" * 50)

def setup_virtual_env():
    """
    CẢI TIẾN: Khuyến nghị và hướng dẫn tạo môi trường ảo (venv)
    """
    print_header("Thiết lập môi trường ảo (Virtual Environment)")
    if "VIRTUAL_ENV" in os.environ:
        print("✅ Bạn đang ở trong một môi trường ảo.")
        return True

    if os.path.exists("venv"):
        print("✅ Thư mục 'venv' đã tồn tại.")
    else:
        print("🚀 Tạo môi trường ảo...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Môi trường ảo 'venv' đã được tạo.")

    print("\n⚠️ Vui lòng kích hoạt môi trường ảo và chạy lại script này!")
    if platform.system() == "Windows":
        print("   Lệnh: .\\venv\\Scripts\\activate")
    else:
        print("   Lệnh: source venv/bin/activate")
    return False

def install_requirements():
    """
    CẢI TIẾN: Cài đặt thư viện một cách trực tiếp hơn
    """
    print_header("Cài đặt các thư viện cần thiết")
    print("📦 Đang cài đặt từ requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Tất cả thư viện đã được cài đặt thành công.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi cài đặt thư viện: {e}")
        sys.exit(1) # Dừng script nếu cài đặt lỗi

def create_directories_and_fix_structure():
    """
    Tạo thư mục cần thiết và sửa cấu trúc nếu cần
    """
    print_header("Tạo cấu trúc thư mục")
    dirs = ['database', 'models', 'static', 'data', 'templates']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   - Đã tạo/xác nhận thư mục: {dir_name}/")

    # --- CẢI TIẾN: Tự động di chuyển index.html ---
    source_path = 'static/index.html'
    dest_path = 'templates/index.html'
    if os.path.exists(source_path) and not os.path.exists(dest_path):
        print("\n🔧 Phát hiện 'index.html' trong 'static/'. Đang di chuyển đến 'templates/'...")
        shutil.move(source_path, dest_path)
        print("✅ Đã di chuyển 'index.html' thành công.")

def create_training_data():
    """Tạo file training data nếu chưa có"""
    print_header("Chuẩn bị dữ liệu huấn luyện")
    # (Giữ nguyên code tạo data của bạn)
    data_file = 'data/training_data.json'
    if os.path.exists(data_file):
        print("✅ Dữ liệu huấn luyện đã tồn tại.")
        return
    print("📊 Đang tạo file training_data.json...")
    # ... (phần code json.dump của bạn ở đây)
    training_data = {
        "legitimate": ["Xin chào", "Cảm ơn bạn"],
        "spam": ["Trúng thưởng 100 triệu", "Vay tiền nhanh"],
        "suspicious": ["Link này hay lắm", "Gửi mã OTP giúp tôi"]
    }
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    print("✅ Dữ liệu huấn luyện đã được tạo.")


def pre_train_model():
    """
    CẢI TIẾN: Huấn luyện trước model Naive Bayes
    """
    print_header("Huấn luyện Model Naive Bayes")
    if os.path.exists('models/nb_model.pkl'):
        print("✅ Model đã được huấn luyện từ trước.")
    else:
        print("⏳ Bắt đầu huấn luyện model... (việc này có thể mất vài giây)")
        try:
            nb_filter = NaiveBayesFilter()
            nb_filter.train_model()
            print("✅ Model đã được huấn luyện và lưu lại.")
        except Exception as e:
            print(f"❌ Lỗi trong quá trình huấn luyện model: {e}")

def show_final_instructions():
    """Hiển thị hướng dẫn cuối cùng"""
    print_header("HOÀN TẤT CÀI ĐẶT")
    print("🎉 Mọi thứ đã sẵn sàng!")
    print("\n🏃‍♂️ Để chạy ứng dụng, gõ lệnh:")
    print("   python app.py")
    print("\n🌐 Sau đó, mở trình duyệt tại địa chỉ:")
    print("   http://localhost:5000")


def main():
    print("🚀 SCRIPT CÀI ĐẶT TOÀN DIỆN CHO SPAM FILTER DEMO 🚀")
    if not setup_virtual_env():
        return # Dừng lại để người dùng kích hoạt venv

    install_requirements()
    create_directories_and_fix_structure()
    create_training_data()
    pre_train_model()
    show_final_instructions()

if __name__ == "__main__":
    # Đảm bảo script chỉ chạy khi có các thư mục con cần thiết
    if not all(os.path.exists(d) for d in ['models', 'static']):
        print("❌ Lỗi: Vui lòng chạy script này từ thư mục gốc của dự án (nơi chứa app.py).")
    else:
        main()