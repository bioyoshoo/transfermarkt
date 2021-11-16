# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 01:34:41 2021

@author: yoshi
"""


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import numpy as np
import pandas as pd
from transfermarkt import TransferMarkt

options = Options()
options.page_load_strategy = 'none'
driver = webdriver.Chrome("C:/Users/yoshi/webdriver/chromedriver_win32/chromedriver.exe", options=options)

headers = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84"}

# transfermarktのホームページ開いて動的に操作したい場合(各リーグの詳細テーブルのURLを取得したい時など)はdriver引数の設定が必要
# 詳細テーブルのURLからscraypingしたい時はrequestsに渡すheaders引数を設定する必要がある
tf = TransferMarkt(driver, headers)

output_df = tf.make_empty_df()
error_df = pd.DataFrame(np.zeros((0, 4)), columns=["Country", "Competition", "Error", "Message"])

# ここのリストに取得したい国名を入れる
# tf.search_all_country()で全世界の国名入ったリストが得られる
# ここではGermanyの全てのリーグのデータを取得する
for country in ["Germany"]:
    # その国の全てのcompetiotonを検索
    for i, comp in enumerate(tf.search_competition(country)):
        
        try:
            if i == 0:
                detail_url = tf.guide_from_country_and_league_to_leagueurl(country, comp)
            else:
                detail_url = tf.guide_from_country_and_league_to_leagueurl(country, comp, same_country=True)
        except Exception as e:
            print("URL-ERROR:", country, ":", comp)
            print("MESSAGE: ", e)
            error_info = np.array([country, comp, "URL-ERROR", e]).reshape(1, -1)
            error_info_df = pd.DataFrame(error_info, columns=error_df.columns)
            error_df = pd.concat([error_df, error_info_df])
            continue

        if detail_url:
            try:
                # detail_urlがNoneではなかったらスクレイピングを行う
                df = tf.scrayping_this_league(detail_url)
            except Exception as e:
                print("SCRAYPING-ERROR:", country, ":", comp)
                print("MESSAGE: ", e)
                error_info = np.array([country, comp, "SCRAYPING-ERROR", e]).reshape(1, -1)
                error_info_df = pd.DataFrame(error_info, columns=error_df.columns)
                error_df = pd.concat([error_df, error_info_df])
            else:
                output_df = pd.concat([output_df, df])
                print("OK:", country, ":", comp)
            
# ここのファイル名もその都度変える!!!! 上書きされないように!!!
output_df.to_csv("./output_dataframe/Germany.csv", index=False)
output_df.to_csv("./output_dataframe/Germany_Error.csv", index=False)

driver.close()
driver.quit()

print("done!")
