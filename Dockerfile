# Bước 1: Chọn base image với phiên bản Python ổn định
# python:3.11-slim là một lựa chọn tốt, nhẹ và tương thích với các thư viện
FROM python:3.11-slim

# Bước 2: Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Bước 3: Tối ưu hóa build cache
# Copy file requirements.txt trước để tận dụng cache của Docker
# Nếu file này không đổi, Docker sẽ không cần cài lại thư viện ở các lần build sau
COPY requirements.txt .

# Bước 4: Cài đặt các thư viện Python
# --no-cache-dir giúp giảm kích thước image
RUN pip install --no-cache-dir -r requirements.txt

# Bước 5: Copy toàn bộ code của dự án vào container
COPY . .

# Bước 6: Chạy script setup để tạo các thư mục và dữ liệu cần thiết
# Bước này tương đương với việc bạn chạy `python run_demo.py` lần đầu
RUN python run_demo.py

# Bước 7: Mở port 5000 để có thể truy cập từ bên ngoài container
EXPOSE 5000

# Bước 8: Lệnh mặc định để khởi chạy ứng dụng khi container bắt đầu
CMD ["python", "app.py"]