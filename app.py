from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# 設定資料庫檔案路徑
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定義資料表模型
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now)

# 初始化資料庫
with app.app_context():
    db.create_all()

# 首頁：讀取所有留言
@app.route('/')
def index():
    # 按時間倒序排列（最新的在上面）
    all_messages = Message.query.order_by(Message.date_posted.desc()).all()
    return render_template('index.html', messages=all_messages)

# 新增留言功能
@app.route('/post_message', methods=['POST'])
def post_message():
    name = request.form.get('user_name')
    text = request.form.get('content')
    
    if name and text:
        new_msg = Message(user_name=name, content=text)
        db.session.add(new_msg)
        db.session.commit()
    
    return redirect(url_for('index'))

# 刪除留言功能
@app.route('/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    msg_to_delete = Message.query.get_or_404(message_id)
    try:
        db.session.delete(msg_to_delete)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "刪除時發生錯誤"

# 關於頁面
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)