from flask import Flask, request, jsonify, render_template
import openai
from bs4 import BeautifulSoup
import requests
from flask_cors import CORS

# Flask 애플리케이션 생성
app = Flask(__name__)

# OpenAI API 키 설정
openai.api_key = ''

# 최대 메시지 수 설정
msg_cnt = 50

# 웹 페이지에서 HTML 데이터를 가져와 BeautifulSoup 객체로 변환
def fetch_html(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

# 다양한 자료를 가져오는 URL 리스트
urls = [
    # "https://docs.google.com/document/d/1yaEIK-3-vM_tkT3hmwz6ByzFvtq21nsREdM3cI409X0/edit",
    # "https://www.061mind.or.kr/gurye/contentsView.do?pageId=gurye16",
    # "https://www.psychiatricnews.net/news/articleView.html?idxno=16546",
    # "https://www.yonginmh.co.kr/news2/12399",
    # "https://mobile.hidoc.co.kr/healthstory/news/C0000312959",
    "https://www.hankyung.com/article/2023051720391"
    # "https://app.luminpdf.com/viewer/66dc361185c0bc2263fefd0d?credentials-id=ae1aa3a4-5fdb-4813-8737-2c6a5bf08040",
    # "https://app.luminpdf.com/viewer/66dc3637eb85a4c4ec74a3d3?credentials-id=f890ce69-82f3-4826-9a9e-3598b737632d",
    # "https://www.psychiatricnews.net/news/articleView.html?idxno=9111",
    # "https://blog.naver.com/hyeonse77/222273872237"
]

# 모든 URL의 HTML 데이터를 BeautifulSoup 객체로 변환
html_contents = [fetch_html(url) for url in urls]

# 메시지 히스토리 초기화
msg_history = [
    {"role": "system", "content": "당신은 친절하고 비약물적 우울증 치료 및 멘탈케어를 전문으로 하는 AI입니다. 사용자의 감정에 공감하며 따뜻한 대화를 나누고, 존중과 이해를 바탕으로 실질적인 조언을 제공합니다. 안전하고 지지적인 환경을 제공하며 긍정적인 방향으로 대화를 이끌어 주세요."},
    {"role": "user", "content": [
        # {"type": "text", "text": f"이 문서는 우리 서비스 내용에 관한 문서입니다. 모든 내용을 반드시 읽고 학습해 주시되, 생애주기와 관련된 내용을 반드시 숙지하여 사용자의 정보를 바탕으로 생애주기를 고려한 대화를 할 수 있게 해주세요. (추가 설명 : 사용자의 연령대에 따라 뚜렷한 AI의 답변 차이점이 보이는 말투, 가치관 등의 구성으로 대화해주세요.): {html_contents[0].text}"},
        # {"type": "text", "text": f"이 문서들은 비약물학적 우울증 치료에 관한 참고 문서입니다. : {html_contents[5].text}, {html_contents[6].text}"},
        # {"type": "text", "text": f"이 문서들은 우울증 관련 참고 문서입니다. : {', '.join([content.text for content in html_contents[1:5]])}"},
        # {"type": "text", "text": f"이 문서들은 위로를 해주는 방법 및 말투에 관한 참고 문서입니다. : {html_contents[7].text}, {html_contents[8].text}, {html_contents[9].text}"}
        {"type": "text", "text": f"이 문서들은 위로를 해주는 방법 및 말투에 관한 참고 문서입니다. : {html_contents[0].text}"}
    ]}
]

# OpenAI GPT-4 API 호출 함수
def generate_response(prompt):
    msg_history.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=msg_history,
            max_tokens=100,
            temperature=0.7
        )
        # 메시지 히스토리가 설정된 최대 개수를 초과하지 않도록 유지
        if len(msg_history) > msg_cnt:
            msg_history.pop(1)
        answer = response.choices[0].message['content'].strip()
        msg_history.append({"role": "assistant", "content": answer})
        return answer
    except openai.error.Timeout:
        return "응답 시간이 초과되었습니다. 다시 시도해 주세요."
    except openai.error.APIError as e:
        return f"API 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

# 기본 라우트
@app.route('/')
def index():
    return render_template('roharam_chatbot_service.html')

# 채팅 라우트
@app.route('/roharam_chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "메시지가 필요합니다."}), 400
    response = generate_response(user_input)
    return jsonify({"response": response})

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
