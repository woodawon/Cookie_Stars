from flask import Flask, request, session, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import os
import sqlite3
import json
import re

def parse_response_to_dict(response):
    try:
        # 문자열에서 키-값 쌍을 추출
        pattern = r"'([^']+)'\s*:\s*(\d+)"
        matches = re.findall(pattern, response)

        # 딕셔너리로 변환
        result = {key: int(value) for key, value in matches}
        return result
    except Exception as e:
        app.logger.error(f"파싱 오류: {str(e)}")
        return None


# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)

# OpenAI API 키 설정
openai.api_key = ""
app.secret_key = ""  # 세션 데이터를 암호화하기 위한 키

# SQLite3 데이터베이스 파일 경로 설정
DATABASE = os.path.join("db", "C:\\Users\\MASTER\\cookiestars\\database.db")


# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """ 
        CREATE TABLE IF NOT EXISTS TEST (
            EMAIL TEXT NOT NULL,
            RELATIONSHIP INTEGER,
            RECTAL INTEGER,
            ACADEMIC INTEGER ,
            FAMILY INTEGER,
            HEALTH INTEGER,
            COURSE INTEGER,
            MHEALTH INTEGER,
            MTEMP INTEGER
        )
    """
    )
    conn.commit()
    conn.close()


# 웹 페이지에서 HTML 데이터를 가져와 BeautifulSoup 객체로 변환
def fetch_html(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")


# 다양한 자료를 가져오는 URL 리스트
urls = [
    "https://chatgpt.com/share/67466ab5-f474-800b-9f91-7b6cb93a970a",
    # "https://drive.google.com/file/d/1Iy1WzIoMI-CvfUlxsLkKFmG3Nglw847L/view?usp=sharing",
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]
fixed = []
num = 0

msg_history = [
    {
        "role": "user",
        "content": [
            # {
            #    "type": "text",
            #    "text": f"이 파일은 당신이 학습해야 할 지식(Knowledge)입니다. {html_contents[1].text}",
            # },
            {
                "type": "text",
                "text": f"이 파일은 미리 지식을 학습한 모델의 대화 예시입니다. {html_contents[0].text}",
            },
        ],
    },
]


# OpenAI GPT-4 API 호출 함수
def generate_response(prompt):

    msg_history.append({"role": "user", "content": prompt})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4", messages=msg_history, temperature=0.7
        )
        app.logger.info(f"OpenAI 원본 응답: {response}")

        if response and "choices" in response and len(response.choices) > 0:
            content = response.choices[0].message["content"].strip()
            app.logger.info(f"OpenAI 응답 내용: {content}")
            return content
        else:
            app.logger.warning("OpenAI 응답이 비어 있습니다.")
            return "OpenAI 응답이 비어 있습니다."
    except openai.error.Timeout:
        return "응답 시간이 초과되었습니다. 다시 시도해 주세요."
    except openai.error.APIError as e:
        return f"API 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"


@app.route("/")
def index():
    return render_template("mh_static_care_service.html")


@app.route("/start", methods=["POST"])
def start():
    global fixed
    categories = request.json.get("variables", [])
    fixed = categories
    return jsonify({"response": "start"})


# 기본 라우트
@app.route("/mh_static_chat", methods=["POST"])
def chat():
    global num
    global msg_history
    conn = None
    email = session.get("user", {}).get("email")

    if num == 0:

        # 다중 카테고리를 하나의 문자열로 변환
        categories_text = ", ".join(fixed)

        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT NAME, AGE, GENDER FROM USER WHERE EMAIL=?""", (email,)
            )
            user = cursor.fetchone()
            print(f"대화 주제 : {categories_text}")
            print(f"사용자 정보 : {user[0]}, {user[1]}, {user[2]}")
        except Exception as e:
            return jsonify({"status": "error", "error": f"DB 오류 발생: {str(e)}"}), 500
        finally:
            conn.close()

        msg_history.append(
            {
                "role": "system",
                "content": "1.  아이, 청소년, 20~30대, 40~50대, 노인까지 나누어서 해당 생애 주기의 사람마다 존중 받도록 느끼게 말을 하며 멘탈 헬스 진단을 해주면 돼."
                + "max token = 200으로, 약 200자 내외로 모든 말들을 해주면 돼. 중요한 건, 문장을 200자보다 더 많이 생성했는데, 토큰은 200으로 제한되어 있다 보니까 문장을 그냥 잘라버리는 경우가 아닌, 200자 내외로 모든 말이 다 끝나게 대화를 해줘야 한다는 거야. 또한, 200으로 설정을 했다고 해서, 이 숫자를 의식하여 억지로 글을 더 많이 생성할 필요도 없어. 150자를 넘지 말라는 거지, 글이 더 적은 것 등은 괜찮아."
                + "2. 카테고리에 따라 관련된 질문을 해야 해. 대인 관계, 직장, 학업, 가족, 건강, 진로 중에서 사용자는 원하는 만큼 선택할 것이고 GPT는 선택한 것에 관련된 질문과 답변을 해줘. 추가적으로 현실적인 해결 방안보다는 상대방을 이해하고 대안을 스스로 찾을 수 있도록 하는 것에 초점을 맞춰줘. 그리고 정말 중요한 것은, 대화가 시작될 때 사용자가 어떤 카테고리를 선택했는지, 그리고 사용자에 대한 정보가 입력 예시처럼 무조껀 너에게 사용자 프롬프트에 입력되어 전송될 거라는 거야. 입력 예시처럼 전송된 값을 보고, 선택된 카테고리와 관련된 멘탈 헬스 진단을 해주면 돼. 입력 예시는 다음과 같아."
                + "입력 예시 : "
                + "대화 주제 : 대인 관계, 직장, 학업, 가족, 건강, 진로"
                + "사용자 정보 : 이름 : 김민선, 성별 : 여성, 나이 : 30"
                + "3. 10~20번 정도 대화를 진행하면서 일정 수준 검사를 해주고, 사용자가 '대화 종료' 라고 치기 전까지는 대화를 끝내지 말고 더 진행하며 검사해주면 돼."
                + " 사용자가 선택한 카테고리의 멘탈 헬스 수치를 %로 측정해주면 되고, 추가로 사용자의 마음 온도와 마음 건강도 %로 측정해주면 돼. 사용자가 대답한 글들을 바탕으로 감정을 분석하면서 종합적인 수치 계산 후 측정해주면 돼. 스트레스를 받는 수치에 따라 0~100%까지 '마음 건강' 수치 측정, 행복도의 수치에 따라 0~100%까지 '마음 온도' 수치 측정을 하면 돼. 정말 중요한 것은, 이 대화가 끝날 때 너가 보내주는 결과값을 코드로 퍼센트만 뽑아갈 예정이기 때문에, 사용자가 '대화 종료' 라고 입력했다면 그 어떤 사족도 붙이지 말고 무조껀 종료 시의 출력 예시대로만 답해야 한다는 거야. 출력 예시는 다음과 같아. 모든 항목을 다 줘야 되고, 만약 선택하지 않은 카테고리라면, 0으로 해서 줘야돼."
                + "출력 예시 : [ '대인 관계' : 30 , '직장' : 45, '학업' : 33, '가족' : 50, '건강' : 20, '진로' : 60, '마음 건강' : 40, '마음 온도' : 15 ]"
                + "5. 마지막은 꿀팁인데, 사용자가 선택한 주제에서 대화가 크게 벗어나지 않게 해주고 무조건적인 예시, 팁을 말하는 빈도를 조금 줄이고 그저 공감을 해주는 말을 할때도 많이 필요해 보이니 참고해줘."
                + f"대화 주제 : {categories_text}"
                + f"사용자 정보 : 이름 : {user[0]}, 성별 : {user[1]}, 나이 : {user[2]}",
            }
        )
        num += 1

    try:
        # 사용자 입력 데이터 확인
        user_input = request.json.get("message", None)
        app.logger.info(f"사용자 입력: {user_input}")
        if not user_input:
            raise ValueError("사용자 입력이 없습니다.")

        email = session.get("user", {}).get("email", None)
        app.logger.info(f"세션 이메일: {email}")
        if not email:
            raise ValueError("세션에 이메일 정보가 없습니다.")
    except Exception as e:
        # 예외 발생 시 로그 출력
        app.logger.error(f"에러 발생: {str(e)}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

    # OpenAI 응답 생성
    response = generate_response(user_input)
    app.logger.info(f"OpenAI 응답: {response}")

    if isinstance(response, str):  # 응답이 문자열인지 확인
        if user_input.strip() == "대화 종료":
            try:

                response_data = parse_response_to_dict(response)
                if not response_data:
                    raise ValueError("response 데이터를 파싱할 수 없습니다.")

                # 응답 데이터를 JSON 문자열에서 딕셔너리로 변환
                print(f"response : {response}")
                app.logger.info(f"response_data: {response_data}")
                app.logger.info(response_data.get("대인 관계", 0))
                app.logger.info(response_data.get("직장", 0))

                # 데이터베이스에 사용자 선택 및 AI 응답 값 저장
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO TEST (EMAIL, RELATIONSHIP, RECTAL, ACADEMIC, FAMILY, HEALTH, COURSE, MHEALTH, MTEMP)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        response_data.get("대인 관계", 0),
                        response_data.get("직장", 0),
                        response_data.get("학업", 0),
                        response_data.get("가족", 0),
                        response_data.get("건강", 0),
                        response_data.get("진로", 0),
                        response_data.get("마음 건강", 0),
                        response_data.get("마음 온도", 0)
                    ),
                )
                conn.commit()
                session["diagnosis"] = response_data
                return jsonify({"response": "result"})
            except json.JSONDecodeError as e:
                app.logger.error(f"JSON 디코딩 오류: {str(e)}")
                return jsonify({"error": "응답 데이터를 처리하는 중 오류가 발생했습니다."}), 500
            except Exception as e:
                return jsonify({"error": f"DB 저장 오류: {str(e)}"}), 500
            finally:
                if conn:
                    conn.close()

        # 일반적인 응답 반환
        return jsonify({"response": response})
    else:  # JSON 직렬화 불가능한 경우
        return (
            jsonify({"error": "OpenAI 응답이 JSON 직렬화할 수 없는 형식입니다."}),
            500,
        )


@app.route("/graph")
def graph():
    diagnosis = session.get("diagnosis", {})
    return render_template("graph.html", diagnosis=diagnosis)


# 서버 실행
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5200, debug=True)
