# -*- coding: utf-8 -*-
"""
Markdown 渲染器类
负责将解析后的 Markdown 结构转换为其他格式（如 HTML、纯文本等）
"""

class MarkdownRenderer:
    """
    Markdown 渲染器类
    """
    
    def __init__(self):
        pass
    
    def render_html(self, structure, original_text):
        """
        将 Markdown 结构渲染为 HTML
        :param structure: 解析后的 Markdown 结构
        :param original_text: 原始 Markdown 文本
        :return: HTML 文本
        """
        html = ''
        
        for block in structure['blocks']:
            if block['type'] == 'heading':
                html += f'<h{block["level"]}>{block["content"]}</h{block["level"]}>\n'
            
            elif block['type'] == 'code_block':
                # 提取代码块内容
                lines = original_text.split('\n')
                code_content = '\n'.join(lines[block['lines'][0]+1:block['lines'][-1]])
                html += f'<pre><code>{code_content}</code></pre>\n'
            
            elif block['type'] == 'blockquote':
                html += f'<blockquote>{block["content"]}</blockquote>\n'
            
            elif block['type'] == 'unordered_list':
                html += '<ul>\n'
                for item in block['items']:
                    html += f'  <li>{item}</li>\n'
                html += '</ul>\n'
            
            elif block['type'] == 'ordered_list':
                html += '<ol>\n'
                for item in block['items']:
                    html += f'  <li>{item["content"]}</li>\n'
                html += '</ol>\n'
            
            elif block['type'] == 'paragraph':
                # 处理内联元素
                content = self._render_inline_elements(block['content'])
                html += f'<p>{content}</p>\n'
            
            elif block['type'] == 'horizontal_rule':
                html += '<hr>\n'
        
        return html
    
    def render_plain_text(self, structure, original_text):
        """
        将 Markdown 结构渲染为纯文本（去除所有 Markdown 标记）
        :param structure: 解析后的 Markdown 结构
        :param original_text: 原始 Markdown 文本
        :return: 纯文本
        """
        plain_text = ''
        
        for block in structure['blocks']:
            if block['type'] == 'heading':
                plain_text += f'{block["content"]}\n\n'
            
            elif block['type'] == 'code_block':
                # 提取代码块内容
                lines = original_text.split('\n')
                code_content = '\n'.join(lines[block['lines'][0]+1:block['lines'][-1]])
                plain_text += f'{code_content}\n\n'
            
            elif block['type'] == 'blockquote':
                plain_text += f'{block["content"]}\n\n'
            
            elif block['type'] == 'unordered_list':
                for item in block['items']:
                    plain_text += f'- {item}\n'
                plain_text += '\n'
            
            elif block['type'] == 'ordered_list':
                for i, item in enumerate(block['items'], 1):
                    plain_text += f'{i}. {item["content"]}\n'
                plain_text += '\n'
            
            elif block['type'] == 'paragraph':
                # 处理内联元素
                content = self._render_inline_elements_plain(block['content'])
                plain_text += f'{content}\n\n'
            
            elif block['type'] == 'horizontal_rule':
                plain_text += '---\n\n'
        
        return plain_text.strip()
    
    def _render_inline_elements(self, text):
        """
        渲染内联元素为 HTML
        :param text: 包含内联元素的文本
        :return: HTML 文本
        """
        import re
        
        # 链接
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # 图片
        text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', text)
        
        # 粗体
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # 斜体
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # 行内代码
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        return text
    
    def _render_inline_elements_plain(self, text):
        """
        渲染内联元素为纯文本（去除标记）
        :param text: 包含内联元素的文本
        :return: 纯文本
        """
        import re
        
        # 链接
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
        
        # 图片
        text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'\1', text)
        
        # 粗体
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # 斜体
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # 行内代码
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        return text