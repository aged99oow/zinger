#
# 「いらすとや」ランダム画像取得（Web）
# iras_web.py 2025/12/21
#
import pyxel
import pxt
import asyncio
from pyodide.http import pyfetch
import json
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import numpy as np

PYXEL_PALETTE = (
    0x000000, 0x2B335F, 0x7E2072, 0x19959C,
    0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9,
    0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0)
TRANSPARENT = pyxel.COLOR_WHITE  # 7
IMG_BANK = 0
IMG_SIZE = 128
FETCHING,READY,SUCCEEDING,FAILING,SUCCESS,FAILURE = -1,0,1,2,20,40

class Irasutoya:
    def __init__(self):
        self.fetch_status = READY
        self.error_txt = ''
        self.fetch_txt = ''
        self.fetch_img = None
        self.total_posts = 0
        self.post_num = 0
        self.random_post_url = ''
        self.image_url = ''
        self.title_text = ''

    async def fetch_text(self, url, cors=1):  # テキスト取得（エラー:511）
        if cors==1:
            url = 'https://api.codetabs.com/v1/proxy/?quest='+url
        elif cors==2:
            url = 'https://api.allorigins.win/raw?url='+url
        try:
            response = await pyfetch(url)
            self.fetch_txt = await response.text()
        except Exception as e:
            self.error_txt = 'Error 511: '+str(e)  # 通信エラー
            self.fetch_status = FAILING
        else:
            self.fetch_status = SUCCEEDING

    async def fetch_image(self, url, cors=1):  # 画像取得（エラー:521,523）
        if cors==1:
            url = 'https://api.codetabs.com/v1/proxy/?quest='+url
        elif cors==2:
            url = 'https://api.allorigins.win/raw?url='+url
        try:
            response = await pyfetch(url)
        except Exception as e:
            self.error_txt = 'Error 521: '+str(e)  # 画像取得エラー
            self.fetch_status = FAILING
            return
        if not response or response.status!=200:
            self.error_txt = 'Error 522: '+str(response)  # 読込・応答エラー
            self.fetch_status = FAILING
            return
        try:
            blob = await response.bytes()
            self.fetch_img = Image.open(BytesIO(blob))
        except Exception as e:
            self.error_txt = 'Error 523: '+str(e)
            self.fetch_img = None
            self.fetch_status = FAILING
        else:
            self.fetch_status = SUCCEEDING

    def closest_pyxel_color(self, r, g, b, a):
        min_distance = float('inf')
        closest_color = 0
        r,g,b,a = float(r),float(g),float(b),float(a)/255
        for i, color in enumerate(PYXEL_PALETTE):
            pr,pg,pb = (color>>16)&255,(color>>8)&255,color&255
            pr,pg,pb = float(pr),float(pg),float(pb)
            dr,dg,db = (r*a)-pr,(g*a)-pg,(b*a)-pb
            distance = dr*dr+dg*dg+db*db
            if distance<min_distance:
                min_distance = distance
                closest_color = i
                if distance==0:
                    break
        return closest_color

    def get_total_posts(self):  # イラスト総数取得
            if self.fetch_status==READY:
                self.fetch_status = FETCHING
                asyncio.ensure_future(self.fetch_text('https://www.irasutoya.com/feeds/posts/summary?alt=json'))
            elif self.fetch_status==SUCCEEDING:
                try:
                    data = json.loads(self.fetch_txt)
                    self.total_posts = int(data['feed']['openSearch$totalResults']['$t'])
                except json.JSONDecodeError as e:
                    self.error_txt = str(e)
                    self.fetch_status = FAILURE
                else:
                    self.fetch_status = SUCCESS
            elif self.fetch_status==FAILING:
                self.fetch_status = FAILURE

    def get_random_post_url(self):  # ランダムURL取得
            if self.fetch_status==READY:
                self.fetch_status = FETCHING
                self.post_num = pyxel.rndi(1,self.total_posts-1)
                asyncio.ensure_future(self.fetch_text(f'https://www.irasutoya.com/feeds/posts/summary?start-index={self.post_num}%26max-results=1%26alt=json'))
            elif self.fetch_status==SUCCEEDING:
                try:
                    data = json.loads(self.fetch_txt)
                    self.random_post_url = data['feed']['entry'][0]['link'][-1]['href']
                except json.JSONDecodeError as e:
                    self.error_txt = str(e)
                    self.fetch_status = FAILURE
                else:
                    self.fetch_status = SUCCESS
            elif self.fetch_status==FAILING:
                self.fetch_status = FAILURE

    def get_image_url(self):  # タイトル・イラストURL取得（エラー:321,322,331,332）
            if self.fetch_status==READY:
                self.fetch_status = FETCHING
                asyncio.ensure_future(self.fetch_text(self.random_post_url))
            elif self.fetch_status==SUCCEEDING:
                soup = BeautifulSoup(self.fetch_txt, 'html.parser')
                image_div = soup.find('div', class_='separator')  # 画像URLを取得
                if image_div:
                    image_tag = image_div.find('a')
                    if image_tag and 'href' in image_tag.attrs:
                        self.image_url = image_tag['href']
                    else:
                        self.error_txt = 'Error 321: '
                        self.fetch_status = FAILURE
                        return
                else:
                    self.error_txt = 'Error 322: '  # 画像URL取得不可
                    self.fetch_status = FAILURE
                    return
                title_div = soup.find('div', class_='title')  # タイトル取得
                if title_div:
                    self.title_text = title_div.text.strip()
                    if self.title_text=='':
                        self.error_txt = 'Error 331: '
                        self.fetch_status = FAILURE
                        return
                else:
                    self.error_txt = 'Error 332: '
                    self.fetch_status = FAILURE
                    return
                self.fetch_status = SUCCESS
            elif self.fetch_status==FAILING:
                self.fetch_status = FAILURE

    def get_image(self):  # イラスト取得
            if self.fetch_status==READY:
                self.fetch_status = FETCHING
                asyncio.ensure_future(self.fetch_image(self.image_url))
            elif self.fetch_status==SUCCEEDING:
                img = self.fetch_img.convert('RGBA')  # PNGの場合、アルファチャンネル（透明度）を保持
                img.thumbnail((IMG_SIZE, IMG_SIZE), Image.LANCZOS)  # アスペクト比を維持してリサイズ
                self.width,self.height = img.size
                img_array = np.array(img)
                sx = (max(self.width,self.height)-self.width)//2
                sy = (max(self.width,self.height)-self.height)//2
                for y in range(256):
                    for x in range(256):
                        pyxel.images[IMG_BANK].pset(x,y,TRANSPARENT)
                for y in range(self.height):
                    for x in range(self.width):
                        r,g,b,a = img_array[y,x]
                        if a<16: # アルファ値：透明
                            pyxel.images[IMG_BANK].pset(sx+x,sy+y,TRANSPARENT)
                        else:
                            pyxel.images[IMG_BANK].pset(sx+x,sy+y,self.closest_pyxel_color(r,g,b,a))
                self.fetch_status = SUCCESS
            elif self.fetch_status==FAILING:
                self.fetch_status = FAILURE

    def remove_lastparen_block(self, txt):  # 文末の（...）を削除
        if not txt.endswith('）'):
            return txt
        depth = 0
        for i in range(len(txt)-1, -1, -1):
            if txt[i] == '）':
                depth += 1
            elif txt[i] == '（':
                depth -= 1
                if depth == 0:
                    return txt[:i]
        return txt

    def amend_title(self, txt):
        CV_PRE = [['イラストレーター','＄＄＄'], ]  # 前処理
        CV_POST = [['＄＄＄','イラストレーター'], ]  # 後処理
        CV_IRAS_DESCRIP = [
                'いろいろな角度から見た', '正面から見た', '前から見た', '後ろから見た', '横から見た', '上から見た', 
                'いろいろな表情の', 'いろいろな世代の', 'いろいろな年齢の', 'いろいろな色の', 'いろいろな', '色々な', 
                '「タイトル文字」', '「イラスト文字」', 'のイラストPOP文字', 'のタイトル文字', 'のイラスト文字', 'イラスト文字', 
                'のハガキテンプレート', 'のはがきテンプレート', 'のテンプレート', 'テンプレート', 'のライン素材', 
                'の背景素材', 'のPOP素材', 'POP素材', 'のフレーム素材', 'のパターン素材',  
                'のイメージのイラスト', 'の似顔絵イラスト', 'のメッセージイラスト', 'のイラストフレーム', 'のイラストリクエスト', 
                'のフレーム', 'のイラスト2', 'のイラスト', 'イラスト', 'のキャラクター', 'のマーク', 'のアイコン', ]  # 不要文字
        CV_UNDISPLAY_WORD = [
                ['招財進寶','招財進ぽう'], ['一揆','いっき'], ['饅頭','まんじゅう'], ['綺麗','きれい'], ['撥水','はっ水'], ['嚥下','えん下'], ['几帳','き帳'], 
                ['餃子','ギョーザ'], ['明菴栄西','明あん栄西'], ['花椒','かしょう'], 
                ['炒め','いため'], ['躾','しつけ'], ['痙攣','けいれん'], ['六芒星','六ぼう星'], ['啐啄同時','そっ啄同時'], ['痺れ','しびれ'], 
                ['哺乳瓶','ほ乳瓶'], ['喀痰検査','かくたん検査'], ['稟議','りん議'], ['茹で','ゆで'], ['枡','ます'], ['巫女','みこ'], ['閻魔','えん魔'], ['剪定','せん定'], 
                ['睨み','にらみ'], ['嗅ぐ','かぐ'], ['猩々','しょうじょう'], ['賽','さい'], ['土蜘蛛','土グモ'], ['戌年','いぬ年'], ['羊羹','羊かん'], 
                ['脾臓','ひ臓'], ['徘徊','はいかい'], ['蛆','うじ'], ['麻痺','麻ひ'], ['胚芽米','はい芽米'], 
                ['罠','わな'], ['屏風','びょうぶ'], ['揉まれる','もまれる'], ['涅槃','ねはん'], ['印籠','印ろう'], ['生姜','しょうが'], ['孵化','ふ化'], 
                ['祓い','はらい'], ['山椒','山ショウ'], ['琥珀','こはく'], ['軍荼利明王','軍だ利明王'], ['睨まれた','にらまれた'], 
                ['痒い','かゆい'], ['親鸞','親らん'], ['筐体','きょう体'], ['蜘蛛','クモ'],
                ['華奢','華しゃ'], ['一筆箋','一筆せん'], ['鳳梨酥','フォンリースー'], ['駕籠','かご'], ['熱燗','熱かん'], ['小籠包','小ロン包'], ['奢る','おごる'], 
                ['壺','つぼ'], ['贅肉','ぜい肉'], ['頷いて','うなずいて'], ['眩しい','まぶしい'], ['筍','タケノコ'], ['霊柩車','霊きゅう車'], ['処方箋','処方せん'], 
                ['鍼','はり'], ['茹でる','ゆでる'], ['水蜘蛛','水グモ'], ['外反母趾','外反母し'], ['揉める','もめる'], 
                ['改札鋏','改札ばさみ'], ['5月病','五月病'], ['菘','すずな'], 
                ['薺','なずな'], ['繁縷','はこべ'], ['シベリアン・ハスキー','シベリアンハスキー'], ['隋臣','ずい臣'], ['付箋','付せん'], ['灯籠','灯ろう'], 
                ['灯篭流し','灯ろう流し'], ['熨斗','のし'], ['光圀','光国'], ['薔薇','バラ'], 
                ['嘔吐','おう吐'], ['アキレス腱','アキレスけん'], ['絆創膏','ばん創膏'], ['飯盒炊爨','飯ごう炊さん'], ['苺','イチゴ'], ]  # 表示不可文字
        txt = self.remove_lastparen_block(txt)
        for cv in CV_PRE:
            txt = txt.replace(cv[0], cv[1])
        for cv in CV_IRAS_DESCRIP:
            txt = txt.replace(cv, '')
        for cv in CV_UNDISPLAY_WORD:
            txt = txt.replace(cv[0], cv[1])
        for cv in CV_POST:
            txt = txt.replace(cv[0], cv[1])
        return txt
