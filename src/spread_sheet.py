from information import TakeInformation
from google.auth import exceptions
from google.oauth2 import service_account
from collections import Counter
from wordcloud import WordCloud
from literal import json_path, start_row, cell_range, stop_word, FONT, sentiment_dict_path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import networkx as nx
import japanize_matplotlib
import gspread
import itertools
import re

class res_report(TakeInformation):
    def __init__(self, sheetname):
        '''
        TakeInformationクラスからの継承
        '''
        super().__init__()
        self.rmlist = self.take_sent_of_sheet(sheetname)
        self.text = ' '.join(self.rmlist)
        self.counter = Counter(self.rmlist)
        self.sentiment_dict = self.read_dict(sentiment_dict_path)
    
    def remove_stop_word_norm(self, text):
        '''
        正規表現でのstop word除去
        '''
        noun_list = []
        x_list, doc_1 = self.ja_ginza_token(text)
        pattern = re.compile(r"^[ぁ-ん]{1,2}$|^[ァ-ン]{1,2}$|^[0-9]{1}$|^[亜-熙]{1}$|^[〇一二三四五六七八九十百千万億兆京]{1}$") 
        for token in doc_1:
            if token.pos_ == "NOUN" or token.pos == "VERB":
                if not pattern.match(token.orth_):
                    noun_list.append(token.orth_)
        
        return noun_list             
    
    def read_dict(self, filepath):
        '''
        感情表現辞書読み込み
        '''
        with open(filepath,encoding='utf-8') as f:
            lines = f.readlines()    
            dic = { x.split(',')[0]:x.split(',')[1].strip('\n') for x in lines }
            
            return dic
    
    def draw_graph(self, count1, count2, count3):
        '''
        円グラフ描画
        '''
        labels = ['Positive','Neutral' ,'Negative']
        sizes = [count1, count2, count3]

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.pie(sizes, labels=labels, startangle=90, radius=1.12, autopct='%1.1f%%', pctdistance=0.75,
            wedgeprops=dict(width=0.7, edgecolor='w'), textprops=dict(color='w', fontsize=14))
        ax.set_title('EmotionRate', fontsize=20, pad=50)
        ax.legend(labels, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=14)

        # 中心に円を描画してドーナツ型にする
        centre_circle = plt.Circle((0, 0), 0.001, fc='white')
        ax.add_artist(centre_circle)

        plt.savefig('./image/emotionrate.png')
        
    def sentiment_analysis(self):
        '''
        感情分析グラフ出力
        '''
        p_count=0
        n_count=0
        ne_count=0
        err_count=0

        for token in self.text:
            res = self.sentiment_dict.get(token,'-')
            if res == 'POSITIVE':
                p_count += 1
            elif res == 'NEGATIVE':
                n_count += 1
            elif res == 'NEUTRAL':
                ne_count += 1
            else:
                err_count += 1

        self.draw_graph(p_count, n_count, ne_count)
    
    def wordcloud_result(self):
        '''
        wordcloud生成
        '''
        wordcloud = WordCloud(background_color='white', font_path=FONT, width=500, height=400).generate(self.text)    
        wordcloud.to_file("./image/wordcloud.png")
    
    def plt_counter(self):
        '''
        単語頻度集計
        '''
        # サブプロットを作成
        fig, ax = plt.subplots()

        # データをプロット
        words = [word for word, _ in self.counter.most_common(10)]
        counts = [num for _, num in self.counter.most_common(10)]
        ax.bar(words, counts)
        
        ax.grid(axis='y')
        ax.set_xlabel('単語')
        ax.set_ylabel('頻度')
        ax.set_title('単語頻度集計')

        # 画像を保存
        plt.savefig('./image/count_result.png')
    
    def plt_network_graph(self):
        '''
        共起グラフ生成
        '''
        pair_list = list(itertools.combinations([n for n in self.rmlist if len(self.rmlist) >= 2], 2))
        cnt_pairs = Counter(pair_list)

        tops = sorted(cnt_pairs.items(), key=lambda x: x[1], reverse=True)[:90]

        noun_1 = []
        noun_2 = []
        frequency = []

        for n, f in tops:
            noun_1.append(n[0])
            noun_2.append(n[1])
            frequency.append(f)

        df_G = pd.DataFrame({'前出名詞': noun_1, '後出名詞': noun_2, '出現頻度': frequency})

        weighted_edges = np.array(df_G)

        G = nx.Graph()
        G.add_weighted_edges_from(weighted_edges)


        plt.figure(figsize=(15, 10))

        nx.draw_networkx(
            G,
            node_shape="s",
            node_color="c",
            node_size=100,
            edge_color="gray",
            font_family="IPAexGothic",
        )

        plt.savefig('./image/netg.png')
    
    def take_sent_of_sheet(self, sheet_Name):
        '''
        スプレッドシート読み込み
        下処理
        '''
        n_list = []
        
        # 認証情報を読み込む
        scope = [self.spreadsheet, self.drive]
        credentials = service_account.Credentials.from_service_account_file(json_path, scopes=scope)
        client = gspread.authorize(credentials)
        
        # スプレッドシートにアクセス
        spreadsheet_id = self.sheetinfo.split('/')[-2]
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # 指定したシートを開く
        worksheet = spreadsheet.worksheet(sheet_Name)
        
        # 指定したセル範囲内の値を取得
        cell_values = worksheet.get(cell_range)[start_row - 1:] 
        for value in cell_values:
            if value:  
                text = ''.join(value)
                text = text.replace('\n','')
                text = text.replace('\r\n','')
                text = text.replace('\r','')
                n_list.append(text)
        
        text = ''.join(n_list)
        
        rm_list = self.remove_stop_word_norm(text)
        
        return rm_list