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
DATABASE = os.path.join("db", "C:\\Users\\MASTER\\cookiestars\\database.db")

@app.route('/mypage/mh_static_care_service', methods=['GET'])
def mh_static_care_service():
    email = session.get('user', {}).get('email')  # 현재 로그인한 사용자 이메일
    if not email:
        return jsonify({"status": "error", "error": "사용자가 로그인되지 않았습니다."}), 403

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 이메일로 사용자 기록 조회
        cursor.execute(
            """
            SELECT RELATIONSHIP, RECTAL, ACADEMIC, FAMILY, HEALTH, COURSE, MHEALTH, MTEMP
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
                "진로": record[5],
                "마음 건강": record[6],
                "마음 온도": record[7]
            }
            for record in records
        ]

        return render_template("mh_details.html", data=data)

    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500

@app.route('/mypage/detail_customized_human_care_service', methods=['GET'])
def detail_customized_human_care_service():
    email = session.get('user', {}).get('email')  # 현재 로그인한 사용자 이메일
    if not email:
        return jsonify({"status": "error", "error": "사용자가 로그인되지 않았습니다."}), 403

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 설계표 데이터를 조회하도록 쿼리 수정 필요 (예: WRITE 테이블)
        cursor.execute(
            """
            SELECT THEME, TITLE, CONTENT, REASON
            FROM WRITE
            WHERE EMAIL = ?
            """, (email,)
        )
        records = cursor.fetchall()
        conn.close()

        # 결과를 JSON 형식으로 변환
        data = [
            {
                "주제": record[0],
                "제목": record[1],
                "설계": record[2],
                "이유": record[3]
            }
            for record in records
        ]

        return render_template("detail_details.html", data=data)

    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6300, debug=True)