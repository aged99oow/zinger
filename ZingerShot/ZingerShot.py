#
# Zinger Shot
# Zinger.py 2025/12/14
#
import pyxel
import pxt
import iras
import retort

IMG_SIZE = 128 #158  # イラストサイズ
WIDTH = 202  # アプリ幅
IMG_XYWH = (4,4, IMG_SIZE+2,IMG_SIZE+2)  # イラスト
TITLE_XYWH = (4,IMG_XYWH[1]+IMG_XYWH[3], IMG_SIZE+2,15)  # タイトル
AUTO_BTN_XYWH = (IMG_SIZE+19,IMG_XYWH[1]+IMG_XYWH[3]-42, 42,19)  # オートボタン
IMG_BTN_XYWH = (IMG_SIZE+10,IMG_XYWH[1]+IMG_XYWH[3]-19, 60,19)  # イラスト変更ボタン
HEIGHT = TITLE_XYWH[1]+TITLE_XYWH[3]+2  # アプリ高さ
BG_COL,FRAME_COL = pyxel.COLOR_NAVY,pyxel.COLOR_CYAN

class App:
    def load_img(self):  # イラスト読み込み：成功False／エラーTrue
        for i in range(3):
            desc = self.iras.random_image_title((IMG_SIZE,IMG_SIZE), 7, -1)
            img_txt = f'{self.iras.post_num:<5} {desc}'
            print('No.'+img_txt)
            if self.iras.error_code:
                print(f'         画像読み込み失敗{i+1} エラー{self.iras.error_code}')
                self.iras.error_code = 0
                continue
            else:
                break
        else:
            print('         画像なし')
            return False
        self.title = self.iras.amend_title(desc)  # タイトル
        print('         '+self.title)
        return True

    def set_popup(self, txt):  # ポップアップセット
        self.popup_txt = txt
        chars,lines = pxt.textbox(0,0, self.popup_txt, txt_out=False)
        self.popup_w = chars*4+4
        self.popup_h = lines*12+3
        self.popup_x = IMG_XYWH[0]+(IMG_XYWH[2]-self.popup_w)//2
        self.popup_y = IMG_XYWH[1]+(IMG_XYWH[3]-self.popup_h)//2
        self.popup_exists = True

    def in_cursor(self, xywh):  # カーソル内
        if xywh[0]<=pyxel.mouse_x<xywh[0]+xywh[2] and xywh[1]<=pyxel.mouse_y<xywh[1]+xywh[3]:
            return True
        return False

    def __init__(self):
        pyxel.init(WIDTH,HEIGHT, title='Zinger Shot', display_scale=3, capture_scale=3, capture_sec=90)
        pyxel.load('ZingerShot.pyxres')
        pyxel.integer_scale(True)
        pyxel.mouse(True)
        self.iras = iras.Irasutoya()
        if self.iras.error_code:
            print(f'接続エラー{self.iras.error_code}')
        print(f'全イラスト数 {self.iras.total_posts}')
        self.auto_cnt = 0  # オートモードOFF
        self.popup_exists = False
        self.img_exists = False
        self.load_cnt = 10  # リロードカウント
        pyxel.run(self.update, self.draw) 

    def update(self):
        if self.load_cnt:  # リロード中
            self.load_cnt -= 1
            if self.load_cnt==9:  # イラスト読み込みポップアップ表示
                self.set_popup('イラスト読み込み')
            elif self.load_cnt==6:  # イラスト読み込み
                if(not self.load_img()):  # 読み込みエラー
                    self.load_cnt = 0  # リロード中断
                    self.auto_cnt = 0  # オートモードOFF
                    self.set_popup('読み込みエラー')
                    self.img_exists = False
            elif self.load_cnt==3:  # 一言読み込み
                self.oneliner = pxt.pyxel_choice(retort.RETORT_DIC)  # 一言
                self.oneliner_lines = self.oneliner.count('\n')  # 一言行数
                self.img_exists = True
            elif self.load_cnt==0:  # イラスト読み込みポップアップ消去
                self.popup_exists = False
            return

        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            self.popup_exists = False  # ポップアップ消去
            if self.auto_cnt:  # オートモードOFF
                self.auto_cnt = 0  # オートモードOFF
            elif self.in_cursor(AUTO_BTN_XYWH):  # ボタン：オートモードON
                self.auto_cnt = 2
            elif self.in_cursor(IMG_BTN_XYWH):  # ボタン：イラスト変更
                self.load_cnt = 10
        if self.auto_cnt:
            self.auto_cnt -= 1
            if self.auto_cnt==1:
                self.auto_cnt = 180  # 180カウントごとにイラスト変更
                self.load_cnt = 10

    def draw(self):
        pyxel.cls(BG_COL)
        pyxel.rectb(*IMG_XYWH, FRAME_COL)  # メインイラスト（枠）
        if self.img_exists:
            pyxel.blt(IMG_XYWH[0]+1,IMG_XYWH[1]+1, 0, 0,0, IMG_SIZE,IMG_SIZE)  # イラスト
            pxt.speech_bubble(IMG_XYWH[0]+IMG_XYWH[2]-20,IMG_XYWH[1]+25+self.oneliner_lines*12, 0, self.oneliner, 10)  # 一言
            chars,lines = pxt.textbox(0,0, self.title, txt_out=False)
            pxt.textbox(TITLE_XYWH[0] if chars>(IMG_SIZE+2)//4 else TITLE_XYWH[0]+TITLE_XYWH[2]//2-chars*2,TITLE_XYWH[1]+2, self.title, pyxel.COLOR_LIGHT_BLUE)  # タイトル
        pyxel.elli(*AUTO_BTN_XYWH, pyxel.COLOR_RED if self.auto_cnt else pyxel.COLOR_ORANGE if self.in_cursor(AUTO_BTN_XYWH) else pyxel.COLOR_NAVY)  # オートボタン（背景）
        pyxel.ellib(*AUTO_BTN_XYWH, pyxel.COLOR_LIGHT_BLUE if self.auto_cnt else FRAME_COL)  # オートボタン（枠）
        pxt.textline(AUTO_BTN_XYWH[0]+10,AUTO_BTN_XYWH[1]+4, 'オート', pyxel.COLOR_WHITE if self.auto_cnt or self.in_cursor(AUTO_BTN_XYWH) else pyxel.COLOR_GRAY)  # オートボタン
        pyxel.elli(*IMG_BTN_XYWH, pyxel.COLOR_ORANGE if self.in_cursor(IMG_BTN_XYWH) else pyxel.COLOR_NAVY)  # イラスト変更ボタン（背景）
        pyxel.ellib(*IMG_BTN_XYWH, FRAME_COL)  # イラスト変更ボタン（枠）
        pxt.textline(IMG_BTN_XYWH[0]+6,IMG_BTN_XYWH[1]+4, 'イラスト変更', pyxel.COLOR_WHITE if self.in_cursor(IMG_BTN_XYWH) else pyxel.COLOR_GRAY)  # イラスト変更ボタン
        if self.popup_exists:
            pyxel.rect(self.popup_x,self.popup_y,self.popup_w,self.popup_h, pyxel.COLOR_BLACK)  # ポップアップ（背景）
            pyxel.rectb(self.popup_x,self.popup_y,self.popup_w,self.popup_h, pyxel.COLOR_WHITE)  # ポップアップ（枠）
            pxt.textbox(self.popup_x+2,self.popup_y+2, self.popup_txt, pyxel.COLOR_YELLOW)  # ポップアップ

        #pyxel.text(0, 0, f'Load:{self.load_cnt:>2} / Auto:{self.auto_cnt:>3}', 3)
        #pyxel.text(0, 6, f'Post:{self.iras.post_num:>5} / {self.iras.total_posts:5}', 3)

App()
