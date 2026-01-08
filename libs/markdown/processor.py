# -*- coding: utf-8 -*-
import re

class MarkdownProcessor:
    """
    Markdown 处理器类
    负责将 Markdown 文本解析为结构化数据
    """
    
    def __init__(self):
        self.patterns = {
            'code_block': re.compile(r'```(?:\w*\n)?(.*?)```', re.DOTALL),
            'heading': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'blockquote': re.compile(r'^>\s*(.*)$', re.MULTILINE),
            'unordered_list': re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE),
            'ordered_list': re.compile(r'^\s*(\d+)\.\s+(.+)$', re.MULTILINE),
            'bold': re.compile(r'\*\*(.+?)\*\*'),
            'italic': re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)'),
            'inline_code': re.compile(r'`(.+?)`'),
            'link': re.compile(r'\[(.*?)\]\((.*?)\)'),
            'image': re.compile(r'!\[(.*?)\]\((.*?)\)'),
            'horizontal_rule': re.compile(r'^[-*_]{3,}$', re.MULTILINE)
        }
    
    def parse(self, text):
        """
        解析 Markdown 文本
        :param text: Markdown 文本
        :return: 解析后的结构化数据
        """
        structure = {
            'headings': [],
            'code_blocks': [],
            'blocks': []
        }
        
        # 提取代码块
        code_blocks = self.patterns['code_block'].findall(text)
        structure['code_blocks'] = code_blocks
        
        # 提取标题
        for match in self.patterns['heading'].finditer(text):
            level = len(match.group(1))
            content = match.group(2).strip()
            structure['headings'].append({
                'level': level,
                'content': content,
                'start': match.start(),
                'end': match.end()
            })
        
        # 解析为块结构
        lines = text.split('\n')
        current_block = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 标题
            heading_match = self.patterns['heading'].match(line)
            if heading_match:
                if current_block:
                    structure['blocks'].append(current_block)
                level = len(heading_match.group(1))
                current_block = {
                    'type': 'heading',
                    'level': level,
                    'content': heading_match.group(2).strip(),
                    'lines': [i]
                }
                continue
            
            # 代码块
            if line.startswith('```'):
                if current_block and current_block['type'] == 'code_block':
                    current_block['lines'].append(i)
                    structure['blocks'].append(current_block)
                    current_block = None
                else:
                    if current_block:
                        structure['blocks'].append(current_block)
                    current_block = {
                        'type': 'code_block',
                        'content': '',
                        'lines': [i]
                    }
                continue
            
            # 引用
            blockquote_match = self.patterns['blockquote'].match(line)
            if blockquote_match:
                if current_block and current_block['type'] == 'blockquote':
                    current_block['content'] += '\n' + blockquote_match.group(1)
                    current_block['lines'].append(i)
                else:
                    if current_block:
                        structure['blocks'].append(current_block)
                    current_block = {
                        'type': 'blockquote',
                        'content': blockquote_match.group(1),
                        'lines': [i]
                    }
                continue
            
            # 无序列表
            ul_match = self.patterns['unordered_list'].match(line)
            if ul_match:
                if current_block and current_block['type'] == 'unordered_list':
                    current_block['items'].append(ul_match.group(1))
                    current_block['lines'].append(i)
                else:
                    if current_block:
                        structure['blocks'].append(current_block)
                    current_block = {
                        'type': 'unordered_list',
                        'items': [ul_match.group(1)],
                        'lines': [i]
                    }
                continue
            
            # 有序列表
            ol_match = self.patterns['ordered_list'].match(line)
            if ol_match:
                if current_block and current_block['type'] == 'ordered_list':
                    current_block['items'].append({
                        'number': ol_match.group(1),
                        'content': ol_match.group(2)
                    })
                    current_block['lines'].append(i)
                else:
                    if current_block:
                        structure['blocks'].append(current_block)
                    current_block = {
                        'type': 'ordered_list',
                        'items': [{
                            'number': ol_match.group(1),
                            'content': ol_match.group(2)
                        }],
                        'lines': [i]
                    }
                continue
            
            # 水平分割线
            hr_match = self.patterns['horizontal_rule'].match(line)
            if hr_match:
                if current_block:
                    structure['blocks'].append(current_block)
                current_block = {
                    'type': 'horizontal_rule',
                    'lines': [i]
                }
                structure['blocks'].append(current_block)
                current_block = None
                continue
            
            # 段落
            if stripped:
                if current_block and current_block['type'] == 'paragraph':
                    current_block['content'] += '\n' + line
                    current_block['lines'].append(i)
                else:
                    if current_block:
                        structure['blocks'].append(current_block)
                    current_block = {
                        'type': 'paragraph',
                        'content': line,
                        'lines': [i]
                    }
            else:
                if current_block:
                    structure['blocks'].append(current_block)
                    current_block = None
        
        if current_block:
            structure['blocks'].append(current_block)
        
        return structure
    
    def extract_inline_elements(self, text):
        """
        提取内联元素（粗体、斜体、链接等）
        :param text: 文本
        :return: 包含内联元素的列表
        """
        elements = []
        
        # 粗体
        for match in self.patterns['bold'].finditer(text):
            elements.append({
                'type': 'bold',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        # 斜体
        for match in self.patterns['italic'].finditer(text):
            elements.append({
                'type': 'italic',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        # 行内代码
        for match in self.patterns['inline_code'].finditer(text):
            elements.append({
                'type': 'inline_code',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        # 链接
        for match in self.patterns['link'].finditer(text):
            elements.append({
                'type': 'link',
                'text': match.group(1),
                'url': match.group(2),
                'start': match.start(),
                'end': match.end()
            })
        
        # 图片
        for match in self.patterns['image'].finditer(text):
            elements.append({
                'type': 'image',
                'alt_text': match.group(1),
                'url': match.group(2),
                'start': match.start(),
                'end': match.end()
            })
        
        return sorted(elements, key=lambda x: x['start'])