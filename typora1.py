import sys
import re
from PyQt6.QtWidgets import QApplication, QTextEdit, QMainWindow
from PyQt6.QtGui import (
    QTextCursor,
    QTextCharFormat,
    QFont,
    QColor,
    QTextBlockFormat,
)
from PyQt6.QtCore import Qt


MD_COLOR = QColor("#999999")
CODE_BG = QColor("#f2f2f2")
QUOTE_BG = QColor("#ffdddd")
INDENT_WIDTH = 40


class MarkdownEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Menlo", 14))
        self.setTabStopDistance(32)
        self.document().setIndentWidth(INDENT_WIDTH)

        self.textChanged.connect(self.apply_markdown_styles)

    # ===============================
    # Markdown Rendering (Undo Safe)
    # ===============================
    def apply_markdown_styles(self):
        doc = self.document()
        cursor = self.textCursor()
        pos = cursor.position()

        self.blockSignals(True)
        doc.setUndoRedoEnabled(False)

        self.clear_formatting()

        text = self.toPlainText()
        self.apply_code_blocks(text)
        self.apply_headings(text)
        self.apply_blockquotes()
        self.apply_lists(text)
        self.apply_inline(text)

        doc.setUndoRedoEnabled(True)
        self.blockSignals(False)

        cursor.setPosition(pos)
        self.setTextCursor(cursor)

    def clear_formatting(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)

        char_fmt = QTextCharFormat()
        char_fmt.setFont(QFont("Menlo", 14))
        char_fmt.setForeground(QColor("black"))
        char_fmt.setBackground(Qt.GlobalColor.transparent)

        block_fmt = QTextBlockFormat()
        block_fmt.setIndent(0)
        block_fmt.setLeftMargin(0)

        cursor.setCharFormat(char_fmt)
        cursor.mergeBlockFormat(block_fmt)

    # ===============================
    # Block-level formatting
    # ===============================
    def apply_code_blocks(self, text):
        for m in re.finditer(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL):
            cursor = self.textCursor()
            cursor.setPosition(m.start())
            cursor.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)

            fmt = QTextCharFormat()
            fmt.setFont(QFont("Menlo", 13))
            fmt.setBackground(CODE_BG)
            cursor.mergeCharFormat(fmt)

            self.weak_token(m.start(), 3)
            self.weak_token(m.end() - 3, 3)

    def apply_headings(self, text):
        for m in re.finditer(r"^(#{1,6})\s+", text, re.MULTILINE):
            level = len(m.group(1))
            self.weak_token(m.start(1), level)

            size = {1: 28, 2: 24, 3: 20, 4: 18, 5: 16, 6: 14}[level]
            self.format_range(m.end(), None, size=size, bold=True)

    def apply_blockquotes(self):
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            if text.startswith(">"):
                cursor = QTextCursor(block)

                fmt = QTextBlockFormat()
                fmt.setLeftMargin(20)
                fmt.setBackground(QUOTE_BG)
                cursor.mergeBlockFormat(fmt)

                self.weak_token(block.position(), 1)

                char_fmt = QTextCharFormat()
                char_fmt.setForeground(QColor("#555555"))
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text) - 1)
                cursor.mergeCharFormat(char_fmt)

            block = block.next()

    def apply_lists(self, text):
        for line_num, line in enumerate(text.splitlines()):
            stripped = line.lstrip()
            if stripped.startswith(("- ", "* ", "+ ")) or re.match(r"\d+\.\s", stripped):
                indent = (len(line) - len(stripped)) // 2
                block = self.document().findBlockByLineNumber(line_num)
                cursor = QTextCursor(block)

                fmt = QTextBlockFormat()
                fmt.setIndent(indent + 1)
                cursor.mergeBlockFormat(fmt)

                marker_len = len(stripped.split()[0])
                self.weak_token(block.position() + len(line) - len(stripped), marker_len)

    # ===============================
    # Inline formatting
    # ===============================
    def apply_inline(self, text):
        for m in re.finditer(r"\*\*(.+?)\*\*", text):
            self.weak_token(m.start(), 2)
            self.weak_token(m.end() - 2, 2)
            self.format_range(m.start(1), len(m.group(1)), bold=True)

        for m in re.finditer(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", text):
            self.weak_token(m.start(), 1)
            self.weak_token(m.end() - 1, 1)
            self.format_range(m.start(1), len(m.group(1)), italic=True)

        for m in re.finditer(r"`(.+?)`", text):
            self.weak_token(m.start(), 1)
            self.weak_token(m.end() - 1, 1)
            self.format_range(m.start(1), len(m.group(1)), mono=True, bg=CODE_BG)

    # ===============================
    # Helpers
    # ===============================
    def weak_token(self, start, length):
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)

        fmt = QTextCharFormat()
        fmt.setForeground(MD_COLOR)
        cursor.mergeCharFormat(fmt)

    def format_range(self, start, length, size=None, bold=False, italic=False, mono=False, bg=None):
        cursor = self.textCursor()
        cursor.setPosition(start)
        if length:
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)

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

    # ===============================
    # Keyboard behavior
    # ===============================
    def keyPressEvent(self, event):
        # Shift+Enter → soft break
        if event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            text = cursor.block().text().rstrip()

            # Exit empty list
            if text in ("- ", "* ", "+ "):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                return

            prefix = None
            if text.startswith(("- ", "* ", "+ ")):
                prefix = text[:2]
            else:
                m = re.match(r"(\d+)\.\s", text)
                if m:
                    prefix = f"{int(m.group(1)) + 1}. "

            super().keyPressEvent(event)

            cursor = self.textCursor()
            if prefix:
                cursor.insertText(prefix)
            return

        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Markdown Editor (Typora-style)")
        self.resize(950, 650)
        self.setCentralWidget(MarkdownEditor())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
