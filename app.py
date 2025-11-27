from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
from ai_module import full_financial_analysis

load_dotenv()

app = Flask(__name__)
CORS(app)
# Database configuration with fallback
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///expense.db'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class VaiTro(db.Model):
    __tablename__ = 'vai_tro'
    id = db.Column(db.Integer, primary_key=True)
    loai_vai_tro = db.Column(db.String(50), nullable=False)
    mo_ta = db.Column(db.String(255))

class NguoiDung(db.Model):
    __tablename__ = 'nguoi_dung'
    id = db.Column(db.Integer, primary_key=True)
    ho_ten = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mat_khau = db.Column(db.String(255), nullable=False)
    so_du = db.Column(db.Float, default=0)
    trang_thai = db.Column(db.String(20), default='Hoạt động')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DanhMuc(db.Model):
    __tablename__ = 'danh_muc'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=False)
    loai_danh_muc = db.Column(db.String(20), nullable=False)
    ten_danh_muc = db.Column(db.String(100), nullable=False)
    mo_ta = db.Column(db.String(255))
    icon = db.Column(db.String(50))

class GiaoDich(db.Model):
    __tablename__ = 'giao_dich'
    id = db.Column(db.Integer, primary_key=True)
    danh_muc_id = db.Column(db.Integer, db.ForeignKey('danh_muc.id'), nullable=False)
    so_tien = db.Column(db.Float, nullable=False)
    mo_ta = db.Column(db.String(255))
    ngay = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TichLuy(db.Model):
    __tablename__ = 'tich_luy'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=False)
    ten_tich_luy = db.Column(db.String(100), nullable=False)
    so_tien_muc_tieu = db.Column(db.Float, nullable=False)
    ngay_ket_thuc = db.Column(db.DateTime)
    trang_thai = db.Column(db.String(20), default='Đang thực hiện')

class VayNo(db.Model):
    __tablename__ = 'vay_no'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=False)
    ho_ten_vay_no = db.Column(db.String(100), nullable=False)
    loai = db.Column(db.String(20), nullable=False)
    trang_thai = db.Column(db.String(20), default='Đang trả')
    so_tien = db.Column(db.Float, nullable=False)
    lai_suat = db.Column(db.Float, default=0)
    ngay_vay_no = db.Column(db.DateTime, default=datetime.utcnow)
    han_tra = db.Column(db.DateTime)
    mo_ta = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('mat_khau') or not data.get('ho_ten'):
            return jsonify({'message': 'Thiếu thông tin'}), 400
        
        if NguoiDung.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email đã tồn tại'}), 400
        
        hashed_password = bcrypt.hashpw(data['mat_khau'].encode('utf-8'), bcrypt.gensalt())
        
        user = NguoiDung(
            ho_ten=data['ho_ten'],
            email=data['email'],
            mat_khau=hashed_password.decode('utf-8'),
            so_du=data.get('so_du', 0)
        )
        
        db.session.add(user)
        db.session.flush()
        
        # Tạo danh mục mặc định
        default_categories = [
            {'loai': 'Chi tiêu', 'ten': 'Ăn uống', 'icon': '🍔'},
            {'loai': 'Chi tiêu', 'ten': 'Giải trí', 'icon': '🎮'},
            {'loai': 'Chi tiêu', 'ten': 'Mua sắm', 'icon': '🛒'},
            {'loai': 'Chi tiêu', 'ten': 'Di chuyển', 'icon': '🚗'},
            {'loai': 'Thu nhập', 'ten': 'Lương', 'icon': '💰'},
            {'loai': 'Thu nhập', 'ten': 'Thưởng', 'icon': '🎁'},
        ]
        
        for cat in default_categories:
            danh_muc = DanhMuc(
                nguoi_dung_id=user.id,
                loai_danh_muc=cat['loai'],
                ten_danh_muc=cat['ten'],
                icon=cat['icon']
            )
            db.session.add(danh_muc)
        
        db.session.commit()
        
        return jsonify({'message': 'Đăng ký thành công', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('mat_khau'):
        return jsonify({'message': 'Thiếu email hoặc mật khẩu'}), 400
    
    user = NguoiDung.query.filter_by(email=data['email']).first()
    
    if not user or not bcrypt.checkpw(data['mat_khau'].encode('utf-8'), user.mat_khau.encode('utf-8')):
        return jsonify({'message': 'Email hoặc mật khẩu không đúng'}), 401
    
    if user.trang_thai == 'Bị khóa':
        return jsonify({'message': 'Tài khoản đã bị khóa'}), 403
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token, 'user_id': user.id}), 200

# Transaction Routes
@app.route('/api/giao-dich', methods=['POST'])
@jwt_required()
def create_transaction():
    from ai_module import full_financial_analysis  # import AI module ở đây

    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Nếu không có danh_muc_id, tự động lấy danh mục mặc định
    danh_muc_id = data.get('danh_muc_id')
    if not danh_muc_id:
        loai = data.get('loai', 'chi')
        loai_danh_muc = 'Chi tiêu' if loai == 'chi' else 'Thu nhập'
        danh_muc = DanhMuc.query.filter_by(nguoi_dung_id=user_id, loai_danh_muc=loai_danh_muc).first()
        if not danh_muc:
            return jsonify({'message': 'Không tìm thấy danh mục mặc định'}), 404
        danh_muc_id = danh_muc.id
    else:
        danh_muc = DanhMuc.query.filter_by(id=danh_muc_id, nguoi_dung_id=user_id).first()
        if not danh_muc:
            return jsonify({'message': 'Danh mục không tồn tại'}), 404
    
    giao_dich = GiaoDich(
        danh_muc_id=danh_muc_id,
        so_tien=data['so_tien'],
        mo_ta=data.get('mo_ta', ''),
        ngay=datetime.fromisoformat(data['ngay']) if 'ngay' in data else datetime.utcnow()
    )
    
    user = NguoiDung.query.get(user_id)
    if danh_muc.loai_danh_muc == 'Chi tiêu':
        user.so_du -= data['so_tien']
    else:
        user.so_du += data['so_tien']
    
    db.session.add(giao_dich)
    db.session.commit()
    
    # --- Gọi AI dự đoán chi tiêu sau khi thêm giao dịch ---
    danh_mucs = DanhMuc.query.filter_by(nguoi_dung_id=user_id).all()
    danh_muc_ids = [dm.id for dm in danh_mucs]
    giao_dichs = GiaoDich.query.filter(GiaoDich.danh_muc_id.in_(danh_muc_ids)).all()
    transactions_history = [{
        'amount': g.so_tien,
        'category': g.danh_muc_id,
        'date': g.ngay.isoformat(),
        'description': g.mo_ta
    } for g in giao_dichs]

    ai_result = full_financial_analysis(transactions_history)
    
    return jsonify({
        'message': 'Giao dịch thành công',
        'so_du_moi': user.so_du,
        'ai_prediction': ai_result
    }), 201

@app.route('/api/giao-dich', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    danh_mucs = DanhMuc.query.filter_by(nguoi_dung_id=user_id).all()
    danh_muc_ids = [dm.id for dm in danh_mucs]
    
    giao_dichs = GiaoDich.query.filter(GiaoDich.danh_muc_id.in_(danh_muc_ids)).all()
    
    return jsonify([{
        'id': g.id,
        'so_tien': g.so_tien,
        'mo_ta': g.mo_ta,
        'ngay': g.ngay.isoformat()
    } for g in giao_dichs]), 200

# Category Routes
@app.route('/api/danh-muc', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    danh_muc = DanhMuc(
        nguoi_dung_id=user_id,
        loai_danh_muc=data['loai_danh_muc'],
        ten_danh_muc=data['ten_danh_muc'],
        mo_ta=data.get('mo_ta', ''),
        icon=data.get('icon', '')
    )
    
    db.session.add(danh_muc)
    db.session.commit()
    
    return jsonify({'message': 'Tạo danh mục thành công', 'id': danh_muc.id}), 201

@app.route('/api/danh-muc', methods=['GET'])
@jwt_required()
def get_categories():
    user_id = int(get_jwt_identity())
    danh_mucs = DanhMuc.query.filter_by(nguoi_dung_id=user_id).all()
    
    return jsonify([{
        'id': dm.id,
        'ten_danh_muc': dm.ten_danh_muc,
        'loai_danh_muc': dm.loai_danh_muc,
        'icon': dm.icon
    } for dm in danh_mucs]), 200

# User Routes
@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = NguoiDung.query.get(user_id)
    
    return jsonify({
        'id': user.id,
        'ho_ten': user.ho_ten,
        'email': user.email,
        'so_du': user.so_du,
        'trang_thai': user.trang_thai
    }), 200

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    user = NguoiDung.query.get(user_id)
    
    if 'ho_ten' in data:
        user.ho_ten = data['ho_ten']
    if 'mat_khau' in data:
        user.mat_khau = bcrypt.hashpw(data['mat_khau'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.session.commit()
    return jsonify({'message': 'Cập nhật thành công'}), 200

# Statistics Routes
@app.route('/api/thong-ke', methods=['GET'])
@jwt_required()
def get_statistics():
    user_id = int(get_jwt_identity())
    danh_mucs = DanhMuc.query.filter_by(nguoi_dung_id=user_id).all()
    danh_muc_ids = [dm.id for dm in danh_mucs]
    
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    chi_tieu = db.session.query(db.func.sum(GiaoDich.so_tien)).filter(
        GiaoDich.danh_muc_id.in_(danh_muc_ids),
        GiaoDich.ngay >= month_start,
        DanhMuc.loai_danh_muc == 'Chi tiêu'
    ).join(DanhMuc).scalar() or 0
    
    thu_nhap = db.session.query(db.func.sum(GiaoDich.so_tien)).filter(
        GiaoDich.danh_muc_id.in_(danh_muc_ids),
        GiaoDich.ngay >= month_start,
        DanhMuc.loai_danh_muc == 'Thu nhập'
    ).join(DanhMuc).scalar() or 0
    
    return jsonify({
        'chi_tieu_thang_nay': chi_tieu,
        'thu_nhap_thang_nay': thu_nhap,
        'so_du': NguoiDung.query.get(user_id).so_du
    }), 200

#AI
@app.route('/api/ai/prediction', methods=['GET'])
@jwt_required()
def ai_prediction():
    user_id = int(get_jwt_identity())

    # 1. Lấy danh mục và giao dịch
    danh_mucs = DanhMuc.query.filter_by(nguoi_dung_id=user_id).all()
    danh_muc_ids = [dm.id for dm in danh_mucs]

    giao_dichs = GiaoDich.query.filter(GiaoDich.danh_muc_id.in_(danh_muc_ids)).all()

    transactions = []
    for g in giao_dichs:
        danh_muc = next((dm.ten_danh_muc for dm in danh_mucs if dm.id == g.danh_muc_id), 'khác')
        transactions.append({
            'danh_muc': danh_muc,
            'so_tien': g.so_tien,
            'mo_ta': g.mo_ta,
            'ngay': g.ngay.isoformat() if g.ngay else None
        })

    # 2. Lấy phân tích hiện tại + gợi ý
    result = full_financial_analysis(transactions)

    advice = result.get('advice', [])
    category_summary = result.get('category_summary', {})
    current_total = result.get('monthly_prediction', {}).get('predicted_amount', 0)

    # 3. Tạo dict category mới theo gợi ý
    new_category_amounts = category_summary.copy()

    import re

    for item in advice:
        # Giảm category xuống target % tổng
        match_cat = re.search(r"Chi tiêu '(.+?)' chiếm [\d\.]+% — nên giảm xuống (\d+)-(\d+)%", item)
        if match_cat:
            cat_name = match_cat.group(1)
            low_pct = int(match_cat.group(2))
            high_pct = int(match_cat.group(3))
            target_ratio = (low_pct + high_pct) / 2 / 100  # trung bình
            # cập nhật category mới = target_ratio * tổng hiện tại
            new_category_amounts[cat_name] = target_ratio * current_total

    # 4. Tính tổng dự đoán mới từ category mới
    predicted_total = sum(new_category_amounts.values())

    # 5. Áp dụng tiết kiệm nếu có
    for item in advice:
        match_save = re.search(r'Hãy dành (\d+)% để tiết kiệm', item)
        if match_save:
            save_ratio = int(match_save.group(1)) / 100
            predicted_total *= (1 - save_ratio)

    # 6. Cập nhật dự đoán
    result['monthly_prediction']['predicted_amount'] = round(predicted_total)

    return jsonify(result), 200



# Tạo bảng khi khởi động
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
