# HƯỚNG DẪN CHẠY ỨNG DỤNG QUẢN LÝ CHI TIÊU

## Cách 1: Chạy Local (Đơn giản nhất)

### Bước 1: Cài đặt Python
- Tải Python từ https://python.org (phiên bản 3.8 trở lên)
- Khi cài đặt, nhớ tick "Add Python to PATH"

### Bước 2: Chạy server
- Mở thư mục dự án
- Double-click file `run_server.bat`
- Đợi server khởi động (sẽ hiển thị "Running on http://127.0.0.1:5000")

### Bước 3: Mở ứng dụng
- Mở trình duyệt
- Vào địa chỉ: `http://localhost:5000` hoặc mở file `index.html`

## Cách 2: Chạy thủ công

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Khởi tạo database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Chạy server
python app.py
```

## Các tính năng đã sửa:

✅ **Thống kê**: Hiển thị chi tiết theo tháng/năm
✅ **Vay nợ**: Quản lý khoản vay/cho vay
✅ **Tiết kiệm**: Tạo mục tiêu tiết kiệm
✅ **Giọng nói**: Sửa lỗi "50 đ" → "50.000 đ"
✅ **API**: Tự động chuyển đổi local/online

## Lưu ý:
- Nếu gặp lỗi, kiểm tra Python đã cài đặt chưa
- Database sẽ được tạo tự động ở `instance/expense.db`
- Để dừng server: nhấn Ctrl+C trong terminal