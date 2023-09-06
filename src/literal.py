# discord channel ID
channel_id = 'ID'

# img Path
image_path = './image/komoot.png'
image_path_2 = './image/map.png'
pin_path = './image/nc269495.png'
pin_path_2 = './image/pin.png'
txt_file_path = './txtfile/time.txt'
image_data = [
    {"path": "./image/count_result.png", "filename": "count_result.png", "name":"単語集計"},
    {"path": "./image/wordcloud.png", "filename": "wordcloud.png", "name":"単語頻度"},
    {"path": "./image/netg.png", "filename": "netg.png", "name":"共起グラフ"},
    {"path": "./image/emotionrate.png", "filename": "emotionrate.png", "name":"ネガポジレート"},
]

# info delay line
kobeline_URL = 'https://transit.yahoo.co.jp/diainfo/273/0'
chiyoda_URL = 'https://transit.yahoo.co.jp/diainfo/136/0'
jyoubann_URL = 'https://transit.yahoo.co.jp/diainfo/59/59'

# open map
COPYRIGHT_TEXT = '©OpenStreetMap(openstreetmap.org/copyright) contributors'
FONT = './Font/ipaexm.ttf' 
FONT_SIZE = 20

# ChatGPT 
l_model_name="gpt-3.5-turbo"
l_template = """
下記の状況に対して、認知行動療法の観点からアドバイスしてください。
また、チェックすべき認知のゆがみを「考え方の見直しポイント」としてアドバイスの後に列挙して、セルフチェックできるようにしてください。
口調はベテランのカウンセラー調としてください。
また、なるべく学術的な用語は使用せず、平易な用語や文体で話してください。
`内容文:`以降の内容が明らかに専門外の内容だった場合(例：GPGPUってなに?, PythonでHello Worldを出力する といった心理学的に答えられない専門外の質問)には「お悩み, 相談以外の話題には回答できません」と返答してください。
内容文：{command}
"""
x_template = """
日記を分析した結果、下記の単語が多く含まれていました。
下記結果は今の自分の頭の中を占めていることとなっています。
例えば`仕事`が結果に含まれていた場合、仕事に関することを考える機会が当月では多かったということになります。
まず心理学的観点から思考の傾向の総評を文章として記述し、そのあとで改善点を「今後の改善案」として1行程度で箇条書きで5つ程示してください。
また、なるべく学術的な用語は使用せず、平易な用語や文体で記載してください。

頻出語top10:{command}
"""

# Twitch Strimer ID
s_names = ['ID']

# spreadsheet
sheet_name = "20230"  
start_row = 5  
cell_range = "C:C"
json_path = "./google_spread_sheet/copper-seeker-396204-8a2ea5b4e9e0.json"
sentiment_dict_path = "./google_spread_sheet/pn_formatted.csv"

# sentiment analysis
stop_word = ['こと', 'よう', 'そう', 'これ', 'それ', 'あれ', 'どれ', 'の', 'ん', 'ぼく', 
        'もの', 'たち','一','どこ', 'わけ', 'つもり', 'そもそも', 'ところ','ため','今','一切','自分','奴','他','身','気','年','度','1']

