import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


class MarkdownNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Markdown Notes")
        self.geometry("1000x600")

        # ===== 数据结构 =====
        # {
        #   "分组名": {
        #       "笔记名": "内容"
        #   }
        # }
        self.data = {}

        self.current_group = None
        self.current_note = None

        self._create_ui()

    # ================= UI =================
    def _create_ui(self):
        # 主分割区域
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # ===== 左侧 =====
        left_frame = ttk.Frame(paned, width=250)
        paned.add(left_frame, weight=1)

        # 工具栏
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="＋ 分组", command=self.add_group).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="＋ 笔记", command=self.add_note).pack(side=tk.LEFT)

        # TreeView
        self.tree = ttk.Treeview(left_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ===== 右侧 =====
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        # 标题
        self.note_title = ttk.Label(right_frame, text="未选择笔记", font=("Helvetica", 14))
        self.note_title.pack(anchor="w", padx=10, pady=5)

        # 文本编辑区
        self.text = tk.Text(
            right_frame,
            wrap=tk.WORD,
            font=("Menlo", 13),
            undo=True
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ================= 逻辑 =================
    def add_group(self):
        name = simpledialog.askstring("新分组", "请输入分组名称")
        if not name:
            return
        if name in self.data:
            messagebox.showerror("错误", "分组已存在")
            return

        self.data[name] = {}
        self.tree.insert("", tk.END, iid=name, text=name)

    def add_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个分组")
            return

        group = selected[0]
        if group not in self.data:
            group = self.tree.parent(group)

        name = simpledialog.askstring("新笔记", "请输入笔记名称")
        if not name:
            return

        if name in self.data[group]:
            messagebox.showerror("错误", "笔记已存在")
            return

        self.data[group][name] = ""
        self.tree.insert(group, tk.END, iid=f"{group}/{name}", text=name)
        self.tree.item(group, open=True)

    def on_tree_select(self, event):
        self.save_current_note()

        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]

        # 如果点的是分组
        if item in self.data:
            self.current_group = item
            self.current_note = None
            self.note_title.config(text=item)
            self.text.delete("1.0", tk.END)
            return

        # 如果点的是笔记
        group, note = item.split("/", 1)
        self.current_group = group
        self.current_note = note

        self.note_title.config(text=note)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", self.data[group][note])

    def save_current_note(self):
        if self.current_group and self.current_note:
            self.data[self.current_group][self.current_note] = self.text.get("1.0", tk.END).rstrip()


if __name__ == "__main__":
    app = MarkdownNotesApp()
    app.mainloop()
