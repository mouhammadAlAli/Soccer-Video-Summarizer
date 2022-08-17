import sys

from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QAbstractButton, QApplication, QWidget, QHBoxLayout, QCheckBox


class PicButton(QAbstractButton):
    def __init__(self, pixmap, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap.scaled(101,71)
        self.clicked.connect(self.onClick)
        self.isCheckable()
        self.check = QCheckBox(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()
    def onClick(self):
        print("1111111111111111111")

# app = QApplication(sys.argv)
# window = QWidget()
# layout = QHBoxLayout(window)
#
# button = PicButton(QPixmap("images/Icon.png"))
# check = QCheckBox(button)
# layout.addWidget(button)
#
# window.show()
# sys.exit(app.exec_())


