#!/usr/bin/env python3
"""
Script để khởi tạo database trên production
Chạy một lần sau khi deploy lên Render
"""

import os
from app import app, db

def init_database():
    """Tạo tất cả tables nếu chưa có"""
    with app.app_context():
        try:
            # Tạo tất cả tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Kiểm tra tables đã tạo
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables created: {tables}")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")

if __name__ == "__main__":
    init_database()