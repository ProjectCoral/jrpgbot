import random
import sqlite3
from typing import List, Tuple

"""
.ra/rc 检定指令

用法：.ra/rc ([检定轮数]#)[属性名] ([成功率]) //角色卡设置了属性时，可省略成功率

    .rc 困难智力 99	//困难、极难在技能名开头视为关键词
    .rc 自动成功爆破	//自动成功在技能名开头视为关键词，非大失败即成功
    .rc 体质*5	//允许使用+-*/，但顺序要求为乘法>加减>除法
    .rc 敏捷-10	//修正后成功率必须在1-1000内
    .rc 3#p 手枪	//轮数与奖惩骰至多9个

sqlite3数据库：

CREATE TABLE IF NOT EXISTS users 
(user_id INTEGER PRIMARY KEY, 
name TEXT, 
str INTEGER, 
con INTEGER, 
siz INTEGER, 
dex INTEGER, 
app INTEGER, 
int INTEGER, 
pow INTEGER, 
edu INTEGER, 
luk INTEGER)
CREATE TABLE IF NOT EXISTS status
(user_id INTEGER PRIMARY KEY, 
name TEXT, 
hp INTEGER, 
mp INTEGER, 
dmg TEXT, 
def TEXT, 
san INTEGER
)
CREATE TABLE IF NOT EXISTS skills
(user_id INTEGER PRIMARY KEY, 
name TEXT, 
skillname TEXT, 
expression TEXT)
"""

def register_function(jrpg_functions, sqlite_conn):
    RollCheck_instance = RollCheck(sqlite_conn)
    jrpg_functions['rc'] = RollCheck_instance.rc
    jrpg_functions['ra'] = RollCheck_instance.rc

class RollCheck:
    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn
        self.cursor = sqlite_conn.cursor()
        self.special_skills = {
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

    async def rc(self, args: str, sender_user_id: int, group_id: int) -> str:
        # 确保 args 是一个字符串, 是列表进行处理
        if isinstance(args, list):
            args = ' '.join(args)
    
        # 解析参数
        args = args.strip()
        if not args:
            return '检定参数不能为空'
        
        # 分割轮数和检定内容
        parts = args.split('#', 1)
        rounds = 1
        if len(parts) > 1:
            try:
                rounds = int(parts[0])
                if rounds < 1 or rounds > 9:
                    return '轮数必须在1到9之间'
            except ValueError:
                return '无效的轮数'
            args = parts[1].strip()
        
        # 获取用户属性
        user_attributes = self.get_user_attributes(sender_user_id)
        if not user_attributes:
            return '用户未设置属性，请先设置属性'
        
        # 解析检定内容
        skill_name, success_rate = self.parse_skill_name_and_success_rate(args, user_attributes)
        if not skill_name:
            return '无效的检定内容'
        
        # 执行检定
        results = []
        for _ in range(rounds):
            result = self.perform_roll_check(skill_name, success_rate)
            results.append(result)
        
        return '\n'.join(results)

    def get_user_attributes(self, user_id: int) -> dict:
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {col[0]: row[i] for i, col in enumerate(self.cursor.description)}
        return {}

    def parse_skill_name_and_success_rate(self, args: str, user_attributes: dict) -> Tuple[str, int]:
        # 处理特殊关键词
        keywords = ['困难', '极难', '自动成功']
        for keyword in keywords:
            if args.startswith(keyword):
                skill_name = args[len(keyword):].strip()
                if keyword == '自动成功':
                    return skill_name, 100
                elif keyword == '困难':
                    return skill_name, 20
                elif keyword == '极难':
                    return skill_name, 10
    
        # 处理特殊技能名
        
    
        # 分割技能名和表达式
        expression_parts = args.split()
        skill_name = expression_parts[0]
    
        # 如果技能名是特殊技能名，直接使用对应的属性值
        if skill_name in self.special_skills:
            attr = self.special_skills[skill_name]
            if attr in user_attributes:
                return skill_name, user_attributes[attr]
    
        # 处理表达式
        expression = ''.join(expression_parts[1:])
    
        # 替换属性值
        for attr, value in user_attributes.items():
            expression = expression.replace(attr, str(value))
    
        try:
            success_rate = eval(expression)
            if success_rate < 1 or success_rate > 1000:
                return None, None
            return skill_name, success_rate
        except Exception as e:
            return None, None

    def perform_roll_check(self, skill_name: str, success_rate: int) -> str:
        roll = random.randint(1, 100)
        if roll == 100:
            return f'检定 {skill_name} 大失败（1d100 = [{roll}] <= {success_rate}）'
        elif roll == 1:
            return f'检定 {skill_name} 大成功（1d100 = [{roll}] <= {success_rate}）'
        elif roll <= success_rate:
            return f'检定 {skill_name} 成功（1d100 = [{roll}] <= {success_rate}）'
        else:
            return f'检定 {skill_name} 失败（1d100 = [{roll}] > {success_rate}）'