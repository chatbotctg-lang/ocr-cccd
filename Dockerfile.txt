# Sử dụng Python 3.9 trên nền Linux nhẹ (Slim)
FROM python:3.9-slim

# 1. Cài đặt các gói hệ thống cần thiết (Tesseract + Tiếng Việt + Thư viện xử lý ảnh)
# Đây là bước quan trọng nhất để Server hiểu được Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Thiết lập thư mục làm việc
WORKDIR /app

# 3. Copy file requirements và cài thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy toàn bộ code vào
COPY . .

# 5. Tạo thư mục uploads để chứa ảnh tạm thời
RUN mkdir -p uploads

# 6. Lệnh chạy App bằng Gunicorn (Server Production)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]