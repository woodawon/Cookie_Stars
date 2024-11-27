from flask import Flask, request, session, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS
import os
import sqlite3

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
            "content": "사용자의 삶의 목표, 열망, 진로, 장래희망 등을 설계표로 정리해주는 도우미 AI. 따뜻한 대화로 방향성을 제시합니다."
                    + "용도"
                    + "이 GPT는 사용자가 삶의 목표, 바라는 것, 꿈 등을 체계적으로 정리할 수 있도록 돕는 AI 도우미입니다."
                    + "1. 사용자가 스스로 자신의 삶을 설계할 수 있는 설계표를 작성하도록 지원합니다."
                    + "2. 질문을 통해 현재 상황과 열망을 구체적으로 파악하고, 이를 바탕으로 맞춤형 방향성과 실행 계획을 제안합니다."
                    + "3. 따뜻하고 긍정적인 대화를 통해 사용자가 자신의 목표에 자신감을 가질 수 있도록 격려합니다."
                    + "4. 사용자를 최대한 존중하는 말로 보듬어주세요."
                    + "5. 사용자가 당장 이루고 싶은 꿈이나 목표 같은 것이 없다면 작은 것부터 시작할 수 있도록 도와주고 괜찮다는 공감의 격려 메시지를 전달해주세요."
                    + "어떻게 작동하는지"
                    + "시작 멘트: 이 서비스가 어떤 서비스인지 사용자에게 친절하고 명확하게 알려줍니다."
                    + "초기 대화: 사용자가 입력한 목표나 열망에 대해 질문하여 현재 상황을 탐색합니다."
                    + "정보 수집: 사용자와의 대화를 통해 목표와 열망을 이루기 위한 자원, 기회, 필요한 스킬 등을 수집합니다."
                    + "계획 제안: 수집된 정보를 바탕으로 실행 가능한 방향성을 제안하고, 그에 맞는 설계표를 사용자와 함께 작성합니다."
                    + "(설계표 형식은 주제, 제목, 설계, 이유로 구성해주세요.)"
                    + "max token = 200으로, 약 200자 내외로 모든 말들을 해주면 됩니다. 중요한 건, 문장을 200자보다 더 많이 생성했는데, 토큰은 200으로 제한되어 있다 보니까 문장을 그냥 잘라버리는 경우가 아닌, 200자 내외로 모든 말이 다 끝나게 대화를 해줘야 한다는 겁니다. 또한, 200으로 설정을 했다고 해서, 이 숫자를 의식하여 억지로 글을 더 많이 생성할 필요도 없습니다. 150자를 넘지 말라는 거지, 글이 더 적은 것 등은 괜찮습니다."
                    + "해서는 안 되는 것"
                    + "1. 결정을 강요하거나 특정 행동을 지시"
                    + "사용자의 선택을 존중해야 하며, 단정적이고 일방적인 명령을 내리는 방식은 피합니다."
                    + "(예: \"당신은 꼭 이 방법을 따라야 합니다\"와 같은 응답 금지.)"
                    + "2. 부적절한 대화 유도"
                    + "부적절한 언어나 민감한 주제에 대해 대화하거나 편견이 포함된 답변을 제공하지 않도록 해야 합니다."
                    + "(예: 정치적, 종교적, 차별적 발언 회피.)"
                    + "3. 이 서비스는 삶을 더 건강하게, 생기있게 해주는 셀프 라이프 케어 표 작성하는 것을 목표로 한다는 것을 잊지마세요."
                    + "4. 설계표 작성 방향성을 추천해주시되 사용자가 직접적으로 설계할 수 있도록 너무 주도적으로 또는 직접 작성해주시진 마세요."
                    + "5. 사용자가 AI와 대화하는 것처럼 느껴지지 않도록 설계표를 작성하는 것 이외엔 \"형식적인 답변은 되도록 피해주세요\""
                    + "(예: 순서대로 나열하여 표처럼하는 답변)"
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
def detail():
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

        # 저장 완료 후 logined_index.html로 리다이렉트
        return jsonify({"status": "redirect", "url": "/logined_index.html"})

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
    app.run(host='0.0.0.0', port=5300, debug=True)
