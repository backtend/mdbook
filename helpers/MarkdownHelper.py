# -*- coding: utf-8 -*-
import re
from PyQt6.QtGui import QColor, QFont

class MarkdownHelper:
    """
    Markdown 解析和渲染辅助类
    提供 Markdown 语法的解析、格式化和转换功能
    """
    
    # Markdown 语法正则表达式
    PATTERNS = {
        'code_blocks': r'```(?:\w*\n)?(.*?)```',
        'headings': r'^(#{1,6})\s+',
        'blockquotes': r'^>.*$',
        'unordered_lists': r'^\s*[-*+]\s+',
        'ordered_lists': r'^\s*\d+\.\s+',
        'bold': r'\*\*(.+?)\*\*',
        'italic': r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',
        'inline_code': r'`(.+?)`',
        'links': r'\[(.*?)\]\((.*?)\)',
        'images': r'!\[(.*?)\]\((.*?)\)'
    }
    
    @staticmethod
    def extract_code_blocks(text):
        """
        提取文本中的所有代码块
        :param text: Markdown 文本
        :return: 包含所有代码块的列表
        """
        return re.findall(MarkdownHelper.PATTERNS['code_blocks'], text, re.DOTALL)
    
    @staticmethod
    def extract_headings(text):
        """
        提取文本中的所有标题
        :param text: Markdown 文本
        :return: 包含所有标题的列表，每个元素是 (标题级别, 标题内容) 的元组
        """
        headings = []
        lines = text.split('\n')
        for line in lines:
            match = re.match(MarkdownHelper.PATTERNS['headings'], line)
            if match:
                level = len(match.group(1))
                content = line[match.end():].strip()
                headings.append((level, content))
        return headings
    
    @staticmethod
    def markdown_to_html(markdown_text):
        """
        将 Markdown 文本转换为简单的 HTML
        用于实时预览功能
        :param markdown_text: Markdown 文本
        :return: HTML 文本
        """
        html = markdown_text
        
        # 代码块
        html = re.sub(
            MarkdownHelper.PATTERNS['code_blocks'], 
            r'<pre><code>\1</code></pre>', 
            html, 
            flags=re.DOTALL
        )
        
        # 标题
        for i in range(6, 0, -1):
            html = re.sub(
                rf'^#{{{i}}}\s+(.+)$', 
                rf'<h{i}>\1</h{i}>', 
                html, 
                flags=re.MULTILINE
            )
        
        # 引用
        html = re.sub(
            r'^>(.*)$', 
            r'<blockquote>\1</blockquote>', 
            html, 
            flags=re.MULTILINE
        )
        
        # 无序列表
        html = re.sub(
            r'^\s*[-*+]\s+(.*)$', 
            r'<ul><li>\1</li></ul>', 
            html, 
            flags=re.MULTILINE
        )
        
        # 有序列表
        html = re.sub(
            r'^\s*(\d+)\.\s+(.*)$', 
            r'<ol><li>\2</li></ol>', 
            html, 
            flags=re.MULTILINE
        )
        
        # 粗体
        html = re.sub(MarkdownHelper.PATTERNS['bold'], r'<strong>\1</strong>', html)
        
        # 斜体
        html = re.sub(MarkdownHelper.PATTERNS['italic'], r'<em>\1</em>', html)
        
        # 行内代码
        html = re.sub(MarkdownHelper.PATTERNS['inline_code'], r'<code>\1</code>', html)
        
        # 链接
        html = re.sub(MarkdownHelper.PATTERNS['links'], r'<a href="\2">\1</a>', html)
        
        # 图片
        html = re.sub(MarkdownHelper.PATTERNS['images'], r'<img src="\2" alt="\1">', html)
        
        # 段落
        html = re.sub(r'^(?!<h|<pre|<blockquote|<ul|<ol)(.*)$', r'<p>\1</p>', html, flags=re.MULTILINE)
        
        # 换行
        html = html.replace('\n', '<br>')
        
        return html
    
    @staticmethod
    def validate_markdown(text):
        """
        验证 Markdown 文本的语法
        :param text: Markdown 文本
        :return: 包含错误信息的列表，如果没有错误则返回空列表
        """
        errors = []
        
        # 检查未闭合的代码块
        code_block_starts = len(re.findall(r'```', text))
        if code_block_starts % 2 != 0:
            errors.append('未闭合的代码块')
        
        # 检查未闭合的粗体标记
        bold_marks = len(re.findall(r'\*\*', text))
        if bold_marks % 2 != 0:
            errors.append('未闭合的粗体标记')
        
        # 检查未闭合的斜体标记
        italic_marks = len(re.findall(r'(?<!\*)\*(?!\*)', text))
        if italic_marks % 2 != 0:
            errors.append('未闭合的斜体标记')
        
        # 检查未闭合的行内代码标记
        inline_code_marks = len(re.findall(r'`', text))
        if inline_code_marks % 2 != 0:
            errors.append('未闭合的行内代码标记')
        
        return errors