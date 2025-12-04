# Sử dụng Python 3.9 trên nền Debian Bullseye (Bản ổn định cũ) để tránh lỗi thư viện bị thiếu
FROM python:3.9-slim-bullseye

# 1. Cài đặt các gói hệ thống cần thiết
# Lưu ý: Chúng ta KHÔNG cài tesseract-ocr-vie bằng apt-get nữa vì hay bị lỗi tìm không thấy gói
# Thay vào đó ta cài 'curl' để tải file ngôn ngữ thủ công
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Tải thủ công dữ liệu Tiếng Việt (vie.traineddata) từ GitHub
# Cách này ổn định hơn, đảm bảo 100% có dữ liệu tiếng Việt
RUN mkdir -p /usr/share/tesseract-ocr/tessdata
RUN curl -L -o /usr/share/tesseract-ocr/tessdata/vie.traineddata [https://github.com/tesseract-ocr/tessdata_best/raw/main/vie.traineddata](https://github.com/tesseract-ocr/tessdata_best/raw/main/vie.traineddata)

# 3. Thiết lập biến môi trường để Tesseract biết chỗ tìm file dữ liệu
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata/

# 4. Thiết lập thư mục làm việc
WORKDIR /app

# 5. Copy file requirements và cài thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy toàn bộ code vào
COPY . .

# 7. Tạo thư mục uploads để chứa ảnh tạm thời
RUN mkdir -p uploads

# 8. Lệnh chạy App bằng Gunicorn (Server Production)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]