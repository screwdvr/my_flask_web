from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# --- 設定 (Configurations) ---
# SECRET_KEY 用於 Session 安全加密
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-999')

# 智能資料庫連線：優先讀取 Railway 提供的 DATABASE_URL
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    # 修正 SQLAlchemy 對於新版 PostgreSQL 協定名稱的要求 (從 postgres:// 改為 postgresql://)
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 登入管理器 (Login Manager) ---
login_manager = LoginManager()
login_manager.login_view = 'login' 
login_manager.init_app(app)

# --- 資料表模型 (Models) ---

# 使用者模型：將資料表命名為 'users' 以避開 PostgreSQL 的保留字 'user'
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# 留言模型
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now)

# 初始化資料庫：建立所有資料表
with app.app_context():
    db.drop_all()
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 路由設定 (Routes) ---

# 首頁：顯示所有留言
@app.route('/')
def index():
    messages = Message.query.order_by(Message.date_posted.desc()).all()
    return render_template('index.html', messages=messages)

# 新增留言
@app.route('/post_message', methods=['POST'])
def post_message():
    name = request.form.get('user_name')
    text = request.form.get('content')
    if name and text:
        new_msg = Message(user_name=name, content=text)
        db.session.add(new_msg)
        db.session.commit()
    return redirect(url_for('index'))

# 刪除留言：僅限登入管理員操作
@app.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    msg_to_delete = Message.query.get_or_404(message_id)
    db.session.delete(msg_to_delete)
    db.session.commit()
    flash('留言已成功刪除')
    return redirect(url_for('index'))

# 註冊頁面：建立管理員帳號
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 檢查帳號是否重複
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('帳號已存在，請嘗試其他名稱')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('註冊成功！請登入')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('登入失敗，請檢查帳號或密碼')
            
    return render_template('login.html')

# 登出功能
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- 啟動程式 ---
if __name__ == '__main__':
    # 讀取環境變數 PORT，確保 Railway 部署正確
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)