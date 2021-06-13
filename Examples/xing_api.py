import win32com.client
import pythoncom
import configparser
import os

"""
자주 사용하는 api 메서드에 대해서만 잘 작동하도록 구성하였음(실시간 시세조회, 전체 종목조회 등)
이 파일을 이용해서 다른 작업을 수행하기 전에 반드시 api 공식 문서를 확인하여야 한다
"""

# 기본 설정
class Config:
    """
    config.ini 파일 관련 클래스

    Attributes:
        config: xing_config.ini 파일을 파싱하기위한 ConfigParser 객체
    """
    def __init__(self):
        self.config = configparser.ConfigParser()
        if 'config.ini' not in os.listdir():
            self.config['COM'] = {}
            self.config['COM']['res_path'] = 'C:\\eBEST\\xingAPI\\Res'
            with open('xing_config.ini', 'w') as configfile:
                self.config.write(configfile)

    def res_path(self):
        """
        xing_config.ini 파일을 읽어 res 파일이 저장된 디렉토리 경로를 리턴한다

        returns:
            api 구동에 필요한 res파일이 저장된 디렉토리 경로, str 객체
        """
        self.config.read('xing_config.ini')
        return self.config['COM']['res_path']



# 기본적인 이벤트 처리 구조
class EventHandler:
    """
    이벤트핸들러 기본 구조
    모든 이베스트 api 이벤트 핸들러는 이 클래스를 상속받아야 한다.
    """
    def __init__(self):
        self.user_obj = None
        self.com_obj = None

    def connect(self, user_obj, com_obj):
        self.user_obj = user_obj
        self.com_obj = com_obj

    def OnLogin(self):
        pass

    def OnDisconnect(self):
        pass

    def OnReceiveData(self):
        pass

    def OnReceiveRealData(self):
        pass

# XASession 이벤트 처리
class XASessionEvents(EventHandler):
    """
    XASession 클래스의 이벤트 처리
    """
    # login 메서드의 이벤트 처리
    def OnLogin(self, code, msg):
        if code == "0000":
            self.user_obj.login_status = 1
            print(msg)
        else:
            print(code, msg)

    # 서버와의 연결이 끊어졌을 때 발생하는 이벤트
    def OnDisconnect(self):
        print("Session disconnected")


# XAQuery 이벤트 처리
class XAQueryEvents(EventHandler):
    """
    XAQuery 클래스의 이벤트 처리
    """
    # 요청한 조회 TR 에 대하여 서버로부터 데이터 수신시 발생하는 이벤트
    def OnReceiveData(self, tr_code):
        self.user_obj.receive_state = 1




# XAReal 이벤트 처리
class XARealEvents(EventHandler):
    """
    XAReal 클래스의 이벤트 처리
    """
    def OnReceiveRealData(self, tr_code):
        outblock_field = self.user_obj.outblock_field
        result = {}
        if isinstance(outblock_field, str):
            outblock_field = [outblock_field]
        for i in outblock_field:
            result[i] = self.com_obj.GetFieldData("OutBlock", i)
        print(result)




# 서버연결, 로그인 등
# 로그아웃은 증권사에서 지원하지 않음
class XASession:
    """
     로그인, 연결상태 등의 작업을 하는 클래스

     Attributes:
         login_status: 로그인 상태를 처리하기 위한 인스턴스 변수
    """

    def __init__(self):
        # 이베스트에서 제공하는 com 방식의 api 에 연결
        self.com_obj = win32com.client.Dispatch("XA_Session.XASession")
        self.event_handler = win32com.client.WithEvents(self.com_obj, XASessionEvents)
        self.event_handler.connect(self, self.com_obj)

        self.com_obj.ConnectServer("hts.ebestsec.co.kr", 20001)
        self.login_status = 0

    # 서버 연결상태 반환
    def is_connected(self):
        """
        서버 연결상태를 반환하는 메서드
        
        returns:
            Bool type
            연결되었으면 True, 연결되지않았으면 False 반환
        """
        result = self.com_obj.IsConnected()
        return result

    # 로그인
    def login(self, user_info, server_type = 0):
        """
        이베스트 api 에 로그인하는 메서드

        Args:
            user_info:
                로그인 정보가 있는 딕셔너리 객체
                {"user_id" : "이베스트증권 ID",
                "user_pw" : "이베스트증권 비밀번호",
                "cert_pw" : "공인인증서 비밀번호"}
            server_type:
                0 (실서버, 기본값)
                1 (모의서버)

        """
        user_id = user_info['user_id']
        if server_type == 0:
            self.com_obj.ConnectServer("hts.ebestsec.co.kr", 20001)
            user_pw = user_info['user_pw']
            cert_pw = user_info['cert_pw']
        else:
            self.com_obj.ConnectServer("demo.ebestsec.co.kr", 20001)
            user_pw = user_info["mock_pw"]
            cert_pw = ''
        self.com_obj.Login(user_id, user_pw, cert_pw, 0, False)
        while self.login_status == 0:
            pythoncom.PumpWaitingMessages()
    
    # 보유중인 계좌 개수 리턴
    def account_count(self):
        """
        보유중인 계좌 개수를 리턴함

        Returns:
            int type
            보유중인 계좌 개수를 정수로 반환
        """
        return self.com_obj.GetAccountListCount()

    # 계좌번호 목록 중에서 인덱스에 해당하는 계좌번호 리턴
    def account_num(self, index):
        """
        인덱스에 해당하는 계좌 번호를 리턴함

        Args:
            index: 계좌 인덱스(int)

        Returns:
            str type
            인덱스에 해당하는 계좌번호 리턴
        """
        return self.com_obj.GetAccountList(index)


# 조회 TR
# 동일 TR에 종목코드만 바꾸어 다수의 조회를 요청하려면 종목코드 수만큼 객체를 생성해야함
# (여러종목을 동시조회하는 자체 메서드를 제공하지 않음)
class XAQuery:
    """
    TR요청, 수신을 위한 클래스

    set_inblock -> request -> get_outblock
    의 순서로 진행하면 된다.

    !todo: 연속조회의 경우 이 클래스의 메서드를 사용하면 조회되지 않는다. 수정할것    

    Attributes:
        receive_state: 데이터 수신 상태를 확인하기 위한 인스턴스 변수
    """
    # 이벤트핸들러 지정: XAQueryEvents
    def __init__(self):
        self.com_obj = win32com.client.Dispatch("XA_DataSet.XAQuery")
        self.event_handler = win32com.client.WithEvents(self.com_obj, XAQueryEvents)
        self.event_handler.connect(self, self.com_obj)
        self.receive_state = 0

    # tr inblock 값 지정
    # attr 는 dict 객체
    def set_inblock(self, tr_code, attr):
        """
        TR 요청 전 요청 양식을 작성한다

        Args:
            tr_code: tr코드명(str)
            attr: {'inblock 필드명': value} 형식의 dict 객체

        !todo 이거 나중에 수정할 수도 있음
        """
        res_file = Config().res_path() + "\\" + tr_code + ".res"
        inblock = tr_code + "InBlock"
        self.com_obj.LoadFromResFile(res_file)
        for key, value in attr.items():
            self.com_obj.SetFieldData(inblock, key, 0, value)

    # tr outblock 값 취득하여 리턴
    # field_name은 리스트나 튜플 객체
    def get_outblock(self, outblock, field_name, index):
        result = {}
        if isinstance(field_name, str):
            field_name = [field_name]
        for i in field_name:
            result[i] = self.com_obj.GetFieldData(outblock, i, index)
        return result

    # tr 에 해당하는 outblock이 Occurs 일 경우 Occurs 갯수 반환
    def get_count(self, block_name):
        result = self.com_obj.GetBlockCount(block_name)
        return result

    # Inblock 의 개수 설정
    def set_count(self, block_name, count):
        self.com_obj.SetBlockCount(block_name, count)

    # 지정한 블록의 내용 삭제
    def clear_block(self, block_name):
        self.com_obj.ClearBlockData(block_name)

    # 블록의 전체 데이터 취득
    def get_all(self, block_name):
        result = self.com_obj.GetBlockData(block_name)
        return result

    # 조회 TR 요청
    def request(self, is_next = 0):
        result = self.com_obj.Request(is_next)
        self.receive_state = 0
        while self.receive_state == 0:
            pythoncom.PumpWaitingMessages()
        state = None
        if result >= 0:
            state = "TR received"
        else:
            state = result
        print(state)
        return state

# 실시간 TR
class XAReal:
    """
    실시간 데이터 수신을 위한 클래스

    set_inlock -> set_outblock -> start
    의 순서로 진행하면 된다.
    EventHandler 를 상속받은 새로운 클래스를 이벤트 핸들러로 지정하여 원하는 작업을 수행한다.
    !todo 이벤트핸들러 관련 패턴 개선?

    Attributes:
        receive_state: 데이터 수신 상태를 확인하기 위한 인스턴스 변수
        event_handler: 실시간 데이터 수신 이벤트를 처리할 이벤트 핸들러 지정(class)
    """
    # 이벤트핸들러 지정: XARealEvents
    def __init__(self, event_handler = XARealEvents):
        self.com_obj = win32com.client.Dispatch("XA_DataSet.XAReal.1")
        self.event_handler = win32com.client.WithEvents(self.com_obj, event_handler)
        self.event_handler.connect(self, self.com_obj)
        self.receive_state = 0
        self.outblock_field = None


    # inblock 세팅
    # (블록의 필드명, 데이터)
    def set_inblock(self, tr_code, shcode, field = "shcode"):
        res_file = Config().res_path() + "\\" + tr_code + ".res"
        self.com_obj.LoadFromResFile(res_file)
        if isinstance(shcode, str):
            shcode = [shcode]
        for i in shcode:
            self.com_obj.SetFieldData("InBlock", field, i)
            self.com_obj.AdviseRealData()

    # outblock 세팅
    # (필요한 데이터의 필드명)
    def set_outblock(self, field_name):
        self.outblock_field = field_name

    # outblock 의 전체 데이터 취득
    # def get_all(self):
    #     result = self.com_obj.GelBlockData("OutBlock")
    #     return result

    # 특정 종목의 실시간 데이터 수신 해제
    def del_realdata(self, shcode):
        if isinstance(shcode, str):
            shcode = [shcode]
        for i in shcode:
            self.com_obj.UnadviseRealDataWithKey(i)

    # 등록된 실시간 데이터 전부 해제
    def del_all(self):
        self.com_obj.UnadviseRealData()

    # 실시간 감시 시작
    def start(self):
        while self.receive_state == 0:
            pythoncom.PumpWaitingMessages()

def main():
    print("테스트 : 메인으로 실행")

if __name__ == "__main__":
    main()
    print(os.getcwd())