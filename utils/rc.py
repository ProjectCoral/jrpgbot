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

"""

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    RollCheck_instance = RollCheck(jrpg_functions, jrpg_events, sqlite_conn)
    jrpg_functions['rc'] = RollCheck_instance.rc
    jrpg_functions['ra'] = RollCheck_instance.rc

class RollCheck:
    jrpg_functions = None
    jrpg_events = None
    sqlite_conn = None

    def __init__(self, jrpg_functions, jrpg_events, sqlite_conn):
        self.jrpg_functions = jrpg_functions
        self.jrpg_events = jrpg_events
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

    async def rc(self, args: str, userslot, sender_user_id: int, group_id: int) -> str:
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
        slot_id = userslot.get(sender_user_id)
        user_attributes = self.get_user_attributes(sender_user_id, slot_id)
        if not user_attributes:
            return '用户未设置属性，请先设置属性'
        
        # 解析检定内容
        skill_name, success_rate, reason = self.parse_skill_name_and_success_rate(args, user_attributes)
        if not skill_name:
            return '无效的检定内容'
        
        # 修正成功率
        if success_rate is None:
            return f'无效的成功率或 {skill_name} 录入数据错误'
        
        success_rate = int(success_rate)
        if success_rate < 1:
            success_rate = 1
        elif success_rate > 100:
            success_rate = 100

        # 执行检定
        page_content = None
        results = []
        if reason:
            results.append(f'（{reason}）')
        for _ in range(rounds):
            result = self.perform_roll_check(skill_name, success_rate)
            if rounds == 1:
                if '成功' in result:
                    page_content =  await self.jrpg_events['auto_event']('rc_success', skill_name, sender_user_id, group_id)
                elif '失败' in result:
                    if '大失败' in result:
                        page_content =  await self.jrpg_events['auto_event']('rc_big_failure', skill_name, sender_user_id, group_id)
                    else:
                        page_content =  await self.jrpg_events['auto_event']('rc_failure', skill_name, sender_user_id, group_id)
            results.append(result)
        
        if skill_name in ['hp', 'mp', 'dmg', 'def']:
            results.append("你为什么要检定这个？")

        if page_content:
            return ['\n'.join(results), page_content]
        
        return '\n'.join(results)

    def get_user_attributes(self, user_id: int, slot_id: int) -> dict:
        user_attributes = {}
        
        # 查询 users 表
        self.cursor.execute("SELECT * FROM users WHERE user_id=? AND slot_id=?", (user_id, slot_id,))
        row = self.cursor.fetchone()
        if row:
            user_attributes.update({col[0]: row[i] for i, col in enumerate(self.cursor.description)})
        
        # 查询 status 表
        self.cursor.execute("SELECT * FROM status WHERE user_id=? AND slot_id=?", (user_id, slot_id,))
        row = self.cursor.fetchone()
        if row:
            for i, col in enumerate(self.cursor.description):
                user_attributes[col[0]] = row[i]

        # 查询 skills 表
        self.cursor.execute("SELECT * FROM skills WHERE user_id=? AND slot_id=?", (user_id, slot_id,))
        rows = self.cursor.fetchall()
        for row in rows:
            skillname = row[2]
            expression = row[3]
            user_attributes[skillname] = expression
        
        return user_attributes

    def parse_skill_name_and_success_rate(self, args: str, user_attributes: dict) -> Tuple[str, int, str]:
        # 提取 reason
        reason = ''
        if ' ' in args:
            parts = args.split(maxsplit=1)
            if len(parts) > 1 and not parts[1].isdigit():
                if not any(op in parts[1] for op in ['+', '-', '*', '/']):
                    reason = parts[1]
                    args = parts[0]

        # 处理特殊关键词
        keywords = ['困难', '极难', '自动成功']
        for keyword in keywords:
            if args.startswith(keyword):
                skill_name = args[len(keyword):].strip()
                if keyword == '自动成功':
                    return skill_name, 100, reason
                elif keyword == '困难':
                    return skill_name, 20, reason
                elif keyword == '极难':
                    return skill_name, 10, reason
        
        # 分割技能名和表达式
        expression_parts = args.split()
        skill_name = expression_parts[0]
    
        # 如果技能名是特殊技能名，直接使用对应的属性值
        if skill_name in self.special_skills:
            attr = self.special_skills[skill_name]
            if attr in user_attributes:
                return attr, user_attributes[attr], reason
            
        # 如果只传入技能名，则尝试获取成功率
        if len(expression_parts) == 1:
            if skill_name in user_attributes:
                success_rate = user_attributes[skill_name]
                return skill_name, success_rate, reason
    
        # 处理表达式
        expression = ''.join(expression_parts[1:])
    
        # 替换属性值
        for attr, value in user_attributes.items():
            expression = expression.replace(attr, str(value))
    
        try:
            success_rate = eval(expression)
            if not success_rate.isdigit():
                if 'd' in success_rate:
                    dice_num, dice_size = success_rate.split('d')
                    try:
                        dice_num = int(dice_num)
                        dice_size = int(dice_size)
                        if dice_num < 1 or dice_size < 1:
                            return None, None, reason
                        success_rate = sum([random.randint(1, dice_size) for _ in range(dice_num)])
                        return skill_name, success_rate, reason
                    except ValueError:
                        return None, None, reason
                else:
                    return None, None, reason
            if success_rate < 1 or success_rate > 1000:
                return None, None, reason
            return skill_name, success_rate, reason
        except Exception as e:
            return None, None, reason

    def perform_roll_check(self, skill_name: str, success_rate: int) -> str:
        roll = random.randint(1, 100)
        if 96 <= roll <= 100:
            return f'检定 {skill_name} 大失败（1d100 = [{roll}] <= {success_rate}）'
        elif roll == 1:
            return f'检定 {skill_name} 大成功（1d100 = [{roll}] <= {success_rate}）'
        elif roll <= success_rate:
            return f'检定 {skill_name} 成功（1d100 = [{roll}] <= {success_rate}）'
        else:
            return f'检定 {skill_name} 失败（1d100 = [{roll}] > {success_rate}）'