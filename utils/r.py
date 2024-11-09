import random

"""
.r 普通掷骰指令

用法：.r [掷骰表达式] ([掷骰原因]) 或.r [掷骰原因] [掷骰表达式]：([掷骰次数]#)[骰子个数]d[骰子面数](b[奖励骰个数])(p[惩罚骰个数])(k[取点数最大的骰子数])


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
luk INTEGER, 
san INTEGER)
"""

def register_function(jrpg_functions, sqlite_conn):
    RollDice_instance = RollDice(sqlite_conn)
    jrpg_functions['r'] = RollDice_instance.r


class RollDice:
    sqlite_conn = None

    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn

    async def r(self, args, sender_user_id, group_id):
        # 确保 args 是一个字符串, 是列表进行处理
        if isinstance(args, list):
            args =''.join(args)

        # if not args:
        #     return "请输入掷骰表达式或掷骰原因！"
        
        if not args:
            #默认使用1d100
            args = '1d100'

        if args.startswith('('):
            reason = args[1:args.find(')')]
            args = args[args.find(')')+1:].strip()
        else:
            reason = ''
        
        if '#' in args:
            times, args = args.split('#')
            times = int(times) if times.isdigit() else 1
        else:
            times = 1

        if 'd' not in args:
            return "请输入骰子表达式！"
        
        args = args.split('d')
        if len(args) != 2:
            return "请输入正确的骰子表达式！"
        
        dice_num, dice_side = args
        dice_num = int(dice_num) if dice_num.isdigit() else 1
        dice_side = int(dice_side) if dice_side.isdigit() else 6  # 默认骰子面数为6
        
        bonus_num = self.extract_num(args, 'b')
        penalty_num = self.extract_num(args, 'p')
        keep_num = self.extract_num(args, 'k')

        # 数值合法性检查
        if dice_num > 100 or dice_side > 1000 or bonus_num > 100 or penalty_num > 100 or keep_num > 100:
            return "骰子数量或面数过大！"
        if dice_num < 1 or dice_side < 2 or bonus_num < 0 or penalty_num < 0 or keep_num < 0:
            return "骰子数量或面数过小！"
        if keep_num > dice_num:
            return "取点数最大的骰子数不能大于骰子总数！"
        
        if keep_num == 0:
            keep_num = dice_num
        
        if reason:
            result = f"({reason})掷出了{dice_num}d{dice_side}骰子："
        else:
            result = f"掷出了{dice_num}d{dice_side}骰子："
        
        dice_result = [random.randint(1, dice_side) for _ in range(dice_num)]
        dice_result.sort(reverse=True)
        
        if keep_num == dice_num:
            result += f"{dice_result}"
        else:
            result += f"{dice_result[:keep_num]}({sum(dice_result[:keep_num])})"

        if bonus_num > 0:
            result += f"+{self.roll_bonus(bonus_num, dice_side)}"
        if penalty_num > 0:
            result += f"-{self.roll_penalty(penalty_num, dice_side)}"
        
        return result

    def extract_num(self, args, identifier):
        """辅助方法：提取特定标志后的数字值"""
        if identifier in args:
            start_index = args.index(identifier) + 1
            num_str = ''
            while start_index < len(args) and args[start_index].isdigit():
                num_str += args[start_index]
                start_index += 1
            return int(num_str) if num_str else 0
        return 0

    def roll_bonus(self, bonus_num, dice_side):
        """辅助方法：计算加分骰结果"""
        bonus_result = [random.randint(1, dice_side) for _ in range(bonus_num)]
        bonus_result.sort(reverse=True)
        return bonus_result

    def roll_penalty(self, penalty_num, dice_side):
        """辅助方法：计算减分骰结果"""
        penalty_result = [random.randint(1, dice_side) for _ in range(penalty_num)]
        penalty_result.sort(reverse=True)
        return penalty_result
