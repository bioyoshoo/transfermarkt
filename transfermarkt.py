
class TransferMarkt():
    
    def __init__(self, driver, headers=None):
        from time import sleep

        self.transfer_url = "https://www.transfermarkt.com"
        # webdriverを設定する
        self.driver = driver
        # このdriverがfind_element系で要素を探した時の暗黙の待ち時間20秒までとする
        self.driver.implicitly_wait(20)
        # インスタンス下した際にトップページに入っておく
        self.driver.get(self.transfer_url)
        # window最大化しておく
        self.driver.maximize_window()
        # 2秒待機
        sleep(2)
        # headers要素があればheaderも入れる
        # scrayping_this_page, scrayping_this_leagueで必要 requestsに渡す
        if headers:
            self.headers = headers

    # player_info_tagには、ある選手の全ての情報を含む（テーブルで1行にあたる)タグを指定
    # 移籍情報のテーブルから情報をとってくるための関数を定義
    def scrayping_this_player(self, player_info_tag):
        import requests
        import re

        # player_info_tagを各行の内容に分割する
        player_info_lis = player_info_tag.find_all("td", recursive=False)
        
        # 名前、ポジション、画像が格納されている列
        name_pos_col = player_info_lis[1]
        name = name_pos_col.a.string
        position = name_pos_col.find_all("td")[-1].string
        img = name_pos_col.img["data-src"]

        # 年齢が格納されている列
        age_col = player_info_lis[2]
        age = int(age_col.string)

        # 移籍した年が格納されている列
        season_col = player_info_lis[3]
        season = season_col.string

        # 国籍が格納されている列
        nat_col = player_info_lis[4]
        #二重国籍の選手を考慮
        nat_lis = []
        for img_tag in nat_col.find_all("img"):
            nat_lis.append(img_tag["title"])
        nat = "/".join(nat_lis)

        # 前所属チームが格納されている列
        left_col = player_info_lis[5]
        left_team = left_col.find("td", class_="hauptlink").a.string
        left_nat = left_col.find("img", class_="flaggenrahmen")["title"]
        left_league_tag = left_col.find_all("td")[-1]
        
        # いくつかリーグの国名がaタグで囲われていない
        if left_league_tag.find("a"):
            left_league = left_league_tag.a.string
        else:
            m = re.search("[A-Z][a-z]*", left_league_tag.text)
            left_league = m.group()

        # 加入チームが格納されている列
        joined_col = player_info_lis[6]
        joined_team = joined_col.find("td", class_="hauptlink").a.string
        joined_nat = joined_col.find("img", class_="flaggenrahmen")["title"]
        joined_league_tag = joined_col.find_all("td")[-1]
        
        if joined_league_tag.find("a"):
            joined_league = joined_league_tag.a.string
        else:
            m = re.search("[A-Z][a-z]*", joined_league_tag.text)
            joined_league = m.group()

        # 移籍金が格納されている列
        fee_col = player_info_lis[7]
        # Loanか完全移籍かで表示のされ方が異なる
        if fee_col.find("i"):
            loan_or_not = True
            fee = fee_col.find("i").string
        else:
            loan_or_not = False
            fee = fee_col.string
        
        return name, position, age, season, nat, left_team, left_league, left_nat, joined_team, joined_league, joined_nat, fee, loan_or_not, img

    # 選手情報を入れる空の配列をつくる関数
    @staticmethod
    def make_empty_df():
        import numpy as np
        import pandas as pd
        # データを格納するデータフレームを作成
        col_names = ["Name", "Position", "Age", "Season", "Player_nat", "Left_team", "Left_league", "Left_team_nat", \
                    "Joined_team", "Joined_league", "Joined_nat", "Fee", "Loan_or_not", "Face_img"]
        output_df = pd.DataFrame(np.zeros((0, 14)), columns=col_names)
        
        return output_df

    # 移籍情報のデーブルがあるページのURLを引数にとる
    # 返り値はそのテーブルの選手情報のデータフレームと次のページがあるか
    def scrayping_this_page(self, page_url, headers):
        import requests
        from bs4 import BeautifulSoup
        import numpy as np
        import pandas as pd

        # user-agentを書き換えてrequetsでURLを取得
        response = requests.get(page_url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # データを格納するデータフレームを作成
        output_df = self.make_empty_df()
        col_names = output_df.columns
        
        # リーグによってはこのテーブルが全く存在しないものもある
        try:
            # 選手の情報が入っているテーブル
            table = soup.select("#yw1 > table")[0]
        except:
            next_page_list = []
        else:
            # テーブルの中の選手情報
            table_body = table.find("tbody")
            # このリストの要素が、一人一人の選手のデータを保持しているタグ
            players_tr_tags = table_body.find_all("tr", recursive=False)
            
            # 選手一人一人に対してscrayping_this_playerを適用する
            for player_info_tag in players_tr_tags:
                
                output = self.scrayping_this_player(player_info_tag)
                data = np.array(output).reshape(1, -1)
                player_df = pd.DataFrame(data, columns=col_names)
                output_df = pd.concat([output_df, player_df])
            
            # 次のページへ移るボタンがあるかどうか
            next_page_list = soup.select("#yw2 > li.naechste-seite > a") 

        return output_df, next_page_list

    # ランダムに待機する 2-3秒
    @staticmethod
    def random_sleep():
        import numpy as np
        from time import sleep

        sleeptime = np.random.randint(2, 3, size=1)[0] + np.random.rand(1).round(1)[0]
        sleep(sleeptime)

    # そのリーグのすべてのテーブルをスクレイピング
    # 引数にはそのリーグの最初のページのURL
    def scrayping_this_league(self, first_page_url):
        import pandas as pd

        url = first_page_url
        # 最初に空のデータフレームをつくる
        output_df = self.make_empty_df()
        # requestsの前に2秒以上待機
        self.random_sleep()

        while True:

            page_df, next_page_list = self.scrayping_this_page(url, headers=self.headers)
             # そのページをスクレイピングした情報と、次のページの有無の情報を返す
            
            # 場合によってはpage_dfがNoneの時がある
            if page_df.shape[0] != 0:
                output_df = pd.concat([output_df, page_df])
            
            #次のページに移る前に待機
            self.random_sleep()

            if len(next_page_list) == 0: # もし次のページがない場合
                break
            
            # 次のページのURLを生成
            url = self.transfer_url + next_page_list[0]["href"]

        return output_df # そのリーグのデータが入ったデータフレームを返して終了

    # shadow_elementの要素をスクレイピングするための関数 javascriptからshadow-rootを取得
    def expand_shadow_element(self, element):
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root

    # transfermarkt_webページ全てにある画面上部のshasow-DOMを開くための関数
    def open_shadow_DOM(self):
        # shadow-DOMの親要素を指定
        root_bar = self.driver.find_element_by_xpath('//*[@id="breadcrumb"]/div/div/tm-quick-select-bar')
        # shadow-DOMを開く
        shadow_root_bar = self.expand_shadow_element(root_bar)
        # shadow-root最上部の要素を返す
        return shadow_root_bar

    # transfermarktの検索条件にcountryの項目に値を入れる関数
    # shadow-rootを開いておくように!!!!!
    @staticmethod
    def fill_in_country(country_name, shadow_root_bar):
        # countryのところのボタンをクリック#choosen-country#choosen-country div > form:nth-child(2) > div.selector-title
        shadow_root_bar.find_element_by_css_selector('#choosen-country').click()
        # searchバーに国名を打ち込む
        shadow_root_bar.find_element_by_css_selector("div > form:nth-child(2) > div.selector-dropdown > div > input[type=search]").send_keys(country_name)
        #shadow_root_bar.find_element_by_class_name("country-dropdown-list-item").click()
        shadow_root_bar.find_element_by_css_selector("#mylist > li").click()
    
    # shadow-rootを開いておくように!!!!!
    @staticmethod
    def fill_in_competition(competition_name, shadow_root_bar, same_country_bool):
        
        if same_country_bool:
            # 国名が変わらない時はクリックしないとleague名打ち込めない
            # competetionをクリック
            shadow_root_bar.find_element_by_css_selector("div > form:nth-child(3) > div.selector-title > span").click()

        # leagueの名前を入力div > form:nth-child(3) > div.selector-dropdown > div > input[type=search]
        shadow_root_bar.find_element_by_css_selector("div > form:nth-child(3) > div.selector-dropdown > div > input[type=search]").send_keys(competition_name)
        # leagueをクリック div > form:nth-child(3) > div.selector-dropdown > ul > li
        shadow_root_bar.find_element_by_css_selector("div > form:nth-child(3) > div.selector-dropdown > ul > li").click()

    # 上の方のバーからcountry、competetionを選んでそのリーグの詳細テーブルのURLを返す関数 このバーは全てのページにある
    def guide_from_country_and_league_to_leagueurl(self, country_name, competition_name, same_country):
        from time import sleep
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # shadow-rootを開いておく
        shadow_root_bar = self.open_shadow_DOM()

        # 国そのままでいい場合はcountry設定しない
        if same_country:
            self.fill_in_competition(competition_name, shadow_root_bar, same_country_bool=True)
        # 国を変更する場合はcountryを設定
        # さらにcountry設定したときにleagueのdropdownが開く
        else:
            self.fill_in_country(country_name, shadow_root_bar)
            sleep(1)
            # 国名が変わる、つまり国名を設定するとき 三角ボタンは押さなくていい
            self.fill_in_competition(competition_name, shadow_root_bar, same_country_bool=False)

        # 次のページに移る前に2秒以上待機
        self.random_sleep()
        # forwardボタンをクリック
        shadow_root_bar.find_element_by_css_selector("div > form:nth-child(3) > a").click()

        # cup戦とかはtransfer情報がない!!
        try:
            # 暗示的に待機
            # このoverviewはLeagueでもCupでも存在する
            # これが読み込まれていれば、かつ横にtrasnferが存在するなら、すでに読み込まれているはず
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="overview"]/a')))
            # そのリーグのtransfer情報の部分へ誘導
            # 一時的にimplicitly_waitの待ち時間を変更
            self.driver.implicitly_wait(0)
            transfer_elem = self.driver.find_element_by_xpath('//*[@id="transfers"]')
        # transfer情報のタグが見つからないときに実行する処理
        except:
            self.driver.implicitly_wait(20)
            detail_url = None
            
        # 正常時、つまりtransfer_elemが見つかった時
        else:
            self.driver.implicitly_wait(20)
            self.driver.execute_script("arguments[0].scrollIntoView();", transfer_elem)
            script = "window.scrollTo(0, window.pageYOffset - 80);"
            self.driver.execute_script(script)
            
            # マウスオーバー操作
            #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="transfers"]')))
            actions = ActionChains(self.driver)
            actions.move_to_element(transfer_elem).perform()
            
            # 次のページに移るまで2秒以上待機
            self.random_sleep()
            # そのリーグのTransfer Recordをクリック
            self.driver.find_element_by_xpath('//*[@id="transfers"]/div/div/div[1]/ul/li[7]/a').click()

            # 移籍情報detailのURLを取得
            detail_url = self.driver.find_element_by_xpath('//*[@id="main"]/div[11]/div/div/div[2]/a[2]').get_attribute("href")
        
        return detail_url

    def search_competition(self, country_name):
        from time import sleep

        # shadow-DOMを開く
        shadow_root_bar = self.open_shadow_DOM()
        # 1秒待機 serverにアクセスするわけではないのでsleepでよいか
        sleep(1)
        self.fill_in_country(country_name, shadow_root_bar)
        sleep(1)
        # competetionの三角ボタンをクリック
        # これでcompetitionの一覧が得られる
        # 最新版ではこの操作いらない country_name入れたら勝手にcompetitionのところ開く
        #shadow_root_bar.find_element_by_css_selector("div > form:nth-child(3) > div > div").click()

        # competetionのリストを作成
        competetion_lis = []
        # tagnameなくてもerrorでなかった！！！
        lis = shadow_root_bar.find_elements_by_tag_name("li")
        for tag in lis:
            competetion_lis.append(tag.text)
            
        return competetion_lis

    # 最初にcountryのドロップダウンが閉じている必要がある!!
    def search_all_country(self):
        from time import sleep

        # shadow-DOMを開く
        shadow_root_bar = self.open_shadow_DOM()
        # 1秒待機 serverにアクセスするわけではないのでsleepでよいか
        sleep(1)
        # countryの三角ボタンをクリック
        shadow_root_bar.find_element_by_css_selector("div > form:nth-child(2) > div > div").click()

        # 全てのcountry入れるリストを作成
        all_country = []
        lis = shadow_root_bar.find_elements_by_tag_name("li")
        for tag in lis:
            all_country.append(tag.text)

        # 最後にtopページに戻っておく
        # 後のscraypingとの関係 countryの三角クリックして国名入れたい
        self.driver.find_element_by_xpath('//*[@id="header"]/div[4]/div[1]/a').click()
        
        return all_country

    # 検索する国名のリストを設定したらその国々をスクレイピングしてくれる関数
    def scrayping_countries(self, country_lis, output_filename):
        import numpy as np
        import pandas as pd
        import os
        
        output_df = self.make_empty_df()
        # Errorが出た時の記録用csvファイル
        error_df = pd.DataFrame(np.zeros((0, 4)), columns=["Country", "Competition", "Error", "Message"])

        for country in country_lis:

            try:
                # その国の全てのcompetiotonを検索
                all_competitions = self.search_competition(country)
            # 例外が起こったときの処理
            except:
                # top ページに戻る
                self.driver.get(self.transfer_url)
                all_competitions = self.search_competition(country)


            # 要素が0でなかったらscrayping進める （afganistan）などはリーグのデータがない地域がある!!!!
            if all_competitions:

                for y, comp in enumerate(all_competitions):
                    
                    try:
                        # 国が切り替わる時は、country入れたら自動でleagueのdropdownが開く!!!
                        if y == 0:
                            detail_url = self.guide_from_country_and_league_to_leagueurl(country, comp, same_country=False)
                        # 同じ国でループ回すときはcountryのところいちいち変える必要ない
                        else:
                            detail_url = self.guide_from_country_and_league_to_leagueurl(country, comp, same_country=True)
                        
                    except Exception as e:
                        print("URL-ERROR:", country, ":", comp)
                        print("MESSAGE: ", e)
                        error_info = np.array([country, comp, "URL-ERROR", e]).reshape(1, -1)
                        error_info_df = pd.DataFrame(error_info, columns=error_df.columns)
                        error_df = pd.concat([error_df, error_info_df])
                        # もしスクロールした後エラー出たら次のcompetition打てる所まで戻る操作が必要
                        back_elem = self.driver.find_element_by_xpath('//*[@id="header"]/div[4]/div[1]/a/img')
                        self.driver.execute_script("arguments[0].scrollIntoView();", back_elem)
                        continue

                    # detail_urlが存在する、つまりcompetitionがリーグ戦である時
                    if detail_url:
                        try:
                            # detail_urlがNoneではなかったらスクレイピングを行う
                            df = self.scrayping_this_league(detail_url)
                        
                        except Exception as e:
                            print("SCRAYPING-ERROR:", country, ":", comp)
                            print("MESSAGE: ", e)
                            error_info = np.array([country, comp, "SCRAYPING-ERROR", e]).reshape(1, -1)
                            error_info_df = pd.DataFrame(error_info, columns=error_df.columns)
                            error_df = pd.concat([error_df, error_info_df])
                            continue
                        
                        else:
                            output_df = pd.concat([output_df, df])
                            print("OK:", country, ":", comp)
                    
            else:
                print("No Data:", country)
                no_data_info = np.array([country, "None", "No-Data", "None"]).reshape(1, -1)
                no_data_info_df = pd.DataFrame(no_data_info, columns=error_df.columns)
                error_df = pd.concat([error_df, no_data_info_df])

        # current directory下にoutputディレクトリがあるか確認
        # ない場合作成する
        if not os.path.exists("./output/"):
            os.mkdir("./output")
        
        output_df.to_csv("./output/{}.csv".format(output_filename), index=False)
        error_df.to_csv("./output/{}_Error.csv".format(output_filename), index=False)
        print("done!")
