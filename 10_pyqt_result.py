import cv2
import threading
import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtTest
from PyQt5.QtGui import *

# 경로
path = [
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_2_F_d9_인큐베이터/captured_data_hospital_20200207_133526_인큐베이터/',
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_3/captured_data_hospital_20200207_161139/',
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_4_M_d2/captured_data_hospital_20200207_211837/',
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_5_M_d16/captured_data_hospital_20200210_163202/',
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_6_M_d3/captured_data_hospital_20200213_143500/',
    '/home/lkw/PycharmProjects/newborn_video/newborn_data/Baby_7_M_d4/captured_data_hospital_20200213_170925/']

data_start_num = ['202002071340', '202002071617', '202002072124', '202002101632', '202002131440', '202002131709']
date_end_num = ['202002071525', '202002071742', '202002072259', '202002101842', '202002131700', '202002131829']

# 사용할 변수들
baby_num = 0
extension = '.avi'

speed_V = 1.0
running = False
path_str = ''

start_frame = 0
end_frame = 0
cnt_frame = 0
video_index = 0
x_ticks = []

waiting = False
isfirstSearch = True
isStop = False

lable_ticks = [0]
lable_index = 0

form_class = uic.loadUiType("gui.ui")[0]


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.button_cal.clicked.connect(self.btn_cal)
        self.button_search.clicked.connect(self.btn_search)
        #self.button_playall.clicked.connect(self.btn_play_all)
        self.button_restart.clicked.connect(self.btn_restart)

        self.combo_baby.addItem("-")
        self.combo_baby.addItem("2")
        self.combo_baby.addItem("3")
        self.combo_baby.addItem("4")
        self.combo_baby.addItem("5")
        self.combo_baby.addItem("6")
        self.combo_baby.addItem("7")
        self.combo_baby.activated[str].connect(self.combobox_Changed)
        self.combo_video.activated[str].connect(self.combobox_video_Changed)

        self.state.setStyleSheet("background-color: white; border: 1px solid black;")

    def update_lable(self):
        global lable_ticks
        global lable_index

        input_lable = label_state_input.text()

        update_file = 'baby' + str(baby_num + 2) + '_kmeans.txt'
        file = '/home/lkw/PycharmProjects/newborn_video/' + update_file
        kmean_df = pd.read_csv(file, sep=' ', header=None)

        if not input_lable == '':
            kmean_df[1][lable_index + lable_ticks[video_index]-1] = input_lable
            kmean_df.to_csv('baby' + str(baby_num + 2) + '_kmeans.txt', sep=" ", index=False, header=None)

    def keyPressEvent(self, e):
        global speed_V
        global cnt_frame
        global waiting
        global lable_index
        global start_frame
        global end_frame

        # [, ], enter, 0, 1, 2, 3, esc, +, -

        if waiting:
            # [ : <-
            if e.key() == 91:
                if cnt_frame >= start_frame+120:
                    cnt_frame -= 30
                    cap.set(cv2.CAP_PROP_POS_FRAMES, cnt_frame-90)
                    slider.setValue(cnt_frame-90)
                    label_now.setText("현재 프레임 위치 : " + str(cnt_frame-90))
                    lable_index -= 1
            # ] : ->
            elif e.key() == 93:
                if cnt_frame <= end_frame-60:
                    cnt_frame += 30
                    cap.set(cv2.CAP_PROP_POS_FRAMES, cnt_frame-90)
                    slider.setValue(cnt_frame-90)
                    label_now.setText("현재 프레임 위치 : " + str(cnt_frame-90))
                    lable_index += 1
            # 16777220 : enter
            elif e.key() == 16777220:
                self.update_lable()
                lable_tick_split()
                cnt_frame -= 90
                label_state_input.setText('')
                run(cnt_frame)

        # 48~51 : 0~4
        if e.key() == 48:
            label_state_input.setText('0')
            label_state_input.setStyleSheet('color: green')
        elif e.key() == 49:
            label_state_input.setText('1')
            label_state_input.setStyleSheet('color: black')
        elif e.key() == 50:
            label_state_input.setText('2')
            label_state_input.setStyleSheet('color: blue')
        elif e.key() == 51:
            label_state_input.setText('3')
            label_state_input.setStyleSheet('color: red')
        elif e.key() == 43:
            btn_fast()
        elif e.key() == 45:
            btn_slow()

        # 16777216 : esc
        elif e.key() == 16777216:
            waiting = False
            btn_stop(self)

    def btn_cal(self):
        if self.txt_start.toPlainText() == '':
            print('input frames')
        else:
            self.label_start.setText(str(int(self.txt_start.toPlainText())*30))
            self.label_end.setText(str(int(self.txt_end.toPlainText())*30+120))

    def combobox_Changed(self):
        global video_index
        global x_ticks
        global waiting

        if running:
            print("yet playing video")
            return
        else:
            waiting = False
            btn_stop(self)

            if self.combo_baby.currentText() == '-':
                self.combo_video.clear()
                return

            global baby_num
            baby_num = int(self.combo_baby.currentText()) - 2

            temp = [f for f in os.listdir(path[baby_num]) if os.path.isfile(os.path.join(path[baby_num], f))]

            result = [s for s in temp if extension in s]
            result.sort()

            self.combo_video.clear()
            for i in result:
                self.combo_video.addItem(i)

            video_index = int(self.combo_video.currentIndex())
            f_name = 'baby' + str(baby_num + 2) + '_ticks.txt'
            file = '/home/lkw/PycharmProjects/newborn_video/' + f_name
            df_tick = pd.read_csv(file, sep=',', header=None)
            df_tick.columns = ['xticks']
            x_ticks = df_tick['xticks']
            lable_tick_split()

    def combobox_video_Changed(self):
        global x_ticks
        global video_index
        global waiting

        if running:
            print("yet playing video")
            return
        else:
            waiting = False
            btn_stop(self)

            video_index = int(self.combo_video.currentIndex())

            f_name = 'baby' + str(baby_num + 2) + '_ticks.txt'
            file = '/home/lkw/PycharmProjects/newborn_video/' + f_name
            df_tick = pd.read_csv(file, sep=',', header=None)
            df_tick.columns = ['xticks']
            x_ticks = df_tick['xticks']

    def btn_restart(self):
        executable = sys.executable
        args = sys.argv[:]
        args.insert(0, sys.executable)
        os.execvp(executable, args)

    def btn_search(self):
        global baby_num
        global path_str
        global start_frame
        global end_frame
        global running
        global waiting
        global isStop
        global lable_index
        global cnt_frame

        isStop = False

        if running:
            print("yet playing video")
            return
        elif waiting:
            print("not yet changed")
            return
        elif self.combo_baby.currentText() == '-':
            print("choose video")
            return
        elif self.txt_start.toPlainText() == '':
            print("input frames")
            return

        path_str = path[baby_num] + str(self.combo_video.currentText())
        start_frame = int(self.label_start.text())
        end_frame = int(self.label_end.text())

        lable_index = int(self.txt_start.toPlainText())

        # 슬라이드 바
        self.slider.setMinimum(start_frame)
        self.slider.setMaximum(end_frame)
        self.slider.setValue(start_frame)

        cnt_frame = start_frame
        run(start_frame)


def btn_fast():
    global speed_V

    if speed_V < 8:
        speed_V *= 2
        speed.setText('x' + str(speed_V))


def btn_slow():
    global speed_V

    if speed_V > 0.5:
        speed_V /= 2
        speed.setText('x' + str(speed_V))


def btn_stop(self):
    global running
    global start_frame
    global isfirstSearch
    global isStop
    global cnt_frame

    cnt_frame = 0

    isStop = True
    isfirstSearch = True
    running = False

    self.slider.setValue(0)
    self.label_view.clear()
    self.label_view.setText("이 곳에서 영상이 출력됩니다.")
    state.setStyleSheet("background-color: white; border: 1px solid black;")


def play(img, fps):
    global cnt_frame

    slider.setValue(cnt_frame)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, c = img.shape
    qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap.fromImage(qImg)
    label_view.setPixmap(pixmap)
    QtTest.QTest.qWait(fps / speed_V)


def lable_tick_split():
    global lable_ticks
    global df

    lable_ticks = [0]

    f_name = 'baby' + str(baby_num + 2) + '_kmeans.txt'
    file = '/home/lkw/PycharmProjects/newborn_video/' + f_name

    df = pd.read_csv(file, sep=' ', header=None)
    df.columns = ['frame', 'lable']

    for i in np.arange(1, len(df['frame'])):
        if df['frame'][i - 1] > df['frame'][i]:
            lable_ticks = np.hstack((lable_ticks, i))
    lable_ticks = np.hstack((lable_ticks, len(df['frame'])))


def show_lable():
    global lable_index
    global lable_ticks
    global df
    global video_index

    return df['lable'][lable_index + lable_ticks[video_index]]


def run(_s):
    global running
    global speed_V
    global path_str
    global cnt_frame
    global start_frame
    global end_frame
    global video_index
    global waiting
    global isfirstSearch
    global isStop
    global lable_index
    global cap

    running = True
    waiting = False

    if isfirstSearch:
        isfirstSearch = False
        show_graph(start_frame, end_frame)

    cap = cv2.VideoCapture(path_str)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = int(1000 / fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, cnt_frame)
    label_now.setText("현재 프레임 위치 : " + str(cnt_frame))

    while running:
        ret, img = cap.read()
        if ret:
            cnt_frame += 1
            label_now.setText("현재 프레임 위치 : " + str(cnt_frame))
            label_state.setText(str(show_lable()))
            if show_lable() == 0:
                state.setStyleSheet("background-color: green; border: 1px solid black;")
            elif show_lable() == 1:
                state.setStyleSheet("background-color: black; border: 1px solid black;")
            elif show_lable() == 2:
                state.setStyleSheet("background-color: blue; border: 1px solid black;")
            elif show_lable() == 3:
                state.setStyleSheet("background-color: red; border: 1px solid black;")

            if cnt_frame >= end_frame:
                running = False
                waiting = False
                cnt_frame = 0
                slider.setValue(cnt_frame)
                label_view.clear()
                label_view.setText("이 곳에서 영상이 출력됩니다.")
                break
            else:
                play(img, fps)
                if cnt_frame >= _s + 120:
                    lable_index += 1
                    running = False
                    waiting = True
                    break
        else:
            QtWidgets.QMessageBox.about(myWindow, "Error", "Cannot read frame.")
            print("cannot read frame.")
            break
    cap.release()


def show_graph(s, e):
    global tt
    f_name = 'baby' + str(baby_num + 2) + '_total.txt'
    file = '/home/lkw/PycharmProjects/newborn_video/' + f_name
    df = pd.read_csv(file, sep=',', header=None)
    df.columns = ['timeline', 'frame', 'point', 'x', 'y', 'z']
    time = np.arange(len(df))
    p = df['point']

    # 콤보박스로 선택한 비디오의 시간축을 0~198000... 에서 각각 0~9000 으로 접근할 수 있도록 만들기
    if not (x_ticks[video_index] == x_ticks[len(x_ticks) - 1]):
        tt = time[x_ticks[video_index]:x_ticks[video_index + 1] - 1]
        pp = p[x_ticks[video_index]:x_ticks[video_index + 1] - 1]
    else:
        tt = time[x_ticks[video_index]:]
        pp = p[x_ticks[video_index]:]
    tt = tt - tt[0]

    tt_max = tt.max()
    tt_min = tt.min()
    ttt = np.round((tt - tt_min) / (tt_max - tt_min) * 9000)

    plt.figure(figsize=(9, 1))
    plt.plot(ttt, pp, label='Point Value')
    plt.xlim(s, e)
    # plt.ylim(0,max(pp[s:e]))   # 이걸 넣으면 짧은 컷 그래프가 크게 나옴(ylim값이 작아짐) 근데 기준이 매번 바뀜
    plt.savefig('frame_part.png', bbox_inches='tight')

    qPixmapVar = QPixmap()
    qPixmapVar.load('frame_part.png')
    label_video.setPixmap(qPixmapVar)


if __name__ == "__main__":
    # QApplication : 프로그램을 실행시켜주는 클래스
    QApplication.processEvents()
    app = QApplication(sys.argv)

    # WindowClass  인스턴스 생성
    myWindow = WindowClass()

    speed = myWindow.speed

    label_view = myWindow.label_view
    label_now = myWindow.label_now
    label_sensor = myWindow.label_sensor
    label_video = myWindow.label_video
    label_state = myWindow.label_state
    label_start = myWindow.label_start
    label_end = myWindow.label_end
    label_state_input = myWindow.label_state_input
    state = myWindow.state

    txt_start = myWindow.txt_start
    txt_end = myWindow.txt_end

    slider = myWindow.slider
    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
