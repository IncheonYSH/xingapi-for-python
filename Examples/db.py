from sqlalchemy import create_engine
from sqlalchemy import text as sql_text
import json


#싱글톤 커낵션, 아니 이거 걍 이래놔도 되나? 시발?
class Connection():
    def __new__(cls):
        if not hasattr(cls, 'cursor'):
            
            def conn(user, password, host, port, db, charset):
                db_connection_str = f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'
                engine = create_engine(db_connection_str, encoding = charset, echo = True)
                return engine
            

            def quick_admin_login():
                
                '''
                admin_loging_info.json 구조
                {"user" : "username",
                 "password" : "0000",
                 "host" : "127.0.0.1",
                 "port" : "3306",
                 "db" : "dbname",
                 "charset" : "utf8"}
                '''
                
                file_path = "./admin_login_info.json"
                with open(file_path, "r") as json_file:
                    user = json.load(json_file)

                connection = conn(**user)
                print(connection)
    
                return connection
            
            cls.cursor = quick_admin_login()
            
        return cls.cursor

class KRXNewsData:
    """
    뉴스정보를 저장할 테이블
    """
    def __init__(self):
        self.connection = Connection()

    def create_table(self):
        """
        테이블 생성
        """
        sql = sql_text("""
                       CREATE TABLE krx_news_data(
                           `index` int AUTO_INCREMENT PRIMARY KEY,
                           `datetime` datetime,
                           `id` varchar(3),
                           `title` text,
                           `code` varchar(250)                           
                           );
                       """)
        self.connection.execute(sql)



    def insert(self, context):
        """
        데이터를 krx_news_data 에 삽입
        """
        sql = sql_text("""
                       INSERT INTO krx_news_data 
                       (`datetime`, `id`, `title`, `code`)
                       VALUES(:datetime, :id, :title, :code)
                       """)

        self.connection.execute(sql, **context)
