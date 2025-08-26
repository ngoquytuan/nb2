#!/usr/bin/env python3
"""
Script cài đặt clean cho Spam Filter Demo
"""

import os
import sys
import subprocess
import json
import platform

def print_header():
    print("🛡️  SPAM FILTER DEMO - CLEAN SETUP")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print("=" * 50)

def create_virtual_env():
    """Tạo virtual environment (khuyến nghị)"""
    if not os.path.exists('venv'):
        print("🌍 Creating virtual environment...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("✅ Virtual environment created")
            
            # Hướng dẫn activate
            if platform.system() == "Windows":
                activate_cmd = "venv\\Scripts\\activate"
            else:
                activate_cmd = "source venv/bin/activate"
            
            print(f"📝 To activate: {activate_cmd}")
            return True
        except Exception as e:
            print(f"⚠️  Could not create venv: {e}")
            return False
    else:
        print("✅ Virtual environment already exists")
        return True

def install_requirements_minimal():
    """Cài đặt requirements với cách tiếp cận minimal"""
    print("📦 Installing packages (minimal approach) {requirements_file}...")
    
    # Cài đặt từng package riêng lẻ để tránh conflict
    packages = [
        "Flask==3.0.0",
        "Flask-SocketIO==5.3.6", 
        "scikit-learn==1.5.2",
        "numpy>=1.26",
        "requests==2.31.0",
        "python-socketio==5.8.0",
        "eventlet==0.33.3"
    ]
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                package, "--no-warn-script-location", "--quiet"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Warning installing {package}: {e}")
    
    # Pandas cài riêng với flag đặc biệt
    try:
        print("   Installing pandas (with special flags)...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pandas==2.1.4", 
            "--no-build-isolation",
            "--no-warn-script-location", 
            "--quiet"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("   ✅ pandas")
    except subprocess.CalledProcessError:
        print("   ⚠️  Pandas install had warnings (this is normal)")

def create_minimal_requirements():
    """Tạo file requirements tối giản"""
    minimal_req = """Flask==3.0.0
Flask-SocketIO==5.3.6
scikit-learn==1.3.2
numpy==1.24.3
requests==2.31.0
python-socketio==5.8.0
eventlet==0.33.3
pandas==2.1.4
"""
    
    with open('requirements_minimal.txt', 'w') as f:
        f.write(minimal_req)
    
    print("✅ Created requirements_minimal.txt")

def verify_installation():
    """Kiểm tra cài đặt"""
    print("🔍 Verifying installation...")
    
    required_packages = {
        'flask': 'Flask',
        'sklearn': 'scikit-learn', 
        'numpy': 'NumPy',
        'requests': 'Requests',
        'socketio': 'python-socketio',
        'pandas': 'Pandas'
    }
    
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
            return False
    
    return True

def create_directories():
    """Tạo thư mục cần thiết"""
    print("📁 Creating directories...")
    
    dirs = ['database', 'models', 'static', 'data']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   ✅ {dir_name}/")

def create_training_data():
    """Tạo training data"""
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
            "Có thể gửi thêm thông tin không?"
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
            "Xác thực thông tin ngân hàng để tránh bị hack"
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
            "Xác nhận thông tin để nhận quà"
        ]
    }
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Training data created")

def create_run_script():
    """Tạo script chạy đơn giản"""
    run_script = '''#!/usr/bin/env python3
"""
Chạy Spam Filter Demo
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, socketio
    print("🚀 Starting Spam Filter Demo...")
    print("🌐 Open: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all packages are installed:")
    print("   python setup_clean.py")
except KeyboardInterrupt:
    print("\\n👋 Demo stopped")
except Exception as e:
    print(f"❌ Error: {e}")
'''
    
    with open('run.py', 'w') as f:
        f.write(run_script)
    
    print("✅ Created run.py script")

def show_usage():
    """Hiển thị hướng dẫn sử dụng"""
    print("\n🎯 SETUP COMPLETED!")
    print("=" * 30)
    print("📋 Next steps:")
    print("")
    print("1. 🚀 Run the demo:")
    print("   python run.py")
    print("")
    print("2. 🌐 Open browser:")
    print("   http://localhost:5000")
    print("")
    print("3. 🧪 Test features:")
    print("   • Send test messages")
    print("   • Try different message types") 
    print("   • Check admin panel")
    print("")
    print("4. 🔧 Configure API (optional):")
    print("   • Set OPENAI_API_KEY for real LLM")
    print("   • Or use mock analysis (default)")
    print("")
    print("📂 Files created:")
    print("   • Training data: data/training_data.json")
    print("   • Run script: run.py")
    print("   • Requirements: requirements_minimal.txt")

def main():
    print_header()
    
    # Option to create venv
    print("❓ Create virtual environment? (recommended)")
    print("   This helps avoid package conflicts")
    
    if platform.system() == "Windows":
        user_input = input("Create venv? [y/N]: ").lower()
        if user_input == 'y':
            create_virtual_env()
            print("\n⚠️  Please activate venv and run this script again:")
            print("   venv\\Scripts\\activate")
            print("   python setup_clean.py")
            return
    
    create_minimal_requirements()
    install_requirements_minimal()
    
    if verify_installation():
        create_directories()
        create_training_data() 
        create_run_script()