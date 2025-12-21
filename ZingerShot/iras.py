#
# 「いらすとや」からランダムに画像を読み込み
# iras.py 2025/12/21
#
import pyxel
import requests
import json
from bs4 import BeautifulSoup
from PIL import Image
from PIL import UnidentifiedImageError
from io import BytesIO
import numpy as np

PYXEL_PALETTE = (
    0x000000, 0x2B335F, 0x7E2072, 0x19959C,
    0x8B4852, 0x395C98, 0xA9C1FF, 0xEEEEEE,
    0xD4186C, 0xD38441, 0xE9C35B, 0x70C6A9,
    0x7696DE, 0xA3A3A3, 0xFF9798, 0xEDC7B0)

class Irasutoya:
    def get_total_posts(self):  # 総画像数の取得（エラー:111）
        feed_url = 'https://www.irasutoya.com/feeds/posts/summary?alt=json'  # フィードのURLを構築
        try:
            response = requests.get(feed_url, timeout=3)  # フィードを取得
        except requests.exceptions.RequestException:
            self.error_code = 111
            return 0
        feed_data = json.loads(response.text)
        total_posts = int(feed_data['feed']['openSearch$totalResults']['$t'])  # 総画像数の取得
        return total_posts

    def __init__(self):  # （エラー:111）
        self.error_code = 0
        self.height = 0
        self.width = 0
        self.original_image = None
        self.total_posts = self.get_total_posts()  # （エラー:111）
        self.post_num = 0

    def get_random_post_url(self, post_num=-1):  # （エラー:211）
        if 1<=post_num<=self.total_posts:
            self.post_num = post_num
        else:
            self.post_num = pyxel.rndi(1, self.total_posts) # ランダムな投稿番号を生成
        random_post_feed_url = f"https://www.irasutoya.com/feeds/posts/summary?start-index={self.post_num}&max-results=1&alt=json"  # ランダムな投稿のURLを取得
        try:
            random_post_response = requests.get(random_post_feed_url, timeout=3)
        except requests.exceptions.RequestException:
            self.error_code = 211
            return ''
        random_post_data = json.loads(random_post_response.text)
        random_post_url = random_post_data['feed']['entry'][0]['link'][-1]['href']  # 投稿のURLを取得
        return random_post_url

    def get_imageurl_title(self, url):  # （エラー:311,321,322,331,332）
        try:
            response = requests.get(url, timeout=3)  # ページのHTMLを取得
        except requests.exceptions.RequestException:
            self.error_code = 311  # Timeout可能性あり
            return '', ''
        soup = BeautifulSoup(response.text, 'html.parser')
        image_url, title_text = '', ''
        image_div = soup.find('div', class_='separator')  # 画像URLを取得
        if image_div:
            image_tag = image_div.find('a')
            if image_tag and 'href' in image_tag.attrs:
                image_url = image_tag['href']
            else:
                self.error_code = 321
        else:
            self.error_code = 322  # 画像URL取得不可
        title_div = soup.find('div', class_='title')  # タイトル文字列を取得
        if title_div:
            title_text = title_div.text.strip()
            if title_text=='':
                self.error_code = 331
        else:
            self.error_code = 332
        return image_url, title_text

    def load_image(self, image_url, size):  # 画像読込み（エラー：411,412）
        try:
            response = requests.get(image_url, timeout=3)
        except requests.exceptions.RequestException:
            self.error_code = 411
            return None
        try:
            self.original_image = Image.open(BytesIO(response.content))
        except UnidentifiedImageError:  # 画像ファイルを正しく識別できない
            self.error_code = 412
            return None
        img = self.original_image.convert('RGBA')  # PNGの場合、アルファチャンネル（透明度）を保持
        img.thumbnail(size, Image.LANCZOS)  # アスペクト比を維持しながらリサイズ
        return img

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

    def random_image_title(self, size=(256,256), transparent=16, post_num=-1, imagebank=0):  # （エラー:211,11,321,322,331,332,411,412）
        random_post_url = self.get_random_post_url(post_num)  # （エラー:211）
        if self.error_code:
            return ''
        image_url, title = self.get_imageurl_title(random_post_url)  # （エラー:311,321,322,331,332）
        if self.error_code:
            return ''
        img = self.load_image(image_url, size)  # （エラー:411,412）
        if self.error_code:
            return ''
        self.width,self.height = img.size  # 【エラーあり】AttributeError: 'NoneType' object has no attribute 'size'
        img_array = np.array(img)
        sx = (max(self.width,self.height)-self.width)//2
        sy = (max(self.width,self.height)-self.height)//2
        for y in range(256):
            for x in range(256):
                pyxel.images[imagebank].pset(x,y,transparent)
        for y in range(self.height):
            for x in range(self.width):
                r,g,b,a = img_array[y,x]
                if a<16 and 0<=transparent<16: # アルファ値：透明
                    pyxel.images[imagebank].pset(sx+x,sy+y,transparent)
                else:
                    pyxel.images[imagebank].pset(sx+x,sy+y,self.closest_pyxel_color(r,g,b,a))
        return title

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

