import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QTextEdit, QMainWindow, QMenuBar, QMenu,
    QFileDialog, QSplitter, QTextBrowser, QMessageBox, QToolBar
)
from PyQt6.QtGui import (QAction, 
    QTextCursor, QTextCharFormat, QFont, QColor, QTextBlockFormat, QKeyEvent,
    QIcon, QPixmap
)
from PyQt6.QtCore import Qt, QUrl

from helpers.FileHelper import FileHelper
from helpers.MarkdownHelper import MarkdownHelper
from libs.markdown import MarkdownProcessor, MarkdownRenderer

# =======================
# 配置常量
# =======================
class Config:
    FONT_FAMILY = "Menlo"
    FONT_SIZE = 14
    MD_COLOR = QColor("#999999")       # Markdown 标签颜色
    CODE_BG = QColor("#f6f8fa")         # 代码块背景色，更接近Typora
    CODE_BORDER = QColor("#e1e4e8")     # 代码块边框色
    QUOTE_BG = QColor("#f8f9fa")        # 引用背景色，更接近Typora
    QUOTE_BORDER = QColor("#dfe2e5")     # 引用边框色
    INDENT_WIDTH = 40
    HEADER_COLORS = {                     # 标题颜色
        1: QColor("#24292e"),
        2: QColor("#24292e"),
        3: QColor("#24292e"),
        4: QColor("#24292e"),
        5: QColor("#586069"),
        6: QColor("#586069")
    }
    LINK_COLOR = QColor("#0366d6")       # 链接颜色
    LIST_MARGIN = 20                      # 列表缩进
    CODE_INLINE_BG = QColor("#f1f3f4")   # 行内代码背景色

    SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE = True  # 标签默认隐藏，光标所在行显示

    HEADER_SIZES = {1: 28, 2: 24, 3: 20, 4: 18, 5: 16, 6: 14}  # H1~H6大小映射


class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont(Config.FONT_FAMILY, Config.FONT_SIZE))
        self.setTabStopDistance(32)
        self.document().setIndentWidth(Config.INDENT_WIDTH)
        self.textChanged.connect(self.apply_markdown_styles)
        self.current_file = None
        self.hover_pos = None  # 鼠标悬停位置

    # ===============================
    # 核心 Markdown 样式应用（Undo 安全）
    # ===============================
    def apply_markdown_styles(self):
        cursor = self.textCursor()
        pos = cursor.position()
        
        # 保存当前状态
        doc = self.document()
        original_modified = doc.isModified()
        
        # 关闭 Undo/Redo 防止样式操作被记录
        doc.setUndoRedoEnabled(False)

        # 清除所有格式
        self.clear_formatting()

        text = self.toPlainText()
        
        # 应用所有样式
        self.apply_code_blocks(text)
        self.apply_headings(text)
        self.apply_blockquotes()
        self.apply_lists(text)
        self.apply_inline(text)

        # 重新开启 Undo/Redo
        doc.setUndoRedoEnabled(True)
        
        # 恢复原始修改状态
        doc.setModified(original_modified)

        # 恢复光标位置
        cursor.setPosition(pos)
        self.setTextCursor(cursor)

    def clear_formatting(self):
        # 使用临时光标清除格式，避免影响当前光标和撤销栈
        cursor = QTextCursor(self.document())
        # 设置光标位置到文档开始，然后选择整个文档
        cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)

        char_fmt = QTextCharFormat()
        char_fmt.setFont(QFont(Config.FONT_FAMILY, Config.FONT_SIZE))
        char_fmt.setForeground(QColor("black"))
        char_fmt.setBackground(QColor("transparent"))

        block_fmt = QTextBlockFormat()
        block_fmt.setIndent(0)
        block_fmt.setLeftMargin(0)

        cursor.setCharFormat(char_fmt)
        cursor.mergeBlockFormat(block_fmt)

    # ===============================
    # Block-level formatting
    # ===============================
    def apply_code_blocks(self, text):
        # 使用正则表达式查找所有代码块
        code_block_pattern = r"```(?:\w*\n)?(.*?)```"
        matches = list(re.finditer(code_block_pattern, text, re.DOTALL))
        
        # 从后往前处理，避免位置偏移问题
        for m in reversed(matches):
            start = m.start()
            end = m.end()
            
            # 使用临时光标进行代码块格式化
            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            # 设置代码块背景和边框
            fmt = QTextCharFormat()
            fmt.setFont(QFont(Config.FONT_FAMILY, Config.FONT_SIZE - 1))  # 代码字体稍小
            fmt.setBackground(Config.CODE_BG)
            cursor.mergeCharFormat(fmt)

            # 隐藏代码块标记
            self.weak_token(start, 3)
            self.weak_token(end - 3, 3)

    def apply_headings(self, text):
        cursor_block = self.textCursor().block() if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE else None
        for m in re.finditer(r"^(#{1,6})\s+", text, re.MULTILINE):
            level = len(m.group(1))
            # 隐藏 Markdown # 标签
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block_num = self.document().findBlock(m.start()).blockNumber()
                show_tags = (cursor_block.blockNumber() == block_num)
            self.weak_token(m.start(1), level, show_tags=show_tags)

            # 应用标题样式
            size = Config.HEADER_SIZES.get(level, Config.FONT_SIZE)
            color = Config.HEADER_COLORS.get(level, QColor("black"))
            self.format_range(m.end(), None, size=size, bold=True, color=color)

    def apply_blockquotes(self):
        cursor_block = self.textCursor().block() if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE else None
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                show_tags = (cursor_block == block)

            if text.startswith(">"):
                cursor = QTextCursor(block)
                fmt = QTextBlockFormat()
                fmt.setLeftMargin(20)
                fmt.setBackground(Config.QUOTE_BG)
                cursor.mergeBlockFormat(fmt)

                self.weak_token(block.position(), 1, show_tags=show_tags)

                char_fmt = QTextCharFormat()
                char_fmt.setForeground(QColor("#6a737d"))
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text) - 1)
                cursor.mergeCharFormat(char_fmt)

            block = block.next()

    def apply_lists(self, text):
        cursor_block = self.textCursor().block() if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE else None
        lines = text.splitlines()
        
        # 使用文档块而不是行号来处理，更可靠
        block = self.document().firstBlock()
        line_num = 0
        
        while block.isValid() and line_num < len(lines):
            line = lines[line_num]
            stripped = line.lstrip()
            
            if stripped.startswith(("- ", "* ", "+ ")) or re.match(r"\d+\.\s", stripped):
                cursor = QTextCursor(block)

                fmt = QTextBlockFormat()
                indent = (len(line) - len(stripped)) // 2
                fmt.setIndent(indent + 1)
                fmt.setLeftMargin(Config.LIST_MARGIN)
                cursor.mergeBlockFormat(fmt)

                show_tags = True
                if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                    show_tags = (cursor_block == block)

                marker_len = len(stripped.split()[0])
                self.weak_token(block.position() + len(line) - len(stripped), marker_len, show_tags=show_tags)
            
            block = block.next()
            line_num += 1

    # ===============================
    # Inline formatting
    # ===============================
    def apply_inline(self, text):
        cursor_block = self.textCursor().block() if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE else None

        # **bold**
        for m in re.finditer(r"\*\*(.+?)\*\*", text):
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block = self.document().findBlock(m.start())
                show_tags = (cursor_block == block)
            self.weak_token(m.start(), 2, show_tags)
            self.weak_token(m.end() - 2, 2, show_tags)
            self.format_range(m.start(1), len(m.group(1)), bold=True)

        # *italic*
        for m in re.finditer(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", text):
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block = self.document().findBlock(m.start())
                show_tags = (cursor_block == block)
            self.weak_token(m.start(), 1, show_tags)
            self.weak_token(m.end() - 1, 1, show_tags)
            self.format_range(m.start(1), len(m.group(1)), italic=True)

        # `inline code`
        for m in re.finditer(r"`(.+?)`", text):
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block = self.document().findBlock(m.start())
                show_tags = (cursor_block == block)
            self.weak_token(m.start(), 1, show_tags)
            self.weak_token(m.end() - 1, 1, show_tags)
            self.format_range(m.start(1), len(m.group(1)), mono=True, bg=Config.CODE_INLINE_BG)

        # [links]
        for m in re.finditer(r"\[(.*?)\]\((.*?)\)", text):
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block = self.document().findBlock(m.start())
                show_tags = (cursor_block == block)
            self.weak_token(m.start(), 1, show_tags)
            self.weak_token(m.start() + len(m.group(1)) + 1, 2, show_tags)
            # 链接文本显示为蓝色并带下划线，更接近Typora效果
            link_fmt = QTextCharFormat()
            link_fmt.setForeground(Config.LINK_COLOR)
            link_fmt.setFontUnderline(True)
            # 使用临时创建的光标，避免影响用户当前光标位置
            cursor = QTextCursor(self.document())
            cursor.setPosition(m.start(1))
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(m.group(1)))
            cursor.mergeCharFormat(link_fmt)
            # 隐藏URL部分
            url_start = m.start() + len(m.group(1)) + 2
            url_end = m.end() - 1
            if url_start < url_end:
                self.weak_token(url_start, url_end - url_start, show_tags=False)
        
        # ![images]
        for m in re.finditer(r"!\[(.*?)\]\((.*?)\)", text):
            show_tags = True
            if Config.SHOW_MD_TAGS_ONLY_ON_CURSOR_LINE and cursor_block:
                block = self.document().findBlock(m.start())
                show_tags = (cursor_block == block)
            # 隐藏图片标记
            self.weak_token(m.start(), m.end() - m.start(), show_tags=False)
            # 显示图片alt文本，并用特殊样式标记
            alt_fmt = QTextCharFormat()
            alt_fmt.setForeground(QColor("#666666"))
            alt_fmt.setFontStyleHint(QFont.StyleHint.Italic)
            alt_fmt.setBackground(QColor("#f0f0f0"))
            alt_fmt.setFontUnderline(True)
            # 使用临时创建的光标，避免影响用户当前光标位置
            cursor = QTextCursor(self.document())
            cursor.setPosition(m.start(1))
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(m.group(1)))
            cursor.mergeCharFormat(alt_fmt)

    # ===============================
    # Helpers
    # ===============================
    def weak_token(self, start, length, show_tags=True):
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)

        fmt = QTextCharFormat()
        
        # 检查鼠标是否悬停在当前位置
        hover_over_tag = False
        if self.hover_pos is not None:
            hover_over_tag = start <= self.hover_pos < start + length
        
        # 如果标签应该显示或者鼠标悬停在标签上，显示标签
        if show_tags or hover_over_tag:
            fmt.setForeground(Config.MD_COLOR)
        else:
            fmt.setForeground(self.palette().base().color())  # 隐藏标签，使其颜色与背景一致

        cursor.mergeCharFormat(fmt)

    def format_range(self, start, length, size=None, bold=False, italic=False, mono=False, bg=None, color=None):
        cursor = self.textCursor()
        cursor.setPosition(start)
        if length:
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)

        fmt = QTextCharFormat()
        font = QFont(Config.FONT_FAMILY)
        if size:
            font.setPointSize(size)
        if bold:
            font.setWeight(QFont.Weight.Bold)
        if italic:
            font.setItalic(True)
        if mono:
            font.setFamily(Config.FONT_FAMILY)
        fmt.setFont(font)
        if bg:
            fmt.setBackground(bg)
        if color:
            fmt.setForeground(color)

        cursor.mergeCharFormat(fmt)

    # ===============================
    # File operations
    # ===============================
    def new_file(self):
        self.clear()
        self.current_file = None
        self.parent().setWindowTitle("PyQt Markdown Editor (Typora-style) - Untitled")

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Markdown File", "", "Markdown Files (*.md *.markdown);;All Files (*)"
            )

        if file_path:
            content = FileHelper.read_file(file_path)
            if content:
                self.blockSignals(True)
                self.setPlainText(content)
                self.blockSignals(False)
                self.current_file = file_path
                self.parent().setWindowTitle(f"PyQt Markdown Editor (Typora-style) - {FileHelper.get_file_name(file_path)}")
                self.apply_markdown_styles()

    def save_file(self, file_path=None):
        if not file_path and not self.current_file:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Markdown File", "", "Markdown Files (*.md *.markdown);;All Files (*)"
            )

        if file_path:
            content = self.toPlainText()
            if FileHelper.write_file(file_path, content):
                self.current_file = file_path
                self.parent().setWindowTitle(f"PyQt Markdown Editor (Typora-style) - {FileHelper.get_file_name(file_path)}")
                return True
        elif self.current_file:
            content = self.toPlainText()
            if FileHelper.write_file(self.current_file, content):
                return True
        return False

    def export_to_html(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML", "", "HTML Files (*.html);;All Files (*)"
        )

        if file_path:
            content = self.toPlainText()
            html = MarkdownHelper.markdown_to_html(content)
            if FileHelper.write_file(file_path, html):
                return True
        return False

    # ===============================
    # Key behavior
    # ===============================
    def keyPressEvent(self, event: QKeyEvent):
        cursor = self.textCursor()
        text = cursor.block().text().rstrip()
        
        # 自动补全括号、引号等
        char = event.text()
        if char and self.auto_complete(char):
            return

        # Shift+Enter → soft break
        if event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            super().keyPressEvent(event)
            return

        # Enter → 自动列表续行和多行换行支持
        if event.key() == Qt.Key.Key_Return:
            # 空列表退出
            if text.strip() in ("- ", "* ", "+ "):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                return
            
            # 正常情况下直接换行，支持多行连续换行
            super().keyPressEvent(event)
            
            # 如果是列表项，添加续行
            prefix = None
            if text.startswith(("- ", "* ", "+ ")):
                prefix = text[:2]
            else:
                m = re.match(r"^(\d+)\.\s", text)
                if m:
                    prefix = f"{int(m.group(1)) + 1}. "
            
            if prefix:
                cursor = self.textCursor()
                cursor.insertText(prefix)
            return

        # 快捷键：Ctrl+B → 粗体
        if event.key() == Qt.Key.Key_B and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.apply_formatting("**")
            return

        # 快捷键：Ctrl+I → 斜体
        if event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.apply_formatting("*")
            return

        # 快捷键：Ctrl+K → 代码块
        if event.key() == Qt.Key.Key_K and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.apply_formatting("```\n", "\n```")
            return
        
        # 快捷键：Ctrl+L → 插入链接
        if event.key() == Qt.Key.Key_L and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.apply_formatting("[", "](url)")
            return
        
        # 快捷键：Ctrl+Shift+I → 插入图片
        if event.key() == Qt.Key.Key_I and event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.apply_formatting("![", "]")
            return
        
        # 快捷键：Ctrl+Shift+` → 插入行内代码
        if event.key() == Qt.Key.Key_QuoteLeft and event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.apply_formatting("`")
            return

        super().keyPressEvent(event)

    def apply_formatting(self, prefix, suffix=""):
        cursor = self.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            # 为选中文本添加格式
            cursor.insertText(f"{prefix}{selected_text}{suffix}")
        else:
            # 插入格式标记并将光标置于中间
            cursor.insertText(f"{prefix}{suffix}")
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=suffix)
            self.setTextCursor(cursor)

        self.apply_markdown_styles()

    # 粘贴自动格式化
    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.apply_markdown_styles()
    
    # ===============================
    # 鼠标事件处理（用于悬停显示标签）
    # ===============================
    def mouseMoveEvent(self, event):
        """跟踪鼠标位置，用于显示悬停的Markdown标签"""
        pos = self.cursorForPosition(event.pos()).position()
        if self.hover_pos != pos:
            self.hover_pos = pos
            self.apply_markdown_styles()
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标离开时隐藏悬停效果"""
        self.hover_pos = None
        self.apply_markdown_styles()
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开编辑区域时隐藏悬停效果"""
        self.hover_pos = None
        self.apply_markdown_styles()
        super().leaveEvent(event)
    
    # ===============================
    # Auto-completion
    # ===============================
    def auto_complete(self, char):
        """自动补全Markdown语法"""
        cursor = self.textCursor()
        text = cursor.document().toPlainText()
        pos = cursor.position()
        
        # 自动补全括号、引号等
        pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
            "\"": "\"",
            "'": "'",
            "`": "`",
        }
        
        if char in pairs:
            # 检查是否在单词中，如果是，则不自动补全
            if pos > 0 and text[pos-1].isalnum():
                return False
            
            cursor.insertText(char + pairs[char])
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return True
        
        return False


class MarkdownPreview(QTextBrowser):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.editor.textChanged.connect(self.update_preview)
        self.setOpenExternalLinks(True)

    def update_preview(self):
        text = self.editor.toPlainText()
        html = MarkdownHelper.markdown_to_html(text)
        self.setHtml(html)


# ===============================
# 主窗口
# ===============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Markdown Editor (Typora-style) - Untitled")
        self.resize(1200, 800)

        # 创建编辑器
        self.editor = MarkdownEditor(self)
        self.setCentralWidget(self.editor)

        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # 文件菜单
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.editor.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.editor.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.editor.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(lambda: self.editor.save_file(None))
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_action = QAction("Export to HTML", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.editor.export_to_html)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = QMenu("Edit", self)
        menu_bar.addMenu(edit_menu)

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # 格式菜单
        format_menu = QMenu("Format", self)
        menu_bar.addMenu(format_menu)

        bold_action = QAction("Bold", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.editor.apply_formatting("**"))
        format_menu.addAction(bold_action)

        italic_action = QAction("Italic", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.editor.apply_formatting("*"))
        format_menu.addAction(italic_action)

        code_action = QAction("Code Block", self)
        code_action.setShortcut("Ctrl+K")
        code_action.triggered.connect(lambda: self.editor.apply_formatting("```\n", "\n```"))
        format_menu.addAction(code_action)

        format_menu.addSeparator()

        for i in range(1, 7):
            header_action = QAction(f"Heading {i}", self)
            header_action.setShortcut(f"Ctrl+{i}")
            header_action.triggered.connect(lambda checked, level=i: self.editor.apply_formatting(f"{'#'*level} "))
            format_menu.addAction(header_action)

    def create_tool_bar(self):
        tool_bar = QToolBar("Main Toolbar", self)
        self.addToolBar(tool_bar)

        tool_bar.addAction("New", self.editor.new_file)
        tool_bar.addAction("Open", self.editor.open_file)
        tool_bar.addAction("Save", self.editor.save_file)
        tool_bar.addSeparator()
        tool_bar.addAction("Bold", lambda: self.editor.apply_formatting("**"))
        tool_bar.addAction("Italic", lambda: self.editor.apply_formatting("*"))
        tool_bar.addAction("Code", lambda: self.editor.apply_formatting("```\n", "\n```"))

    def closeEvent(self, event):
        # 移除退出确认对话框，方便调试
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
