#
# Zinger Shot (Web)
# ZingerShotWeb.py 2025/12/12
#
import pyxel
import pxt
import iras_web
import retort

IMG_SIZE = 128  # イラストサイズ
WIDTH = 202  # アプリ幅
IMG_XYWH = (4,4, IMG_SIZE+2,IMG_SIZE+2)  # イラスト
TITLE_XYWH = (4,IMG_XYWH[1]+IMG_XYWH[3], IMG_SIZE+2,15)  # タイトル
AUTO_BTN_XYWH = (IMG_SIZE+19,IMG_XYWH[1]+IMG_XYWH[3]-42, 42,19)  # オートボタン
IMG_BTN_XYWH = (IMG_SIZE+10,IMG_XYWH[1]+IMG_XYWH[3]-19, 60,19)  # イラスト変更ボタン
HEIGHT = TITLE_XYWH[1]+TITLE_XYWH[3]+2  # アプリ高さ
BG_COL,FRAME_COL = pyxel.COLOR_NAVY,pyxel.COLOR_CYAN
READY,SUCCESS,FAILURE = iras_web.READY,iras_web.SUCCESS,iras_web.FAILURE
POPUP_TOTAL,GET_TOTAL,FAIL_TOTAL,POPUP_IMG,GET_RNDURL,GET_IMGURL,GET_IMG,FAIL_IMG,MAIN_LOOP = 0,1,9,10,11,12,13,19,20

class App:
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
        pyxel.init(WIDTH,HEIGHT, title='Zinger Shot (Web)')
        pyxel.load('ZingerShot.pyxres')
        #pyxel.integer_scale(True)
        pyxel.mouse(True)
        self.iras = iras_web.Irasutoya()
        self.status = POPUP_TOTAL
        self.retry = 0
        self.auto_cnt = 0  # オートモードOFF
        self.popup_exists = False
        self.img_exists = False
        pyxel.run(self.update, self.draw) 

    def update(self):
        if self.status==POPUP_TOTAL:  # イラスト総数取得ポップアップ
            self.set_popup('イラスト総数取得')
            self.retry = 0
            self.iras.fetch_status = READY
            self.status = GET_TOTAL
        elif self.status==GET_TOTAL:  # イラスト総数取得
            self.iras.get_total_posts()
            if self.iras.fetch_status==SUCCESS:
                self.status = POPUP_IMG
            elif self.iras.fetch_status==FAILURE:
                self.retry += 1
                if self.retry>=3:
                    self.status = FAIL_TOTAL
                else:
                    self.iras.fetch_status = READY
        elif self.status==FAIL_TOTAL:  # 総数取得失敗
            self.set_popup('読み込みエラー')
            #self.set_popup(self.iras.error_txt)
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
                self.status = POPUP_TOTAL

        elif self.status==POPUP_IMG:  # イラスト読み込みポップアップ
            self.set_popup('イラスト読み込み')
            self.retry = 0
            self.iras.fetch_status = READY
            self.status = GET_RNDURL
        elif self.status==GET_RNDURL:  # ランダムURL取得
            self.iras.get_random_post_url()
            if self.iras.fetch_status==SUCCESS:
                self.iras.fetch_status = READY
                self.status = GET_IMGURL
            elif self.iras.fetch_status==FAILURE:
                self.retry += 1
                if self.retry>=3:
                    self.status = FAIL_IMG
                else:
                    self.iras.fetch_status = READY
        elif self.status==GET_IMGURL:  # タイトル・イラストURL取得
            self.iras.get_image_url()
            if self.iras.fetch_status==SUCCESS:
                self.iras.fetch_status = READY
                self.status = GET_IMG
            elif self.iras.fetch_status==FAILURE:
                self.retry += 1
                if self.retry>=3:
                    self.status = FAIL_IMG
                else:
                    self.iras.fetch_status = READY
                    self.status = GET_RNDURL
        elif self.status==GET_IMG:  # イラスト取得
            self.iras.get_image()
            if self.iras.fetch_status==SUCCESS:
                self.title = self.iras.amend_title(self.iras.title_text)  # タイトル
                self.oneliner = pxt.pyxel_choice(retort.RETORT_DIC)  # 一言
                self.oneliner_lines = self.oneliner.count('\n')  # 一言行数
                self.img_exists = True
                self.popup_exists = False
                self.status = MAIN_LOOP
            elif self.iras.fetch_status==FAILURE:
                self.retry += 1
                if self.retry>=3:
                    self.status = FAIL_IMG
                else:
                    self.iras.fetch_status = READY
                    self.status = GET_RNDURL
        elif self.status==FAIL_IMG:  # イラスト読み込み失敗
            self.set_popup('読み込みエラー')
            #self.set_popup(self.iras.error_txt)
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
                self.status = POPUP_IMG

        elif self.status==MAIN_LOOP:  # メインループ
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
                self.popup_exists = False
                if self.auto_cnt:
                    self.auto_cnt = 0  # オートモードOFF
                elif self.in_cursor(AUTO_BTN_XYWH):  # ボタン：オートモードON
                    self.auto_cnt = 2
                elif self.in_cursor(IMG_BTN_XYWH):  # ボタン：イラスト変更
                    self.status = POPUP_IMG
            if self.auto_cnt:
                self.auto_cnt -= 1
                if self.auto_cnt==1:
                    self.auto_cnt = 150  # 150カウントごとにイラスト変更
                    self.status = POPUP_IMG

    def draw(self):
        pyxel.cls(BG_COL)
        pyxel.rectb(*IMG_XYWH, FRAME_COL)  # イラスト（枠）
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
        
        #pyxel.text(0, 0, f'Status:{self.status:>2} / Fetch:{self.iras.fetch_status:>2} / Auto:{self.auto_cnt:>3} / Retry:{self.retry}', 3)
        #pyxel.text(0, 6, f'Post:{self.iras.post_num:>5} / {self.iras.total_posts:5}', 3)
        #pyxel.text(0,12, 'RndURL:'+self.iras.random_post_url, 3)
        #pyxel.text(0,18, 'ImgURL:'+self.iras.image_url, 3)
        #pxt.textbox(0,24, 'Title:'+self.iras.title_text, 3)
        #pyxel.text(0,36, f"{self.iras.text}", 3)

App()
