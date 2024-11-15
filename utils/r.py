import random
import sqlite3

"""
.r 普通掷骰指令

用法：.r [掷骰表达式] ([掷骰原因]) 或.r [掷骰原因] [掷骰表达式]：([掷骰次数]#)[骰子个数]d[骰子面数](b[奖励骰个数])(p[惩罚骰个数])(k[取点数最大的骰子数])

    .r	//骰子面数默认100，可通过.set修改默认值
    .r 沙漠之鹰	//存在录入角色卡时，可调用角色卡中保存的表达式
    .r 1d4+2 中型刀伤害	//个数范围1-100，面数范围1-1000，否则非法
    .r 3d6X5 幸运	//‘X’或'*'均视为乘号
    .r 3#1d6 3发.22伤害	//每次结果分开发送
    .r 1d10# 乌波·萨斯拉的子嗣	//掷骰次数范围1-10
    .r3d6k2	//取点数最大的2个骰子
    .r3#p 手枪连射	//奖惩骰固定为一个百面骰，不能与h以外其他字母共存
    .rb2 瞄准后偷袭	//2个奖励骰
    .rh 心理学	//暗骰，结果通过私聊发送
    .rs1D10+1D6+3 沙鹰伤害	//省略单个骰子的点数，直接给结果 //现版本开头的r不再可用o或d代替 //一次掷骰超过20个将会自动排序
"""

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    RollDice_instance = RollDice(jrpg_functions, jrpg_events, sqlite_conn)
    jrpg_functions['r'] = RollDice_instance.r


class RollDice:
    jrpg_functions = None
    jrpg_events = None
    sqlite_conn = None

    def __init__(self, jrpg_functions, jrpg_events, sqlite_conn):
        self.jrpg_functions = jrpg_functions
        self.jrpg_events = jrpg_events
        self.conn = sqlite_conn
        self.cursor = self.conn.cursor()

    async def r(self, args, userslot, sender_user_id, group_id):
        # 确保 args 是一个字符串, 是列表进行处理
        if isinstance(args, list):
            args = ' '.join(args)

        if not args:
            # 默认使用1d100
            args = '1d100'

        def contains_special_chars(s, special_chars):
            return any(char in s for char in special_chars)
        special_chars = ['+', '-', '*', '/', '#', 'd', 'b', 'p', 'k']

        # 按空格分割
        parts = args.split()

        if len(parts) > 1:
            if not contains_special_chars(parts[0], special_chars):
                reason = parts[0]
                dice_expr = parts[1]
            elif not contains_special_chars(parts[1], special_chars):
                reason = parts[1]
                dice_expr = parts[0]
            else:
                reason = ''
                dice_expr = args
        else:
            reason = ''
            dice_expr = args

        if '#' in dice_expr:
            times, dice_expr = dice_expr.split('#', 1)
            times = int(times) if times.isdigit() else 1
        else:
            times = 1

        if 'd' not in dice_expr:
            return "请输入骰子表达式！"

        dice_parts = dice_expr.split('d')
        if len(dice_parts) != 2:
            return "请输入正确的骰子表达式！"

        dice_num, dice_side = dice_parts
        dice_num = int(dice_num) if dice_num.isdigit() else 1
        dice_side = int(dice_side) if dice_side.isdigit() else 6  # 默认骰子面数为6

        bonus_num = self.extract_num(dice_expr, 'b')
        penalty_num = self.extract_num(dice_expr, 'p')
        keep_num = self.extract_num(dice_expr, 'k')

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

        dice_results = []
        total_sum = 0
        for _ in range(times):
            dice_result = [random.randint(1, dice_side) for _ in range(dice_num)]
            dice_result.sort(reverse=True)
            kept_dice = dice_result[:keep_num]
            total_sum += sum(kept_dice)
            dice_results.append(f"{kept_dice}({sum(kept_dice)})")

        result += ', '.join(dice_results)

        if bonus_num > 0:
            bonus_result = self.roll_bonus(bonus_num, dice_side)
            total_sum += sum(bonus_result)
            result += f" + {bonus_result}({sum(bonus_result)})"

        if penalty_num > 0:
            penalty_result = self.roll_penalty(penalty_num, dice_side)
            total_sum -= sum(penalty_result)
            result += f" - {penalty_result}({sum(penalty_result)})"

        result += f" = {total_sum}"

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