
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from transfermarkt import TransferMarkt

options = Options()
options.add_argument("--headless")
options.page_load_strategy = 'none'
driver = webdriver.Chrome("C:/Users/yoshi/webdriver/chromedriver_win32_2/chromedriver.exe", options=options)

headers = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"}
#"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
#"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84"
# chrome、chrome-driverのversionはころころ変わるので注意
# transfermarktのホームページ開いて動的に操作したい場合(各リーグの詳細テーブルのURLを取得したい時など)はdriver引数の設定が必要
# 詳細テーブルのURLからscraypingしたい時はrequestsに渡すheaders引数を設定する必要がある
tf = TransferMarkt(driver=driver, headers=headers)

all_countries = tf.search_all_country()
tf.scrayping_countries(country_lis=all_countries, output_filename="world_20211005")

driver.close()
driver.quit()
