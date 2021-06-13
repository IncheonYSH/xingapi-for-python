from xing_api import XASession
from xing_api import XAReal
from xing_api import EventHandler
import json
from db import KRXNewsData
import multiprocessing
import datetime



"""
실시간으로 수신되는 뉴스데이터를 데이터베이스에 저장할때 아래와 같이 작동시킵니다.
데이터베이스 부분은 필요에 맞게 구성합니다.
"""

# 로그인
class Login:
    """
    이베스트증권 api 서버 로그인을 위한 클래스

    Attributes:
        file_path: 로그인 정보가 있는 json 파일의 경로
    """
    def __init__(self):
        self.file_path = "./xing_user2.json"

    def login(self):
        """
        실서버 로그인

        {"user_id" : "이베스트증권 ID",
        "user_pw" : "이베스트증권 비밀번호",
        "mock_pw" : "모의투자 비밀번호",
        "cert_pw" : "공인인증서 비밀번호"}
        형식의 ./xing_user2.json 파일을 읽어 api 로그인
        """
        with open(self.file_path, "r") as json_file:
            user = json.load(json_file)
        session = XASession()
        session.login(user)

    def login_mock(self):
        """
        모의투자서버 로그인

        {"user_id" : "이베스트증권 ID",
        "user_pw" : "이베스트증권 비밀번호",
        "mock_pw" : "모의투자 비밀번호",
        "cert_pw" : "공인인증서 비밀번호"}
        형식의 ./xing_user2.json 파일을 읽어 api 서버로 로그인
        """
        with open(self.file_path, "r") as json_file:
            user = json.load(json_file)
        session = XASession()
        session.login(user, server_type=1)


# 뉴스 전용 실시간 이벤트 핸들러
class NewsEvent(EventHandler):
    """
    xing_api.XAReal 객체에 의해 ReceiveRealData 이벤트 수신 시 작동
    실시간 뉴스 수신 전용 이벤트 핸들러
    krx_news_data 테이블에 저장
    """
    def OnReceiveRealData(self, tr_code):
        outblock_field = self.user_obj.outblock_field
        result = {}
        date_time = self.com_obj.GetFieldData("OutBlock", 'date')
        date_time = date_time + self.com_obj.GetFieldData("OutBlock", 'time')
        date_time = datetime.datetime.strptime(date_time, '%Y%m%d%H%M%S')
        result["datetime"] = str(date_time)
        if isinstance(outblock_field, str):
            outblock_field = [outblock_field]
        for i in outblock_field:
            result[i] = self.com_obj.GetFieldData("OutBlock", i)
        KRXNewsData().insert(result)


class News(multiprocessing.Process):
    def run(self):
        """
        실시간 뉴스데이터 수신
        """
        Login().login()
        news = XAReal(NewsEvent)
        news.set_inblock("NWS", "NWS001", field = "nwcode")
        news.set_outblock(["id", "title", "code"])
        news.start()

# 테스트용
if __name__ == "__main__":
    process1 = News()
    process1.start()
