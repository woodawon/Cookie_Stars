from flask import Flask, request, session, jsonify, render_template
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
# 이렇게만 하고 나서 테스트 돌리고 버그 수정해서 완료하면 됨.
# ###

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = ""
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# 최대 메시지 수 설정
# msg_cnt = 50

num = 0
fixed = ""
exit_count = 0  # AI 응답 횟수가 25번이 되었을 때, 서비스 종료

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
    "https://docs.google.com/document/d/1yaEIK-3-vM_tkT3hmwz6ByzFvtq21nsREdM3cI409X0/edit",
    "https://www.061mind.or.kr/gurye/contentsView.do?pageId=gurye16",
    "https://www.psychiatricnews.net/news/articleView.html?idxno=16546",
    "https://www.yonginmh.co.kr/news2/12399",
    "https://mobile.hidoc.co.kr/healthstory/news/C0000312959",
    "https://www.hankyung.com/article/2023051720391",
    "https://app.luminpdf.com/viewer/66dc361185c0bc2263fefd0d?credentials-id=ae1aa3a4-5fdb-4813-8737-2c6a5bf08040",
    "https://app.luminpdf.com/viewer/66dc3637eb85a4c4ec74a3d3?credentials-id=f890ce69-82f3-4826-9a9e-3598b737632d",
    "https://www.psychiatricnews.net/news/articleView.html?idxno=9111",
    "https://blog.naver.com/hyeonse77/222273872237",
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]

# OpenAI GPT-4 API 호출 함수
def generate_response(prompt, js_variable_value):
    global num, fixed  # 전역 변수로 선언
    print("js_variable_value : ", js_variable_value)
    if num == 0:
        fixed = js_variable_value
        num += 1
    print("fixed : ", fixed)

    msg_history = [
        {
            "role": "system",
            "content": "당신은 비약물적 우울증 치료와 멘탈케어를 전문으로 하는 친절한 AI입니다."
            + "사용자의 감정과 고민에 깊이 공감하며, 따뜻한 태도로 응답해 주세요."
            + "비공식적이고 자연스러운 말투를 사용하며, 존중과 이해를 바탕으로 문제를 함께 고민하고 실질적인 조언을 제공하세요."
            + "사용자에게 안전하고 지지적인 환경을 제공하며, 감정을 존중하고 긍정적인 방향으로 대화를 이끌어 주세요."
            + f"대화 주제를 꼭 인지하여 대화를 진행해주셔야 합니다. 대화 주제는 {fixed} 입니다.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"이 문서는 우리 서비스 내용에 관한 문서입니다. 모든 내용을 반드시 읽고 학습해 주시되, 생애주기와 관련된 내용을 반드시 숙지하여 사용자의 정보를 바탕으로 생애주기를 고려한 대화를 할 수 있게 해주세요. (추가 설명 : 사용자의 연령대에 따라 뚜렷한 AI의 답변 차이점이 보이는 말투, 가치관 등의 구성으로 대화해주세요.): {html_contents[0].text}",
                },
                {
                    "type": "text",
                    "text": f"이 문서들은 비약물학적 우울증 치료에 관한 참고 문서입니다. : {html_contents[5].text}, {html_contents[6].text}",
                },
                {
                    "type": "text",
                    "text": f"이 문서들은 우울증 관련 참고 문서입니다. : {', '.join([content.text for content in html_contents[1:5]])}",
                },
                {
                    "type": "text",
                    "text": f"이 문서들은 위로를 해주는 방법 및 말투에 관한 참고 문서입니다. : {html_contents[7].text}, {html_contents[8].text}, {html_contents[9].text}",
                },
            ],
        },
    ]
    msg_history.append({"role": "assistant", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o", messages=msg_history, temperature=0.7
        )

        # if len(msg_history) > msg_cnt:
        #     msg_history.pop(1)

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
    return render_template("mh_static_care_service.html")


# 채팅 라우트
@app.route("/mh_static_chat", methods=["POST"])
def chat():
    global exit_count, num, fixed
    user_input = request.json.get("message")
    js_variable_value = request.json.get("variable")

    if not user_input:
        return jsonify({"error": "메시지가 필요합니다."}), 400

    response = generate_response(user_input, js_variable_value)
    exit_count += 1
    if exit_count == 20:
        exit_count = 0
        num = 0
        fixed = ""
        return render_template("logined_index.html")
    return jsonify({"response": response})


# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)
