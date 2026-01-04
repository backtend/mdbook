# libs/mariadb/base.py
import os, sys
import time
import pymysql
from peewee import Model, IntegerField, MySQLDatabase, OperationalError

# 定义项目根目录并且加入模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 2)))

from libs.enved.enved import Enved


class ReconnectMySQLDatabase(MySQLDatabase):
    """支持自动重连的 MySQLDatabase"""
    def execute_sql(self, sql, params=None, commit=True):
        try:
            return super().execute_sql(sql, params, commit)
        except OperationalError as e:
            # 常见超时错误码：2006 (MySQL server has gone away), 2013 (Lost connection)
            if e.args[0] in (2006, 2013):
                print(f"[数据库] 检测到连接丢失，正在自动重连...（错误码 {e.args[0]}）")
                self.close()
                self.connect(reuse_if_open=True)
                return super().execute_sql(sql, params, commit)
            raise


# 使用自定义的数据库类
db = ReconnectMySQLDatabase(
    Enved.value("DATABASE_NAME"),
    user=Enved.value("DATABASE_USER"),
    password=Enved.value("DATABASE_PASS"),
    host=Enved.value("DATABASE_HOST"),
    port=int(Enved.value("DATABASE_PORT")),
    charset='utf8mb4'
)


class BaseModel(Model):
    create_time = IntegerField(default=lambda: int(time.time()))
    update_time = IntegerField(default=lambda: int(time.time()))

    class Meta:
        database = db
        legacy_table_names = False

    def save(self, *args, **kwargs):
        self.update_time = int(time.time())
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return super().delete_instance(*args, **kwargs)

    def to_dict(self):
        result = {}
        for t_field in ["create_time", "update_time"]:
            ts = getattr(self, t_field, None)
            if ts:
                result[t_field] = ts
                result[f"{t_field}_str"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        return result


if __name__ == "__main__":
    try:
        db.connect()
        print("数据库连接成功")
    except Exception as e:
        print("数据库连接失败:", e)
    finally:
        db.close()
        print("数据库连接已关闭")
