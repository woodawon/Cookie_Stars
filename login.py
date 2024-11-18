import os
import sqlite3
from flask import Flask, request, session, jsonify, render_template, redirect, url_for
from flask_cors import CORS

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join("db", "C:\\Users\\MASTER\\cookiestars\\database.db")


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
            AGE INTEGER NOT NULL,
            GENDER TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("logined_index"))  # logined_index 함수 호출
    return render_template("login.html")


# 로그인 정보가 사용자 DB와 일치하는지 확인
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email").strip()
    password = data.get("password").strip()

    # 해당 email과 password에 해당하는 사용자 정보를
    # sqlite로 뽑아서 세션에 저장하는 코드 작성할 것

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT NAME, EMAIL, AGE, GENDER FROM USERS WHERE EMAIL=? AND PASSWORD=?""", (email, password)
        )
        user = cursor.fetchone()
        if user:
            # 세션에 로그인 정보 저장
            session["user"] = {
                "name" : user[0],
                "email" : user[1],
                "age" : user[2],
                "gender" : user[3],
            }
            return jsonify({"result": user[0]}), 200
        else:
            return jsonify({"result": "이메일 또는 비밀번호가 잘못되었습니다."}), 401
    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/logined_index")
def logined_index():
    if "user" in session:
        user = session["user"]
        return render_template("logined_index.html", user=user["name"])
    return redirect(url_for("index"))  # index 함수 호출


@app.route("/logout")
def logout():
    session.pop("user", None)  # 세션에서 로그인 정보 제거
    # 세션에 저장돼 있는 모든 로그인 정보 다 제거하는 코드 작성할 것.
    return redirect("http://127.0.0.1:5500/templates/index.html")


@app.route("/mypage")
def user():
    if "user" in session:
        user = session["user"]
        return render_template("mypage.html", user=user)
    return redirect(url_for("index"))


# 서버 실행
if __name__ == "__main__":
    init_db()  # 데이터베이스 초기화
    app.run(host="0.0.0.0", port=6200, debug=True)
