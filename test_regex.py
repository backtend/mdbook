#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：直接测试MarkdownHelper中的正则表达式转换函数
用于定位正则表达式错误
"""

import re
from helpers.MarkdownHelper import MarkdownHelper

# 测试数据
test_data = """
# 标题 1
这是一个**粗体**文本和*斜体*文本

> 这是一个引用

- 无序列表项1
- 无序列表项2

1. 有序列表项1
2. 有序列表项2

这是一个普通段落

```python
# 代码块
print("Hello World")
```
"""

print("=== 测试MarkdownHelper.markdown_to_html ===")
try:
    result = MarkdownHelper.markdown_to_html(test_data)
    print("✅ 转换成功")
    print("结果:")
    print(result)
except Exception as e:
    print(f"❌ 转换失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 单独测试段落正则表达式 ===")
try:
    # 测试段落正则表达式
    html = "测试段落"
    result = re.sub(r'^(?!<h|<pre|<blockquote|<ul|<ol)(.*)$', r'<p>\1</p>', html, flags=re.MULTILINE)
    print(f"✅ 段落转换成功: {result}")
except Exception as e:
    print(f"❌ 段落转换失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试所有正则表达式模式 ===")
patterns_to_test = [
    ('code_blocks', r'```(?:\w*\n)?(.*?)```'),
    ('headings', r'^(#{1,6})\s+'),
    ('blockquotes', r'^>(.*)$'),
    ('unordered_lists', r'^\s*[-*+]\s+(.*)$'),
    ('ordered_lists', r'^\s*(\d+)\.\s+(.*)$'),
    ('bold', r'\*\*(.+?)\*\*'),
    ('italic', r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)'),
    ('inline_code', r'`(.+?)`'),
    ('links', r'\[(.*?)\]\((.*?)\)'),
    ('images', r'!\[(.*?)\]\((.*?)\)'),
    ('paragraph', r'^(?!<h|<pre|<blockquote|<ul|<ol)(.*)$')
]

for name, pattern in patterns_to_test:
    try:
        # 编译正则表达式
        compiled = re.compile(pattern, re.DOTALL | re.MULTILINE)
        print(f"✅ {name} 编译成功")
        
        # 测试匹配
        if compiled.search(test_data):
            print(f"   匹配成功")
        else:
            print(f"   没有匹配项")
    except Exception as e:
        print(f"❌ {name} 失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
