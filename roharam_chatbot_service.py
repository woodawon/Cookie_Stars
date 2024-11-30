from flask import Flask, request, session, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import os
import sqlite3
import json
import re

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join("db", "C:\\Users\\MASTER\\cookiestars\\database.db")

# OpenAI API 키 설정
openai.api_key = ""
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

fixed = ""


# 웹 페이지에서 HTML 데이터를 가져와 BeautifulSoup 객체로 변환
def fetch_html(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")


# 다양한 자료를 가져오는 URL 리스트
urls = [
    "https://docs.google.com/document/d/1yaEIK-3-vM_tkT3hmwz6ByzFvtq21nsREdM3cI409X0/edit",
    "https://www.061mind.or.kr/gurye/contentsView.do?pageId=gurye16",
    "https://www.psychiatricnews.net/news/articleView.html?idxno=16546",
    "https://mobile.hidoc.co.kr/healthstory/news/C0000312959",
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]


# OpenAI GPT-4 API 호출 함수
def generate_response(user_input):

    conn = None
    email = session.get("user", {}).get("email")

    try:
        print(f"연결 중인 데이터베이스 경로: {DATABASE}")
        conn = sqlite3.connect(DATABASE)
        print("데이터베이스 연결 성공")
        cursor = conn.cursor()
        cursor.execute("""SELECT NAME, AGE, GENDER FROM USER WHERE EMAIL=?""", (email,))
        user = cursor.fetchone()
        print(f"쿼리 결과: {user}")
        if not user:
            return jsonify({"status": "error", "error": "사용자 정보가 존재하지 않습니다."}), 404
    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}")
        return jsonify({"status": "error", "error": f"데이터베이스 오류 발생: {str(e)}"}), 500
    finally:
        if conn is not None:
            conn.close()


    # 메시지 히스토리 초기화
    msg_history = [
        {
            "role": "system",
            "content": "당신은 친절하고 비약물적 우울증 치료 및 멘탈케어를 전문으로 하는 AI입니다. 사용자의 감정에 공감하며 따뜻한 대화를 나누고, 존중과 이해를 바탕으로 실질적인 조언을 제공합니다. 안전하고 지지적인 환경을 제공하며 긍정적인 방향으로 대화를 이끌어 주세요.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"이 문서는 우리 서비스 내용에 관한 문서입니다. 모든 내용을 반드시 읽고 학습해 주시되, 생애주기와 관련된 내용을 반드시 숙지하여 사용자의 정보를 바탕으로 생애주기를 고려한 대화를 할 수 있게 해주세요. (추가 설명 : 사용자의 연령대에 따라 뚜렷한 AI의 답변 차이점이 보이는 말투, 가치관 등의 구성으로 대화해주세요.): {html_contents[0].text}, {html_contents[1].text}, {html_contents[2].text}, {html_contents[3].text}",
                },
                {
                    "type": "text",
                    "text": "시작 멘트 : 안녕하세요, 하람님! 하람님께 비타민을 충전시켜 드릴 로하람 챗봇이에요. 반가워요!",
                },
                {
                    "type": "text",
                    "text": "시작 시 입력 예시 : 대화 컨셉 : 핑크피치 비타민",
                },
                {
                    "type": "text",
                    "text": "주의사항 : 1. 입력받은 대화 컨셉에 따라 그에 어울리는 대화를 해주세요. 대화 주제는 핑크피치 비타민, 연고 비타민으로 총 2개 중 하나로 결정됩니다.",
                },
                {
                    "type": "text",
                    "text": " 2. 핑크피치 비타민 : 더 활력 있는 마음이 되도록 내면을 가꾸고 싶을 때 선택하는 대화 컨셉.",
                },
                {
                    "type": "text",
                    "text": " 3. 연고 비타민 비타민 : 상처 나고 지친 마음에 연고를 발라 새살이 돋는 것처럼 케어와 힐링을 받고 싶을 때 선택하는 대화 컨셉.",
                },
                {
                    "type": "text",
                    "text": " 4. max token = 200으로, 약 200자 내외로 모든 말들을 해주면 됩니다. 중요한 건, 문장을 200자보다 더 많이 생성했는데, 토큰은 200으로 제한되어 있다 보니까 문장을 그냥 잘라버리는 경우가 아닌, 200자 내외로 모든 말이 다 끝나게 대화를 해줘야 한다는 겁니다. 또한, 200으로 설정을 했다고 해서, 이 숫자를 의식하여 억지로 글을 더 많이 생성할 필요도 없습니다. 150자를 넘지 말라는 거지, 글이 더 적은 것 등은 괜찮습니다.",
                },
                {
                    "type": "text",
                    "text": " 5. 사용자가 대화 종료 라고 입력해야 대화가 종료됩니다.",
                },
                {"type": "text", "text": f"대화 컨셉 : {fixed}"},
                {
                    "type": "text",
                    "text": f"사용자 정보 : 이름 : {user[0]}, 성별 : {user[1]}, 나이 : {user[2]}",
                },
            ],
        },
    ]

    msg_history.append({"role": "user", "content": user_input})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o", messages=msg_history, temperature=0.7
        )
        answer = response.choices[0].message["content"].strip()
        msg_history.append({"role": "assistant", "content": answer})
        return answer
    except openai.error.Timeout:
        return "응답 시간이 초과되었습니다. 다시 시도해 주세요."
    except openai.error.APIError as e:
        return f"API 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"


# 기본 라우트
@app.route("/")
def index():
    return render_template("roharam_chatbot_service.html")


@app.route("/start", methods=["POST"])
def start():
    global fixed
    fixed = request.json.get("variable")  # HTTP 요청 내에서 'variable' 값 가져오기
    return jsonify({"response": "start"})


# 채팅 라우트
@app.route("/roharam_chat", methods=["POST"])
def chat():
    global fixed
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "메시지가 필요합니다."}), 400

    if user_input.strip() == "대화 종료":
        return jsonify({"response": "exit"})

    print(f"Selected conversation theme: {fixed}")

    response = generate_response(user_input)
    return jsonify({"response": response})


# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100)
