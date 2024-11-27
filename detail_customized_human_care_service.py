###
# - 추가 작업 사항 -
# chatgpts에 만든 디테일 맞춤형 휴먼 케어 서비스 프롬프트 엔지니어링된 모델의 
# 내용물을 쌩으로 가져와서 적용만 시키며, 그 후엔 ai 실시간 응답 챗봇과 표 작성이 
# 한 페이지 내에서 분할되어 각각 동작 및 처리되도록 구현한 뒤 
# 테스트하고 버그 수정하여 완료하면 됨.
# ###
from flask import Flask, request, session, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import os
import sqlite3
import json

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join('db', 'C:\\Users\\choro\\cookiestars\\database.db')

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor() 
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS WRITE (
            EMAIL TEXT NOT NULL,
            THEME TEXT NOT NULL,
            TITLE TEXT NOT NULL,
            CONTENT TEXT NOT NULL,
            REASON TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 웹 페이지에서 HTML 데이터를 가져와 BeautifulSoup 객체로 변환
def fetch_html(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

# 다양한 자료를 가져오는 URL 리스트
urls = [
    "https://chatgpt.com/share/67376215-f41c-800b-8e93-5cff605a2b07",
    "https://drive.google.com/file/d/1UWDmGU241MbnrS8KG9-IRWr-d6Q0L1FS/view?usp=sharing"
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]

# OpenAI GPT-4 API 호출 함수
def generate_response(prompt, categories):
    # 다중 카테고리를 하나의 문자열로 변환
    categories_text = ", ".join(categories)
    email = session.get('user', {}).get('email')

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT NAME, AGE, GENDER FROM USERS WHERE EMAIL=?""", (email)
        )
        user = cursor.fetchone()
    except Exception as e:
        return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500
    finally:
        conn.close()

    msg_history = [
        {
            "role": "system",
            "content": ""
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"이 파일은 당신이 학습해야 할 지식(Knowledge)입니다. {urls[1]}",
                },
                {
                    "type": "text",
                    "text": f"이 파일은 미리 지식을 학습한 모델의 대화 예시입니다. {urls[0]}",
                },
            ],
        },
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=msg_history,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()

    except openai.error.Timeout:
        return "응답 시간이 초과되었습니다. 다시 시도해 주세요."
    except openai.error.APIError as e:
        return f"API 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

@app.route('/')
def index():
    return render_template('detail_customized_human_care_service.html')

# 회원가입 라우트 -> 디테일 내용 DB에 저장하는 걸로 변경하는 작업 실행.
@app.route('/detail', methods=['POST'])
def signup():

    email = session.get('user', {}).get('email')

    data = request.json
    if not data:
        return jsonify({"status": "error", "error": "잘못된 요청입니다."}), 400  # 빈 요청 처리

    theme = data.get("theme")
    title = data.get("title")
    content = data.get("content")
    reason = data.get("reason")

    # 유효성 검사
    if not all([theme, title, content, reason]):
        return jsonify({"status": "error", "error": "모든 필드를 입력해 주세요."}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 데이터 삽입
        cursor.execute('''
            INSERT INTO WRITE (EMAIL, THEME, TITLE, CONTENT, REASON)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, theme, title, content, reason))
        
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
