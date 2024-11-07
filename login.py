import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join('db', 'C:\\Users\\choro\\cookiestars\\database.db')

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS USERS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PASSWORD TEXT NOT NULL,
            NAME TEXT NOT NULL,
            EMAIL TEXT NOT NULL UNIQUE,
            AGE INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('login.html')

# 로그인 정보가 사용자 DB와 일치하는지 확인
@app.route('/login', methods=['GET'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
        '''SELECT NAME FROM USERS WHERE EMAIL=? AND PASSWORD=?''',
        (email, password))
        users = cursor.fetchall()
        return jsonify({"result" : users}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500
    finally:
        conn.close()


@app.route('/logined_index')
def logined_main():
    return render_template('logined_index.html')

# 서버 실행
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=6200, debug=True)
