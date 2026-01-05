import sys
import re
from PyQt6.QtWidgets import QApplication, QTextEdit, QMainWindow
from PyQt6.QtGui import (
    QTextCharFormat,
    QFont,
    QTextCursor,
    QColor,
)
from PyQt6.QtCore import Qt


class MarkdownEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Menlo", 14))
        self.cursorPositionChanged.connect(self.on_cursor_move)
        self.textChanged.connect(self.apply_styles)

    # ================= 核心 =================
    def apply_styles(self):
        cursor = self.textCursor()
        pos = cursor.position()

        self.blockSignals(True)
        self.selectAll()
        self.setFontWeight(QFont.Weight.Normal)
        self.setFontItalic(False)
        self.setFontPointSize(14)
        self.setTextColor(QColor("black"))
        self.moveCursor(QTextCursor.MoveOperation.End)

        text = self.toPlainText()

        self.apply_headings(text)
        self.apply_inline_styles(text)

        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self.blockSignals(False)

    # ================= 标题 =================
    def apply_headings(self, text):
        for match in re.finditer(r"^(#{1,3})\s+(.*)$", text, re.MULTILINE):
            level = len(match.group(1))
            start = match.start(2)
            length = len(match.group(2))

            cursor = self.textCursor()
            cursor.setPosition(start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                length
            )

            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontPointSize({1: 26, 2: 22, 3: 18}[level])
            cursor.mergeCharFormat(fmt)

    # ================= 粗体 / 斜体 =================
    def apply_inline_styles(self, text):
        # 粗体 **text**
        for m in re.finditer(r"\*\*(.+?)\*\*", text):
            self.format_range(m.start(1), len(m.group(1)), bold=True)

        # 斜体 *text*
        for m in re.finditer(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", text):
            self.format_range(m.start(1), len(m.group(1)), italic=True)

    def format_range(self, start, length, bold=False, italic=False):
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            length
        )

        fmt = QTextCharFormat()
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)

        cursor.mergeCharFormat(fmt)

    # ================= 光标 =================
    def on_cursor_move(self):
        # 目前版本：不隐藏符号，只做样式
        # 真正隐藏符号需要 QTextLayout（进阶）
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Typora-like Markdown Editor")
        self.resize(900, 600)

        self.editor = MarkdownEditor()
        self.setCentralWidget(self.editor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
