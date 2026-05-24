from PyQt6.QtWidgets import QLayout
from PyQt6.QtCore import Qt, QSize, QRect


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def sizeHint(self):
        return QSize(200, 100)

    def minimumSize(self):
        return QSize(100, 50)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def _do_layout(self, rect, test_only):
        x, y = rect.x(), rect.y()
        line_h = 0
        spacing = self.spacing()
        if spacing < 0: spacing = 4
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() and x > rect.x():
                x = rect.x()
                y += line_h + spacing
                line_h = 0
            if not test_only:
                item.setGeometry(QRect(x, y, hint.width(), hint.height()))
            x += hint.width() + spacing
            line_h = max(line_h, hint.height())
        if test_only:
            return y + line_h - rect.y()
        return 0
