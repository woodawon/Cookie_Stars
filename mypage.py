from flask import Flask, session, jsonify, render_template
import openai
from flask_cors import CORS
import os
import sqlite3

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = ""
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join('db', 'C:\\Users\\choro\\cookiestars\\database.db')

@app.route("/mypage")
def user():
    if "user" in session:
        user = session["user"]
        return render_template("mypage.html", user=user)

@app.route('/mypage/mh_static_care_service', methods=['GET'])
def mypage_details():
    email = session.get('user', {}).get('email')  # 현재 로그인한 사용자 이메일
    if not email:
        return jsonify({"status": "error", "error": "사용자가 로그인되지 않았습니다."}), 403

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 이메일로 사용자 기록 조회
        cursor.execute(
            """
            SELECT RELATIONSHIP, RECTAL, ACADEMIC, FAMILY, HEALTH, COURSE
            FROM TEST
            WHERE EMAIL = ?
            """, (email,)
        )
        records = cursor.fetchall()
        conn.close()

        # 결과를 JSON 형식으로 변환
        data = [
            {
                "대인 관계": record[0],
                "직장": record[1],
                "학업": record[2],
                "가족": record[3],
                "건강": record[4],
                "진로": record[5]
            }
            for record in records
        ]

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500