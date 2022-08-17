import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QMainWindow, QApplication, QScrollArea, QHBoxLayout, QWidget, QListWidget
from PyQt5.uic import loadUi

from pic_button import PicButton





class ActionBased(QMainWindow):

    def __init__(self, parent=None):
        super(ActionBased, self).__init__(parent)
        QMainWindow.__init__(self)
        loadUi("action_based.ui", self)
        self.init_ui()
    def init_ui(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.goals_scroll_area = self.findChild(QScrollArea, "goals_scroll")
        # wid = Test()
        # self.goals_scroll_area.setWidget(wid)
        #self.goals_scroll_area.rangeChanged.connect(self.r)
    def r(self):
        self.wid.repaint()




def main():
    app = QApplication(sys.argv)
    window = ActionBased()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()