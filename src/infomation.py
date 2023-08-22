import requests
import configparser
import urllib.request
import ginza
import spacy
from bs4 import BeautifulSoup
from xml.etree import ElementTree

config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

class TakeInformation:
    def __init__(self):
        '''
        コンストラクタ定義
        '''
        self.quake_url = config_ini['URLS']['quake']
        self.weather_url =  config_ini['URLS']['weather'] 
        self.attention_url = config_ini['URLS']['attention'] 
        self.client_id = config_ini['TOKENS']['TWID']
        self.tokens = config_ini['TOKENS']['TTOKEN']
        self.client_secret = config_ini['TOKENS']['TSC']
        
        # spreadsheet
        self.spreadsheet = config_ini['URLS']['spreadsheets']
        self.drive = config_ini['URLS']['googledrive']
        self.sheetinfo = config_ini['URLS']['spreadsheet_url']
    
    def take_earthquake_info(self):
        '''
        最新の地震情報を1件取得する
        '''
        e_result_list = []
        m_scale_dict = {
            10:'震度1',
            20:'震度2',
            30:'震度3',
            40:'震度4',
            45:'震度5弱',
            50:'震度5強',
            55:'震度6弱',
            60:'震度6強',
            70:'震度7'
        }
        quake_json = requests.get(self.quake_url).json()
        quake_info = quake_json[0]["earthquake"]
        quake_info_plus = quake_json[0]["earthquake"]["hypocenter"]
        
        time = quake_info["time"]
        m_scale = quake_info["maxScale"]
        point = quake_info_plus["name"]
        depth = quake_info_plus["depth"]
        scale = quake_info_plus["magnitude"]
        point1 = quake_info_plus["latitude"]
        point2 = quake_info_plus["longitude"]
        
        m_scale_p = m_scale_dict[m_scale]
        e_result_list = [time, point, depth, scale, point1, point2, m_scale_p]
        
        return e_result_list
    
    def take_weather_information(self):
        '''
        東京・大阪の当日の天気予報を取得しコメントを返す
        '''
        t_w_list = self.weather_json("130010")
        o_w_list = self.weather_json("270000")
        
        return t_w_list, o_w_list
        
    def weather_json(self, location_code):
        '''
    　　URL+地域コードを元に天気情報をjsonから取得する
        '''
        w_result_list = []
        url = self.weather_url + location_code
        weather_json = requests.get(url).json() 
        date = weather_json["forecasts"][0]["date"]
        locate = weather_json["location"]["prefecture"]
        weather = weather_json["forecasts"][0]["detail"]["weather"]
        telop = weather_json["forecasts"][0]['telop']
        
        if "晴れ" in telop:
            telop = "晴"
        elif "曇り" in telop:
            telop = "曇"
        elif "一時" in telop:
            telop = "一"
        
        wakati_list, doc = self.ja_ginza_token(telop)
        emoji_str = self.convert_weather_string(wakati_list)
        
        w_result_list = [date, locate, weather, emoji_str]
        
        return w_result_list
    
    def ja_ginza_token(self, word:str) -> list:
        '''
        GiNZAでの分かち書き
        '''
        nlp = spacy.load('ja_ginza')
        ginza.set_split_mode(nlp, 'C')
        doc = nlp(word)
        tokens = [token.text for token in doc]
        return tokens, doc
    
    def convert_weather_string(self, weather_list:list) -> str:
        '''
        天気予報文を絵文字に変換する
        '''
        convert_list = []
        weather_emojis = {
            "晴": "☀️",
            "曇": "☁️",
            "雨": "🌧️",
            "雪": "❄️",
            "のち":"->",
            "時々":"/",
            "一":"/"
        }

        for w_str in weather_list:
            conv = weather_emojis[w_str]
            convert_list.append(conv)

        result = ''.join([w for w in convert_list])
        return result
    
    def get_access_token(self):
        '''
        Twitchアクセストーク取得
        '''
        token_url = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(token_url, data=payload)

        if response.status_code == 200:
            data = response.json()
            access_token = data["access_token"]
            return access_token
        else:
            return None
    
    def check_stream_status(self, streamer_name):
        '''
        Twitchの配信情報を取得して返す
        '''
        access_token = self.get_access_token()
        
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {access_token}',
        }

        url = f'https://api.twitch.tv/helix/streams?user_login={streamer_name}'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data['data']:
                data_list = []
                user_id = data['data'][0]['user_login']
                name = data['data'][0]['user_name']
                title = data['data'][0]['title']
                data_list.append(user_id)
                data_list.append(name)
                data_list.append(title)
                return True, data_list # 配信中
            else:
                data_list = None
                return False, data_list  # 配信していない
        else:
            print(response.text)
            data_list = None
            
        return None, data_list# エラーが発生
    
    def take_base_attention_info(self):
        '''
        注意報情報更新取得
        '''
        soup = self.take_url_info(self.attention_url)
        res_list = []
        entries = soup.find_all("entry")
        latest_entry = None
        latest_updated = None

        for entry in entries:
            title = entry.find("title").text
            if title == "気象警報・注意報（Ｈ２７）":
                updated = entry.find("updated").text
                if latest_entry is None or updated > latest_updated:
                    latest_entry = entry
                    latest_updated = updated

        if latest_entry is not None:
            id_updated = latest_entry.find("updated").text
            id_url = latest_entry.find("id").text
        else:
            res_list = None
        
        res_list = [id_updated, id_url]
        
        return res_list
    
    def url_to_take_attention(self, url):
        '''
        詳細情報取得
        '''
        attention_list = []
        code_list = []
        soup = self.take_url_info(url)
        
        information = soup.find("Information", {"type": "気象警報・注意報（府県予報区等）"})
        if information is not None:
            information2 = soup.find("Headline")
            head = information2.find_all("Text")
            text = head[0].text
            items = information.find_all("Item")
            for item in items:
                names = item.find_all("Name")
                codes = item.find_all("Code")
                for name in names:
                    attention_list.append(name.text)
                for code in codes:
                    code_list.append(code.text)
        else:
            attention_list = None
            code_list = None
            text = None
        
        return attention_list, code_list, text
        
    def take_url_info(self, url):
        '''
        処理共通化
        '''
        res = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(res, "xml")
        
        return soup