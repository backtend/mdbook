import sys
import re
from PyQt6.QtWidgets import QApplication, QTextEdit, QMainWindow
from PyQt6.QtGui import (
    QTextCursor,
    QTextCharFormat,
    QFont,
    QColor,
)
from PyQt6.QtCore import Qt


MD_COLOR = QColor("#999999")
CODE_BG = QColor("#f2f2f2")


class MarkdownEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Menlo", 14))
        self.setTabStopDistance(32)

        self.textChanged.connect(self.apply_markdown_styles)

    # ================= 主入口 =================
    def apply_markdown_styles(self):
        cursor = self.textCursor()
        pos = cursor.position()

        self.blockSignals(True)
        self.clear_formatting()

        text = self.toPlainText()

        self.apply_code_blocks(text)
        self.apply_headings(text)
        self.apply_inline(text)

        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self.blockSignals(False)

    # ================= 清理 =================
    def clear_formatting(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)

        fmt = QTextCharFormat()
        fmt.setFont(QFont("Menlo", 14))
        fmt.setForeground(QColor("black"))
        fmt.setBackground(Qt.GlobalColor.transparent)

        cursor.setCharFormat(fmt)

    # ================= B️⃣ 代码块 ``` =================
    def apply_code_blocks(self, text):
        for m in re.finditer(r"```(.*?)```", text, re.DOTALL):
            start = m.start()
            end = m.end()

            cursor = self.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            fmt = QTextCharFormat()
            fmt.setFont(QFont("Menlo", 13))
            fmt.setBackground(CODE_BG)

            cursor.mergeCharFormat(fmt)

            # 弱化 ``` 符号
            self.weak_token(start, 3)
            self.weak_token(end - 3, 3)

    # ================= 标题 =================
    def apply_headings(self, text):
        for m in re.finditer(r"^(#{1,3})\s+", text, re.MULTILINE):
            level = len(m.group(1))

            self.weak_token(m.start(1), level)

            size = {1: 26, 2: 22, 3: 18}[level]
            self.format_range(
                m.end(),
                None,
                size=size,
                bold=True
            )

    # ================= 行内样式 =================
    def apply_inline(self, text):
        # 粗体
        for m in re.finditer(r"\*\*(.+?)\*\*", text):
            self.weak_token(m.start(), 2)
            self.weak_token(m.end() - 2, 2)
            self.format_range(m.start(1), len(m.group(1)), bold=True)

        # 斜体
        for m in re.finditer(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", text):
            self.weak_token(m.start(), 1)
            self.weak_token(m.end() - 1, 1)
            self.format_range(m.start(1), len(m.group(1)), italic=True)

        # 行内代码
        for m in re.finditer(r"`(.+?)`", text):
            self.weak_token(m.start(), 1)
            self.weak_token(m.end() - 1, 1)
            self.format_range(
                m.start(1),
                len(m.group(1)),
                mono=True,
                bg=CODE_BG
            )

    # ================= 工具方法 =================
    def weak_token(self, start, length):
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            length
        )

        fmt = QTextCharFormat()
        fmt.setForeground(MD_COLOR)
        cursor.mergeCharFormat(fmt)

    def format_range(self, start, length, size=None, bold=False, italic=False, mono=False, bg=None):
        cursor = self.textCursor()
        cursor.setPosition(start)

        if length:
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                length
            )
        else:
            cursor.movePosition(
                QTextCursor.MoveOperation.EndOfBlock,
                QTextCursor.MoveMode.KeepAnchor
            )

        fmt = QTextCharFormat()
        if size:
            fmt.setFontPointSize(size)
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        if mono:
            fmt.setFont(QFont("Menlo"))
        if bg:
            fmt.setBackground(bg)

        cursor.mergeCharFormat(fmt)

    # ================= 列表回车 =================
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            block = cursor.block().text()

            if block.strip() == "-":
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                return

            if block.lstrip().startswith("- "):
                super().keyPressEvent(event)
                cursor.insertText("- ")
                return

        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Markdown Editor (Typora Style)")
        self.resize(950, 650)

        self.editor = MarkdownEditor()
        self.setCentralWidget(self.editor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
