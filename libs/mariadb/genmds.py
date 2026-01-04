import os, sys
from peewee import MySQLDatabase
from playhouse.reflection import Introspector

# 定义项目根目录并且加入模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 2)))

from libs.enved.enved import Enved

# ----------------- 配置 -----------------
TABLE_PREFIX = Enved.value("DATABASE_PREX")  # 表前缀
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


db = MySQLDatabase(
    Enved.value("DATABASE_NAME"),
    user=Enved.value("DATABASE_USER"),
    password=Enved.value("DATABASE_PASS"),
    host=Enved.value("DATABASE_HOST"),
    port=int(Enved.value("DATABASE_PORT"))
)

# ----------------- 工具函数 -----------------
def get_column_comments():
    """获取字段注释"""
    sql = """
    SELECT TABLE_NAME, COLUMN_NAME, COLUMN_COMMENT
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = %s
    """
    cursor = db.execute_sql(sql, (Enved.value("DATABASE_NAME"),))
    comments = {}
    for table, column, comment in cursor.fetchall():
        comments.setdefault(table, {})[column] = comment
    return comments


def table_to_class_name(table_name: str) -> str:
    """表名 -> 类名（去掉前缀 + 驼峰化）"""
    if TABLE_PREFIX and table_name.startswith(TABLE_PREFIX):
        table_name = table_name[len(TABLE_PREFIX):]
    return "".join(word.capitalize() for word in table_name.split("_"))


def field_to_code(field_obj, field_name):
    """生成 Peewee 字段声明"""
    field_type = type(field_obj).__name__  # CharField, TextField, etc.
    args = []

    if field_type == "CharField" and getattr(field_obj, "max_length", None):
        args.append(f"max_length={field_obj.max_length}")
    if getattr(field_obj, "null", None):
        args.append("null=True")
    if getattr(field_obj, "unique", False):
        args.append("unique=True")
    if getattr(field_obj, "primary_key", False) and field_type != "AutoField":
        args.append("primary_key=True")

    return f"{field_name} = {field_type}({', '.join(args)})"


# ----------------- 生成模型 -----------------
def generate_models():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    introspector = Introspector.from_database(db)
    models = introspector.generate_models()
    comments = get_column_comments()

    class_map = {}

    for table_name, model_class in models.items():
        class_name = table_to_class_name(table_name)
        class_map[class_name] = table_name
        file_name = f"{class_name}.py"
        file_path = os.path.join(MODELS_DIR, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("import os,sys\n")
            f.write("from peewee import *\n")
            f.write(f"\n")
            f.write("# 定义项目根目录并且加入模块搜索路径\n")
            f.write("sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[\"..\"] * 3)))\n")
            f.write(f"\n")
            f.write("from libs.mariadb.BaseModel import BaseModel\n\n")
            f.write(f"class {class_name}(BaseModel):\n")

            for field_name, field_obj in model_class._meta.fields.items():
                if field_name in ("create_time", "update_time"):
                    continue
                line = field_to_code(field_obj, field_name)
                comment = comments.get(table_name, {}).get(field_name, "")
                if comment:
                    line += f"  # {comment}"
                f.write("    " + line + "\n")

            f.write("\n    class Meta:\n")
            f.write(f"        table_name = '{table_name}'\n")

        print(f"✅ 生成模型: {file_path}")

    # 生成 __init__.py
    init_file = os.path.join(MODELS_DIR, "__init__.py")
    with open(init_file, "w", encoding="utf-8") as f:
        for class_name in class_map:
            f.write(f"from .{class_name} import {class_name}\n")
        f.write("\n__all__ = [\n")
        for class_name in class_map:
            f.write(f"    \"{class_name}\",\n")
        f.write("]\n")
    print(f"✅ 生成入口文件: {init_file}")


if __name__ == "__main__":
    generate_models()
