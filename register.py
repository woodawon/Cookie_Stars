import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join("db", "C:\\Users\\MASTER\\cookiestars\\database.db")

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS USER (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PASSWORD TEXT NOT NULL,
            NAME TEXT NOT NULL,
            EMAIL TEXT NOT NULL UNIQUE,
            AGE INTEGER NOT NULL,
            GENDER TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('register.html')

# 회원가입 라우트
@app.route('/register', methods=['POST'])
def signup():
    data = request.json
    if not data:
        return jsonify({"status": "error", "error": "잘못된 요청입니다."}), 400  # 빈 요청 처리

    name = data.get("name")
    age = data.get("age")
    email = data.get("email")
    password = data.get("password")
    gender = data.get("gender")

    # 유효성 검사
    if not all([name, age, email, password]):
        return jsonify({"status": "error", "error": "모든 필드를 입력해 주세요."}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 데이터 삽입
        cursor.execute('''
            INSERT INTO USER (PASSWORD, NAME, EMAIL, AGE, GENDER)
            VALUES (?, ?, ?, ?, ?)
        ''', (password, name, email, age, gender))
        
        conn.commit()  # 변경사항 저장

        response = jsonify({"status" : "success"})
        response.headers['Content-Type'] = 'application/json'
        return response, 201  # 성공 메시지

    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "error": "이미 등록된 이메일입니다."}), 400
    except sqlite3.Error as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": f"오류가 발생했습니다: {str(e)}"}), 500
    finally:
        conn.close()

# 서버 실행
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=6100, debug=True)
