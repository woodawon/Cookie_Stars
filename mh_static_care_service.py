from flask import Flask, request, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import os
import sqlite3

###
# - 추가 작업 사항 -
# 프롬프트 엔지니어링을 chatgpts에 만든 걸 여기에 링크 말고, 쌩으로 가져와서 적용시키자.
# 적용 시키고, 해당 chatgpts 프롬프트 엔지니어링된 내용 직접 테스트 해보고, 
# 테스트 한 거 url 공유로 혹시 모르니 url 학습에도 한 개 추가해보면 좋을듯. 
# 이렇게만 하고 나서 DB 추가해서 완성하고 테스트 돌리고 버그 수정해서 완료하면 됨.
# ###

# *(sample)*
# 대화 주제 : 대인 관계, 학업
# 사용자 정보 : 이름 : 이수혁, 성별 : 남성, 나이 : 16

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = ""
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join('db', 'C:\\Users\\choro\\cookiestars\\database.db')

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor() 
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS TEST (
            EMAIL TEXT NOT NULL UNIQUE,
            RELATIONSHIP INTEGER NOT NULL,
            RECTAL INTEGER NOT NULL,
            ACADEMIC INTEGER NOT NULL,
            FAMILY INTEGER NOT NULL,
            HEALTH INTEGER NOT NULL,
            COURSE INTEGER NOT NULL
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
    "https://chatgpt.com/g/g-67373a6580308190b9654fa37a95540e-mental-helseu-jindan-seobiseu-mental-helseu-seutaetig",
    "https://drive.google.com/file/d/1Iy1WzIoMI-CvfUlxsLkKFmG3Nglw847L/view?usp=sharing"
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]

# OpenAI GPT-4 API 호출 함수
def generate_response(prompt, categories):
    # 다중 카테고리를 하나의 문자열로 변환
    categories_text = ", ".join(categories)

    msg_history = [
        {
            "role": "system",
            "content": "당신은 비약물적 우울증 치료와 멘탈케어를 전문으로 하는 친절한 AI입니다."
            + "사용자의 감정과 고민에 깊이 공감하며, 따뜻한 태도로 응답해 주세요."
            + "비공식적이고 자연스러운 말투를 사용하며, 존중과 이해를 바탕으로 문제를 함께 고민하고 실질적인 조언을 제공하세요."
            + "사용자에게 안전하고 지지적인 환경을 제공하며, 감정을 존중하고 긍정적인 방향으로 대화를 이끌어 주세요."
            + f"대화 주제를 꼭 인지하여 대화를 진행해주셔야 합니다. 선택된 대화 주제: {categories_text}."
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

# 기본 라우트
@app.route("/")
def index():
    return render_template("mh_static_care_service.html")

# 채팅 라우트
@app.route("/mh_static_chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    categories = request.json.get("variables", [])

    if not user_input or not categories:
        return jsonify({"error": "메시지와 카테고리가 필요합니다."}), 400

    # OpenAI 응답 생성
    response = generate_response(user_input, categories)

    # 데이터베이스에 사용자 선택 저장
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO TEST (EMAIL, RELATIONSHIP, RECTAL, ACADEMIC, FAMILY, HEALTH, COURSE) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "test@example.com",
            1 if "대인관계" in categories else 0,
            1 if "직장" in categories else 0,
            1 if "학업" in categories else 0,
            1 if "가족" in categories else 0,
            1 if "건강" in categories else 0,
            1 if "진로" in categories else 0,
        )
    )
    conn.commit()
    conn.close()

    return jsonify({"response": response})

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)
