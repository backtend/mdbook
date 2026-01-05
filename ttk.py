import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import markdown
import os

NOTES_DIR = "notes"


class MarkdownNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Markdown Notes")
        self.geometry("1100x650")

        self.data = {}
        self.current_group = None
        self.current_note = None

        self._init_storage()
        self._create_ui()
        self._load_notes()

    # ================= 存储 =================
    def _init_storage(self):
        os.makedirs(NOTES_DIR, exist_ok=True)

    def _load_notes(self):
        for group in os.listdir(NOTES_DIR):
            group_path = os.path.join(NOTES_DIR, group)
            if not os.path.isdir(group_path):
                continue

            self.data[group] = {}
            self.tree.insert("", tk.END, iid=group, text=group)

            for file in os.listdir(group_path):
                if file.endswith(".md"):
                    note = file[:-3]
                    with open(os.path.join(group_path, file), "r", encoding="utf-8") as f:
                        self.data[group][note] = f.read()

                    self.tree.insert(
                        group, tk.END,
                        iid=f"{group}/{note}",
                        text=note
                    )

    def _save_note_to_file(self, group, note, content):
        path = os.path.join(NOTES_DIR, group)
        os.makedirs(path, exist_ok=True)

        file_path = os.path.join(path, f"{note}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # ================= UI =================
    def _create_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # ===== 左侧 =====
        left_frame = ttk.Frame(paned, width=250)
        paned.add(left_frame, weight=1)

        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="＋ 分组", command=self.add_group).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="＋ 笔记", command=self.add_note).pack(side=tk.LEFT)

        self.tree = ttk.Treeview(left_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ===== 右侧 =====
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        self.note_title = ttk.Label(
            right_frame, text="未选择笔记", font=("Helvetica", 14)
        )
        self.note_title.pack(anchor="w", padx=10, pady=5)

        vertical = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        vertical.pack(fill=tk.BOTH, expand=True)

        # 编辑区
        self.text = tk.Text(
            vertical, wrap=tk.WORD, font=("Menlo", 13), undo=True
        )
        vertical.add(self.text, weight=3)
        self.text.bind("<<Modified>>", self.on_text_change)

        # 预览区
        self.preview = tk.Text(
            vertical,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            bg="#f7f7f7",
            state=tk.DISABLED
        )
        vertical.add(self.preview, weight=2)

    # ================= 逻辑 =================
    def add_group(self):
        name = simpledialog.askstring("新分组", "请输入分组名称")
        if not name or name in self.data:
            return

        self.data[name] = {}
        os.makedirs(os.path.join(NOTES_DIR, name), exist_ok=True)
        self.tree.insert("", tk.END, iid=name, text=name)

    def add_note(self):
        selected = self.tree.selection()
        if not selected:
            return

        group = selected[0]
        if group not in self.data:
            group = self.tree.parent(group)

        name = simpledialog.askstring("新笔记", "请输入笔记名称")
        if not name:
            return

        self.data[group][name] = ""
        self._save_note_to_file(group, name, "")
        self.tree.insert(group, tk.END, iid=f"{group}/{name}", text=name)
        self.tree.item(group, open=True)

    def on_tree_select(self, event):
        self.save_current_note()

        item = self.tree.selection()[0]

        if item in self.data:
            self.current_group = item
            self.current_note = None
            self.note_title.config(text=item)
            self.text.delete("1.0", tk.END)
            self.clear_preview()
            return

        group, note = item.split("/", 1)
        self.current_group = group
        self.current_note = note

        self.note_title.config(text=note)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", self.data[group][note])
        self.update_preview()

    def save_current_note(self):
        if self.current_group and self.current_note:
            content = self.text.get("1.0", tk.END).rstrip()
            self.data[self.current_group][self.current_note] = content
            self._save_note_to_file(self.current_group, self.current_note, content)

    # ================= Markdown =================
    def on_text_change(self, event):
        if self.text.edit_modified():
            self.update_preview()
            self.save_current_note()
            self.text.edit_modified(False)

    def update_preview(self):
        md_text = self.text.get("1.0", tk.END)
        html = markdown.markdown(md_text, extensions=["fenced_code", "tables"])

        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", html.replace("</p>", "\n\n"))
        self.preview.config(state=tk.DISABLED)

    def clear_preview(self):
        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        self.preview.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = MarkdownNotesApp()
    app.mainloop()
