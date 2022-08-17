import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QPushButton, QComboBox, \
QVBoxLayout, QCheckBox, QSlider, QSizePolicy, QStyle
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.uic import loadUi
import sound_based as fSummary
from math import floor



import os

from goal_detect_module.goal_detect_module import Train, Detect, extract_goals

exportedVideo = None

class MainApp(QMainWindow):

    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)
        loadUi("pro.ui", self)
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QtGui.QIcon('images/icon.png'))
        self.final_video = None
        self.filename = ""
        self.duration = ""
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoName = self.findChild(QLabel, "videoName")
        self.videoName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.importBtn = self.findChild(QPushButton, "ImportBtn")
        self.importBtn.clicked.connect(self.open_file)
        self.summarizeBtn = self.findChild(QPushButton, "summarizeBtn")
        self.summarizeBtn.setEnabled(False)
        self.summarizeBtn.clicked.connect(self.summraizeBtnClick)
        self.playBtn = self.findChild(QPushButton, "playBtn")
        self.playBtn.setEnabled(False)
        self.playBtn.clicked.connect(self.play_video)
        self.exportBtn = self.findChild(QPushButton, "exportBtn")
        self.comboBox = self.findChild(QComboBox, 'comboBox')
        self.comboBox.currentIndexChanged.connect(self.comboIndexChanged)
        self.checks = self.findChild(QVBoxLayout, 'verticalLayout')
        self.goal_check = self.findChild(QCheckBox, "goal_check")
        self.attack_check = self.findChild(QCheckBox, "attack_check")
        self.fouls_check = self.findChild(QCheckBox, "fouls_check")
        self.slider = self.findChild(QSlider, "slider")
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        self.videoWidget = self.findChild(QVideoWidget, "videoWidget")
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaPlayer_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        self.comboBox.setEnabled(False)
        self.goal_check.setEnabled(False)
        self.attack_check.setEnabled(False)
        self.fouls_check.setEnabled(False)
        self.exportBtn.setEnabled(False)
        self.exportBtn.clicked.connect(self.exportBtnClick)

    def comboIndexChanged(self):
        idx = self.comboBox.currentIndex()
        if idx == 0:
            self.goal_check.setEnabled(True)
            self.goal_check.setChecked(True)
            self.attack_check.setEnabled(True)
            self.fouls_check.setEnabled(True)

        else:
            self.goal_check.setChecked(False)
            self.attack_check.setChecked(False)
            self.fouls_check.setChecked(False)
            self.goal_check.setEnabled(False)
            self.attack_check.setEnabled(False)
            self.fouls_check.setEnabled(False)


    def open_file(self):

        filename, _ = QFileDialog.getOpenFileName(self, "choose soccer video", "", "*.mp4 *.mkv")

        self.videoName.setText(os.path.basename(filename))
        if filename != '':
            self.filename = filename
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.playBtn.setEnabled(True)
            self.summarizeBtn.setEnabled(True)
            self.summarizeBtn.setStyleSheet("color:#b1b1b1")
            self.summarizeBtn.setText("Summarize")
            self.exportBtn.repaint()
            self.comboBox.setEnabled(True)
            self.goal_check.setEnabled(True)
            self.goal_check.setChecked(True)
            self.attack_check.setEnabled(True)
            self.fouls_check.setEnabled(True)
            self.exportBtn.setStyleSheet("color:#b1b1b1")
            self.exportBtn.setText("Export Video")
            self.exportBtn.repaint()


    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaPlayer_changed(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )

    def convertMillis(self,millis):
        seconds = (millis / 1000) % 60
        minutes = (millis / (1000 * 60)) % 60
        hours = (millis / (1000 * 60 * 60)) % 24

        return str(floor(hours)) + ":" + str(floor(minutes)) + ":" + str(floor(seconds))

    def position_changed(self, position):
        self.videoName.setText(os.path.basename(self.filename) + " " + self.convertMillis(position) + " / " + self.duration)
        self.videoName.repaint()
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.duration = self.convertMillis(duration)
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def summraizeBtnClick(self):
        self.summarizeBtn.setText("Processing...")
        self.summarizeBtn.setStyleSheet("color:rgb(91, 47, 144)")
        self.summarizeBtn.setEnabled(False)
        self.summarizeBtn.repaint()
        idx = self.comboBox.currentIndex()
        if idx == 1:
            final_times, clip = fSummary.quick_summary(self.filename)
            self.final_video = fSummary.extract_summary(final_times, clip)
        if idx == 0:
            if self.goal_check.isChecked():
                trainer =Train(self.filename)
                trainer.train("goal_detect_module/Input/Orig.txt", True)
                detector = Detect("goal_detect_module/Input/Orig.txt")
                goals = detector.detect(self.filename)
                extract_goals(self.filename, goals)
            if self.fouls_check.isChecked():
                pass
        self.summarizeBtn.setStyleSheet("color:rgb(55, 126, 71)")
        self.summarizeBtn.setText("Done")
        self.summarizeBtn.repaint()
        self.exportBtn.setEnabled(True)

    def exportBtnClick(self):
        self.exportBtn.setText("Extracting...")
        self.exportBtn.setStyleSheet("color:rgb(91, 47, 144)")
        self.exportBtn.setEnabled(False)
        self.exportBtn.repaint()
        exportedVideoPath = QFileDialog.getExistingDirectory(self, "Choose Directory", "")
        if exportedVideoPath != '':
            self.exportBtn.setEnabled(False)
            self.final_video.to_videofile(exportedVideoPath + "/Summary of " + os.path.basename(self.filename) + '.mp4')
            self.mediaPlayer.setMedia(QMediaContent(
                QUrl.fromLocalFile(exportedVideoPath + "/Summary of " + os.path.basename(self.filename) + '.mp4')))
            self.videoName.setText("Summary of " + os.path.basename(self.filename))
            self.filename = "Summary of " + os.path.basename(self.filename)
            self.exportBtn.setStyleSheet("color:rgb(55, 126, 71)")
            self.exportBtn.setText("Done")
            self.exportBtn.repaint()
            self.exportBtn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()


