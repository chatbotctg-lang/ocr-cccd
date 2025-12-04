import os
import cv2
import numpy as np
import pytesseract
import re
import base64
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# ================= CẤU HÌNH TỰ ĐỘNG (QUAN TRỌNG) =================
# Kiểm tra hệ điều hành để set đường dẫn Tesseract
if os.name == 'nt': 
    # WINDOWS: Cần trỏ đúng đường dẫn file .exe bạn đã cài
    # Sửa lại dòng dưới nếu bạn cài ở ổ đĩa khác
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # LINUX (RENDER): Tesseract đã được cài vào hệ thống qua Dockerfile
    # Không cần làm gì cả, code tự tìm thấy lệnh 'tesseract'
    pass

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def preprocess_image_for_cccd(image_path):
    # Đọc ảnh
    img = cv2.imread(image_path)
    
    # Resize ảnh lớn lên gấp đôi để nét hơn
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Chuyển ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Tách ngưỡng động (Adaptive Threshold) để loại bỏ nền hoa văn
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, \
                                   cv2.THRESH_BINARY, 31, 15)
    
    # Khử nhiễu nhẹ
    denoised = cv2.medianBlur(binary, 3)
    
    return denoised

def extract_info_from_text(text):
    data = {
        "id": "Không tìm thấy",
        "name": "Không tìm thấy",
        "dob": "Không tìm thấy",
        "raw_text": text
    }
    
    lines = text.split('\n')
    
    # 1. Tìm số CCCD (12 chữ số)
    id_match = re.search(r'\b\d{12}\b', text)
    if id_match:
        data['id'] = id_match.group(0)

    # 2. Tìm Ngày sinh (DD/MM/YYYY)
    dob_match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', text)
    if dob_match:
        data['dob'] = dob_match.group(0)

    # 3. Tìm Tên (Logic tìm dòng chữ in hoa sau chữ 'Họ và tên')
    for i, line in enumerate(lines):
        if "Họ và tên" in line or "Ho va ten" in line:
            parts = line.split(':')
            if len(parts) > 1 and len(parts[1].strip()) > 3:
                potential_name = parts[1].strip()
                if potential_name.isupper():
                    data['name'] = potential_name
                    break
            
            # Kiểm tra dòng kế tiếp
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.isupper() and not any(char.isdigit() for char in next_line):
                    data['name'] = next_line
                    break

    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Chưa chọn file'})

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Xử lý ảnh
        processed_img = preprocess_image_for_cccd(filepath)
        
        # Chuyển ảnh đã xử lý sang base64 để hiển thị lại cho client
        _, buffer = cv2.imencode('.jpg', processed_img)
        processed_base64 = base64.b64encode(buffer).decode('utf-8')

        # Gọi Tesseract OCR (Tiếng Việt)
        # --psm 6: Giả định là một khối văn bản thống nhất
        config = '--oem 3 --psm 6 -l vie' 
        text = pytesseract.image_to_string(processed_img, config=config)

        # Trích xuất dữ liệu
        extracted_data = extract_info_from_text(text)

        return jsonify({
            'success': True,
            'data': extracted_data,
            'processed_image': processed_base64
        })

    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True, port=5000)