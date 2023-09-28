import configparser
import discord
import traceback
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands, tasks
from staticmap import StaticMap
from geopy.geocoders import Nominatim
from res_gpt import generate_reply
from spred_sheet import res_report
from information import TakeInformation
from langchain.llms import OpenAI
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from literal import (channel_id, diary_id, image_path, image_path_2, pin_path, pin_path_2, kobeline_URL, chiyoda_URL, 
                     jyoubann_URL, COPYRIGHT_TEXT, FONT, FONT_SIZE, l_model_name, l_template, x_template, s_names, image_data)

config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = config_ini['TOKENS']['TOKEN']
client_id = config_ini['TOKENS']['TWID']
tokens = config_ini['TOKENS']['TTOKEN']
openai_key = config_ini['TOKENS']['OPENAIKEY']

info = TakeInformation()

def save_quake_time(txt_file_path, time):
    '''
    ファイル情報書き込み
    '''
    with open(txt_file_path, "w") as f:
        f.write(time)

def load_quake_time(txt_file_path):
    '''
    ファイル情報読み込み
    '''
    try:
        with open(txt_file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def image_map(point1, point2, ivent_flg):
    '''
    経度, 緯度情報を元に地図画像を生成する。
    '''
    try:
        if ivent_flg == 'e':
            p_path = pin_path
            i_path = image_path
            zoom_size = 9
        elif ivent_flg == 'm':
            p_path = pin_path_2
            i_path = image_path_2
            zoom_size = 16
            
        map = StaticMap(800, 600)
        pin_size = (50,50)
        image = map.render(zoom=zoom_size, center=[point2,  point1]).convert('RGBA')
        pin_image = Image.open(p_path).convert('RGBA').resize(pin_size)
        
        # 背景と同サイズの透明な画像を生成
        img_clear = Image.new("RGBA", image.size, (255, 255, 255, 0))
        
        # 透明画像の上にペースト
        img_clear.paste(pin_image, (800 // 2 - pin_size[0], 600 // 2 - pin_size[1]))
        
        # 重ね合わせる
        image = Image.alpha_composite(image, img_clear)
        
        # # Copyright挿入
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT, FONT_SIZE)
        draw.multiline_text((800 - 10, 600 - 10), COPYRIGHT_TEXT, fill=(0, 0, 0), font=font, anchor='rs')
        
        # save
        image.save(i_path)
        return True
    except Exception as e:
        print(e)
        return False

def calc_center(location):
    '''
    位置情報から経度と緯度を取得
    '''
    geolocator = Nominatim(user_agent="user-id")
    locate = geolocator.geocode(location)

    return locate.latitude, locate.longitude

def embed_locatemap(msg):
    '''
    地図情報取得
    '''
    point1, point2 = calc_center(msg)
    ivent_flg = 'm'
    result = image_map(point1, point2, ivent_flg)
    embed = discord.Embed(title=f"{msg}の位置情報ですよ~", color=0x1f8b4c)
    if result == True:
        fname="upload.png "
        file = discord.File(fp=image_path_2,filename=fname,spoiler=False) 
        embed.set_image(url=f"attachment://{fname}")
    else:
        embed.add_field(name="ごめんなさい😢 画像が取得できませんでした。",  value="",inline=False)
        file = None
    
    return embed, file
        
def embed_earthquake(e_result_list):
    '''
    地震情報埋め込み作成
    '''
    ivent_flg = 'e'
    name_list = ['発生時刻', '発生場所', '深さ', 'マグニチュード', '最大震度']
    embed_dict = {}
    result = image_map(e_result_list[4], e_result_list[5], ivent_flg)
    
    # 地震情報辞書作成
    del e_result_list[4:6]
    for i in range(len(name_list)):
        embed_dict[name_list[i]] = e_result_list[i]
    
    embed = discord.Embed(title="つくよみちゃんが最新の地震情報をお届けします!", color=0x992d22)
    
    # 辞書を元にembedを作成
    for i in embed_dict.keys():    
        embed.add_field(name=i, value=embed_dict[i], inline=True)

    # 画像ファイルの送信処理
    if result == True:
        fname="upload.png "
        file = discord.File(fp=image_path,filename=fname,spoiler=False) 
        embed.set_image(url=f"attachment://{fname}")
    else:
        embed.add_field(name="ごめんなさい😢 画像が取得できませんでした。", value="", inline=False)
        file = None
        
    return embed, file

def embed_weather():
    '''
    天気情報埋め込み作成
    '''
    t_res_list, o_res_list = info.take_weather_information()
    embed = discord.Embed(title=f"つくよみちゃんが今日({t_res_list[0]})のお天気をお知らせします!", color=0xff9300)
    embed.add_field(name=f"{t_res_list[1]}のお天気", value=f"天気： {t_res_list[3]}\n詳細：{t_res_list[2]}", inline=False)
    embed.add_field(name=f"{o_res_list[1]}のお天気", value=f"天気： {o_res_list[3]}\n詳細：{o_res_list[2]}", inline=False)
    
    return embed

def embed_dialy_report(sheetname:str, image_info:dict, count:int):
    '''
    情報取得
    '''

    # Embedオブジェクトの生成
    embed = discord.Embed(title=f"{sheetname}のレポートその{count}", description=f"{image_info['name']}のレポート", color=discord.Color.blue())

    # 画像のファイルを添付
    file = discord.File(fp=image_info["path"], filename=image_info["filename"], spoiler=False)
    embed.set_image(url=f"attachment://{image_info['filename']}")     
    
    return embed, file
    
def all_information_embed():
    '''
    チュートリアルメニュー表示
    '''
    embed = discord.Embed(title="つくよみちゃんbot【ver α0.0.5】マニュアル", 
                          description="基本的に会話AIによるチャットの他、メッセージ先頭に「!」を付ける事により各種情報を取得できます。", color=0x2ecc71)
    embed.add_field(name="!メニュー", value="本メニューを表示します。", inline=True)
    embed.add_field(name="!地震", value="つくよみちゃんが最新の地震情報を教えてくれます。また本情報はAPI更新毎に自動的に呟いてくれます。", inline=True)
    embed.add_field(name="!天気", value="つくよみちゃんが今日の天気を教えてくれます", inline=True)
    embed.add_field(name="地図情報取得", value="「○○の場所」と呟くことで○○の位置情報を取得してくれます。", inline=True)
    embed.add_field(name="その他", value="「○○動いてる?」で対応する路線の情報をお知らせします。またTwitchストリーム配信開始も告知してくれます。", inline=False)
    
    return embed  

def delay_line(flg):
    '''
    路線URL埋め込み
    '''
    if flg == 'JR神戸線':
        response = f'JR神戸線の運行状況ですよ~!\n{kobeline_URL}'
    elif flg == '千代田線':
        response = f'東京メトロ 千代田線の運行状況ですよ~!\n{chiyoda_URL}'
    elif flg == 'JR常磐線':
        response = f'JR常磐線の運行状況ですよ~!\n{jyoubann_URL}'
    else:
        response = 'ごめんなさい! 路線情報を取得できませんでした😢'
    return response

def ChatGPT(string:str, template:str)->str:
    '''
    Open AI API利用チャットレスポンス
    '''
    gpt = OpenAI(
    model_name=l_model_name,
    max_tokens=1024,
    temperature=0.95,
    frequency_penalty=0.02,
    openai_api_key=openai_key
    )
    
    prompt = PromptTemplate(input_variables = ["command"], template=template)
    memory = ConversationBufferMemory(memory_key="chat_history")
    chain = LLMChain(llm=gpt, prompt=prompt, verbose=True, memory=memory)
    result = chain.run(string)
    
    return result

@tasks.loop(minutes=2)
async def eqevent():
    '''
    APIに更新が発生したら地震情報告知イベントを作成する
    '''
    await bot.wait_until_ready()  
    channel_sent = bot.get_channel(channel_id) 
    
    # チャンネルが見つからなければ処理終了
    if channel_sent is None:
        return 
    
    e_file_path =  './txtfile/time.txt'
    before_time = load_quake_time(e_file_path)
    e_res_list = info.take_earthquake_info()
    
    # 前回更新時刻と同じであれば以降の処理は行なわない
    if e_res_list[0] == before_time:
        return 
    
    save_quake_time(e_file_path,e_res_list[0])
    embed, file = embed_earthquake(e_res_list)
    
    if file != None:
        await channel_sent.send(file=file, embed=embed)
    else:
        await channel_sent.send(embed=embed)

@tasks.loop(minutes=2)
async def liveevent():
    '''
    twitch配信アナウンサ
    '''
    await bot.wait_until_ready()  
    channel_sent = bot.get_channel(channel_id)  
    for s_name in s_names:
        t_file_path = f"./txtfile/{s_name}.txt"
        
        if channel_sent is None:
            return
        
        bool_num, live_list = info.check_stream_status(s_name)
        # print(f"{s_name}:{bool_num}, {live_list}")
        if bool_num == False or bool_num == None:
            continue
        
        if live_list[2] == load_quake_time(t_file_path):
            continue
        
        save_quake_time(t_file_path,live_list[2])
        t_urls = f"https://www.twitch.tv/{live_list[0]}"
        embed = discord.Embed(title=f"Twitch配信開始のお知らせ!", color=0x71368a)
        embed.add_field(name=f"{live_list[1]}さんが配信「{live_list[2]}」を開始しました!", value=f"{t_urls}", inline=False)
        await channel_sent.send(embed=embed)

@tasks.loop(minutes=1)
async def attentionevent():
    '''
    注意報情報
    '''
    await bot.wait_until_ready()
    channel_sent = bot.get_channel(channel_id)
    a_file_path = './txtfile/attention_time.txt'
    t_res_list, o_res_list = info.take_weather_information()
    
    if channel_sent is None:
        return
    
    before_time = load_quake_time(a_file_path)
    res_list = info.take_base_attention_info()
    if res_list[0] == before_time:
        return
    
    save_quake_time(a_file_path, res_list[0])
    info_attention, info_code, text = info.url_to_take_attention(res_list[1])
    if info_attention is None:
        return
    
    if info_code[-1] in ['130000', '270000']:
        a_list = [at_info for at_info in info_attention[:-1] if '注意報' in at_info]
        w_a_list = [at_info for at_info in info_attention[:-1] if '警報' in at_info]
        
        a_str = '\n'.join(a_list) if a_list else 'なし'
        w_a_str = '\n'.join(w_a_list) if w_a_list else 'なし'
        
        if info_code[-1] == "130000":
            res_list = t_res_list
        elif info_code[-1] == "270000":
            res_list = o_res_list
        
        embed = discord.Embed(title=f"つくよみちゃんが本日({res_list[0]})の天気及び各地の警報・注意報情報をお知らせします!", color=0xff9300)
        embed.add_field(name="地域", value=info_attention[-1], inline=False)
        embed.add_field(name="天気", value=res_list[3], inline=False)
        embed.add_field(name="情報", value=text, inline=False)
        embed.add_field(name="注意報", value=a_str, inline=True)
        embed.add_field(name="警報", value=w_a_str, inline=True)
        
        await channel_sent.send(embed=embed)
    
@bot.event
async def on_ready(): 
    # コマンドライン表示
    print(f"Bot is ready. Logged in as {bot.user}") 
    
    # bot起動時のチャンネル投稿
    await bot.wait_until_ready()  
    channel_sent = bot.get_channel(channel_id) 
    #embed = all_information_embed()
    res = "つくよみちゃんbotが稼働しました!"
    await channel_sent.send(res)
    
    # 定期情報発信イベント
    events = [eqevent, liveevent, attentionevent]

    for event in events:
        if not event.is_running():
            event.start()
    
@bot.event
async def on_message(message):
    '''
    投稿メッセージによるイベント
    '''
    
    # 自分のメッセージには反応しない
    if message.author == bot.user:
        return
    
    try: 
        if message.content.startswith('!地震'):
            e_res_list = info.take_earthquake_info()
            embed, file = embed_earthquake(e_res_list)
            if file != None:
                await message.channel.send(file=file, embed=embed)
            else:
                await message.channel.send(embed=embed)
        elif message.content.startswith('!天気'):
            embed = embed_weather()
            await message.channel.send(embed=embed)
        elif message.content.startswith('!メニュー'):
            embed = all_information_embed()
            await message.channel.send(embed=embed)
        elif '相談内容:' in message.content:
            msg = message.content.replace('相談内容:','')
            res = ChatGPT(msg, l_template)
            # 専門外の質問だった場合
            if '回答できません' in res:
                res = "入力された内容は悩み相談の内容と異なるために回答できません。\nもう一度内容を確認の上入力してください。"
            response = f'認知行動療法GPTさんからのメッセージですよ~\n```{res}```'
            await message.channel.send(response)
        elif '動いてる?' in message.content:
            msg = message.content.replace('動いてる?','')
            response = delay_line(str(msg))
            await message.channel.send(response) 
        elif 'の場所' in message.content:
            msg = message.content.replace('の場所','')
            embed, file = embed_locatemap(msg)
            if file != None:
                await message.channel.send(file=file, embed=embed)
            else:
                await message.channel.send(embed=embed)   
        elif '日記レポート' in message.content: 
            #日記チャネル以外では使用出来なくする 
            if message.channel.id != diary_id:
                await message.channel.send('本チャネルでは対応していないコマンドです')
                return 
            
            #日記チャネルのみ
            msg = message.content.replace('日記レポート','')
            sheetname = f"2023{msg}"
            res_rep = res_report(sheetname)
            top10_words = res_rep.plt_counter()
            res_rep.wordcloud_result()
            res_rep.plt_network_graph()
            res_rep.sentiment_analysis()
            res = ChatGPT(top10_words,x_template)
            counter = 1  
            response = f"```{res}```"
                     
            # 回数分ループ
            for image_info in image_data:
                    embed, file = embed_dialy_report(sheetname, image_info, counter)
                    await message.channel.send(file=file, embed=embed)    
                    counter += 1
            embed = discord.Embed(title=f"{sheetname}総評", color=discord.Color.blue())
            embed.add_field(name="当月の傾向など", value=response, inline=False)
            await message.channel.send(embed=embed)
        else:        
            response = generate_reply(message.content)
            await message.channel.send(response)       
    except Exception as e:
        traceback_info = traceback.format_exc()
        error_message = f"エラー発生中です!： {str(e)}\n{traceback_info}"
        await message.channel.send(error_message)
        
if __name__ == "__main__":
    bot.run(TOKEN)