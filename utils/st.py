import random
import sqlite3

"""

.st 属性录入

用法：.st (del/clr/show) \[属性名] [属性值]	//将属性录入当前绑定卡 .st力量:50 体质:55 体型:65 敏捷:45 外貌:70 智力:75 意志:35 教育:65 幸运:75

    .st hp-1	//+/-开头时，视为基于原值修改
    .st san+1D6
    .st &沙漠之鹰=1D10+1D6+3 以&开头录入掷骰表达式，可被掷骰指令直接调用
    .st del kp裁决	//删除已保存的属性
    .st clr	//清空人物卡
    .st show 灵感	//查看指定人物属性
    .st show //无参数时查看所有属性（不含默认值技能），请使用只st加点过技能的半自动人物卡！ //部分COC属性会被视为同义词，如智力/灵感、理智/san、侦查/侦察


sqlite3数据库：
                self.conn.execute('''
                                CREATE TABLE IF NOT EXISTS users 
                                (user_id INTEGER, 
                                slot_id INTEGER, 
                                name TEXT, 
                                str INTEGER, 
                                con INTEGER, 
                                siz INTEGER, 
                                dex INTEGER, 
                                app INTEGER, 
                                int INTEGER, 
                                pow INTEGER, 
                                edu INTEGER, 
                                luk INTEGER,
                                PRIMARY KEY (user_id, slot_id))''')
                self.conn.execute('''
                                CREATE TABLE IF NOT EXISTS status
                                (user_id INTEGER, 
                                slot_id INTEGER, 
                                hp INTEGER, 
                                mp INTEGER, 
                                dmg TEXT,
                                def TEXT, 
                                san INTEGER,
                                PRIMARY KEY (user_id, slot_id))''')
                self.conn.execute('''
                                CREATE TABLE IF NOT EXISTS skills
                                (user_id INTEGER,
                                slot_id INTEGER,
                                skillname TEXT, 
                                expression TEXT,
                                PRIMARY KEY (user_id, slot_id, skillname))''')

"""

def register_function(jrpg_functions, sqlite_conn):
    StatusRecord_instance = StatusRecord(sqlite_conn)
    jrpg_functions['st'] = StatusRecord_instance.st


class StatusRecord:
    sqlite_conn = None

    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn

    async def st(self, args, userslot, sender_user_id, group_id):
        if isinstance(args, list):
            args = ' '.join(args)

        args = args.strip()

        slot_id = userslot.get(sender_user_id)

        # 解析命令
        parts = args.split()
        command = parts[0].lower() if parts else ''
        attribute = parts[1].lower() if len(parts) > 1 else ''
        value = parts[2] if len(parts) > 2 else ''

        cursor = self.sqlite_conn.cursor()

        if command == 'del':
            # 删除属性
            if attribute.startswith('&'):
                cursor.execute("DELETE FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute[1:]))
            else:
                cursor.execute("DELETE FROM users WHERE user_id = ? AND slot_id = ? AND name = ?", (sender_user_id, slot_id, attribute))
            self.sqlite_conn.commit()
            return f"已删除属性 {attribute}"

        elif command == 'clr':
            # 清空人物卡
            cursor.execute("DELETE FROM users WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
            cursor.execute("DELETE FROM status WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
            cursor.execute("DELETE FROM skills WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
            self.sqlite_conn.commit()
            return "已清空人物卡"

        elif command == 'show':
            # 查看属性
            if attribute:
                if attribute.startswith('&'):
                    cursor.execute("SELECT expression FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute[1:]))
                    result = cursor.fetchone()
                    if result:
                        return f"{attribute}: {result[0]}"
                    else:
                        return f"未找到属性 {attribute}"
                else:
                    cursor.execute("SELECT * FROM users WHERE user_id = ? AND slot_id = ? AND name = ?", (sender_user_id, slot_id, attribute))
                    result = cursor.fetchone()
                    if result:
                        columns = [col[0] for col in cursor.description]
                        attributes = dict(zip(columns, result))
                        return f"{attribute}: {attributes[attribute]}"
                    else:
                        return f"未找到属性 {attribute}"
            else:
                cursor.execute("SELECT * FROM users WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
                results = cursor.fetchall()
                if results:
                    columns = [col[0] for col in cursor.description]
                    attributes = [dict(zip(columns, result)) for result in results]
                    return f"人物卡属性: {attributes}"
                else:
                    return "未找到任何属性"
        
        elif '|' in args:
            # 多属性录入
            attributes = args.split('|')
            for attribute in attributes:
                await self.st(attribute, userslot, sender_user_id, group_id)
            return f"已完成 {len(attributes)} 个属性录入"
        
        elif '=' in args:
            # 录入新属性    
            attribute, value = args.split('=')
            attribute = attribute.strip().lower()
            value = value.strip()
            CONTROLLABLE_ATTRIBUTES = ['hp', 'mp', 'dmg', 'def','san']
            attribute = self.redirect_to_table(attribute)
            USER_ATTRIBUTES = ['str', 'con','siz', 'dex', 'app', 'int', 'pow', 'edu', 'luk']
            if attribute.startswith('&') :
                cursor.execute("INSERT INTO skills (user_id, slot_id, skillname, expression) VALUES (?, ?, ?, ?)", (sender_user_id, slot_id, attribute[1:], value))
            elif attribute in CONTROLLABLE_ATTRIBUTES:
                cursor.execute(f"UPDATE status SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (value, sender_user_id, slot_id))
            elif attribute in USER_ATTRIBUTES:
                cursor.execute(f"UPDATE users SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (value, sender_user_id, slot_id))
            else:
                cursor.execute("INSERT INTO skills (user_id, slot_id, skillname, expression) VALUES (?, ?, ?, ?)", (sender_user_id, slot_id, attribute, value))
            self.sqlite_conn.commit()
            return f"已录入属性 {attribute} 为 {value}"
        
        elif '+' in args:
            # 增加属性值
            attribute, value = args.split('+')
            attribute = attribute.strip().lower()
            value = value.strip()
            CONTROLLABLE_ATTRIBUTES = ['hp', 'mp', 'dmg', 'def','san']
            attribute = self.redirect_to_table(attribute)
            USER_ATTRIBUTES = ['str', 'con','siz', 'dex', 'app', 'int', 'pow', 'edu', 'luk']

            if attribute.startswith('&'):
                cursor.execute("SELECT expression FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute[1:]))
                result = cursor.fetchone()
                if result:
                    current_value = self.evaluate_expression(result[0])
                    new_value = current_value + int(value)
                    new_expression = f"{new_value}"
                    cursor.execute("UPDATE skills SET expression = ? WHERE user_id = ? AND slot_id = ? AND skillname = ?", (new_expression, sender_user_id, slot_id, attribute[1:]))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"
            elif attribute in CONTROLLABLE_ATTRIBUTES:
                    cursor.execute(f"SELECT {attribute} FROM status WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
                    result = cursor.fetchone()
                    current_value = result[0]
                    new_value = current_value + int(value)
                    new_expression = f"{new_value}"
                    cursor.execute(f"UPDATE status SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (new_expression, sender_user_id, slot_id))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                    
            elif attribute in USER_ATTRIBUTES:
                cursor.execute("SELECT * FROM users WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
                result = cursor.fetchone()
                if result:
                    columns = [col[0] for col in cursor.description]
                    current_value = result[columns.index(attribute)]
                    new_value = current_value + int(value) if command == '+' else current_value - int(value)
                    cursor.execute(f"UPDATE users SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (new_value, sender_user_id, slot_id))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"
            else:
                cursor.execute("SELECT expression FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute))
                result = cursor.fetchone()
                if result:
                    current_value = self.evaluate_expression(result[0])
                    new_value = current_value + int(value)
                    new_expression = f"{new_value}"
                    cursor.execute("UPDATE skills SET expression = ? WHERE user_id = ? AND slot_id = ? AND skillname = ?", (new_expression, sender_user_id, slot_id, attribute))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"

        elif '-' in args:
            # 减少属性值
            attribute, value = args.split('-')
            attribute = attribute.strip().lower()
            value = value.strip()
            CONTROLLABLE_ATTRIBUTES = ['hp', 'mp', 'dmg', 'def','san']
            attribute = self.redirect_to_table(attribute)
            USER_ATTRIBUTES = ['str', 'con','siz', 'dex', 'app', 'int', 'pow', 'edu', 'luk']

            if attribute.startswith('&'):
                cursor.execute("SELECT expression FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute[1:]))
                result = cursor.fetchone()
                if result:
                    current_value = self.evaluate_expression(result[0])
                    new_value = current_value - int(value)
                    new_expression = f"{new_value}"
                    cursor.execute("UPDATE skills SET expression = ? WHERE user_id = ? AND slot_id = ? AND skillname = ?", (new_expression, sender_user_id, slot_id, attribute[1:]))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"
            elif attribute in CONTROLLABLE_ATTRIBUTES:
                    cursor.execute(f"SELECT {attribute} FROM status WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
                    result = cursor.fetchone()
                    current_value = result[0]
                    new_value = current_value - int(value)
                    new_expression = f"{new_value}"
                    cursor.execute(f"UPDATE status SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (new_expression, sender_user_id, slot_id))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
            elif attribute in USER_ATTRIBUTES:
                cursor.execute("SELECT * FROM users WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id))
                result = cursor.fetchone()
                if result:
                    columns = [col[0] for col in cursor.description]
                    current_value = result[columns.index(attribute)]
                    new_value = current_value - int(value)
                    cursor.execute(f"UPDATE users SET {attribute} = ? WHERE user_id = ? AND slot_id = ?", (new_value, sender_user_id, slot_id))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"
            else:
                cursor.execute("SELECT expression FROM skills WHERE user_id = ? AND slot_id = ? AND skillname = ?", (sender_user_id, slot_id, attribute))
                result = cursor.fetchone()
                if result:
                    current_value = self.evaluate_expression(result[0])
                    new_value = current_value - int(value)
                    new_expression = f"{new_value}"
                    cursor.execute("UPDATE skills SET expression = ? WHERE user_id = ? AND slot_id = ? AND skillname = ?", (new_expression, sender_user_id, slot_id, attribute))
                    self.sqlite_conn.commit()
                    return f"已更新属性 {attribute} 为 {new_value}"
                else:
                    return f"未找到属性 {attribute}"
                
        else:
            return "无效的命令，请检查输入"

    def evaluate_expression(self, expression):
        # 评估掷骰表达式
        parts = expression.split('D')
        if len(parts) == 2:
            num_dice = int(parts[0])
            dice_sides = int(parts[1])
            return sum(random.randint(1, dice_sides) for _ in range(num_dice))
        else:
            return int(expression)

    def redirect_to_table(self, attribute):
        # 重定向中文属性名到英文属性表
        attribute_mapping = {
            '力量': 'str',
            '体质': 'con',
            '体型': 'siz',
            '敏捷': 'dex',
            '外貌': 'app',
            '智力': 'int',
            '意志': 'pow',
            '教育': 'edu',
            '幸运': 'luk'
        }
        if attribute in attribute_mapping:
            return attribute_mapping[attribute]
        else:
            return attribute