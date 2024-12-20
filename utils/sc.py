import random
import sqlite3

"""

.sc 理智检定

用法：.sc [成功损失]/[失败损失] ([当前san值]) //已经.st了理智/san时，可省略最后的参数

    .sc 0/1 70
    .sc 1d10/1d100 直面外神 //当调用角色卡san时，san会自动更新为sc后的剩余值 //程序上可以损失负数的san，也就是可以用.sc -1d6/-1d6来回复san，但请避免这种奇怪操作 //大失败自动失去最大san值

（规则书） 出1大成功 不满50出96-100大失败，满50出100大失败

"""

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    SanCheck_instance = SanCheck(jrpg_functions, jrpg_events, sqlite_conn)
    jrpg_functions['sc'] = SanCheck_instance.sc

class SanCheck:
    jrpg_functions = None
    jrpg_events = None
    sqlite_conn = None

    def __init__(self, jrpg_functions, jrpg_events, sqlite_conn):
        self.jrpg_functions = jrpg_functions
        self.jrpg_events = jrpg_events
        self.sqlite_conn = sqlite_conn

    async def sc(self, args, userslot, sender_user_id, group_id):
        # 确保 args 是一个字符串, 是列表进行处理
        if isinstance(args, list):
            args = ' '.join(args)

        # 分离理由部分
        parts = args.split(' ')
        dice_parts = parts[0].split('/')
        
        if len(dice_parts) != 2:
            return "参数格式错误，请检查输入"

        success_loss = dice_parts[0]
        fail_loss = dice_parts[1]

        # 检查是否有额外的参数
        remaining_parts = parts[1:]
        san_value = None
        reason = None

        for part in remaining_parts:
            try:
                san_value = int(part)
                break
            except ValueError:
                reason = part

        # 获取用户当前的SAN值
        slot_id = userslot.get(sender_user_id)
        current_san = self.get_current_san(sender_user_id, slot_id, san_value)

        if current_san is None:
            return "您还没有创建角色卡，请先创建角色卡"

        # 进行理智检定
        roll_result = random.randint(1, 100)
        new_san = current_san

        if roll_result == 1:
            # 大成功
            new_san += int(self.parse_dice(success_loss))
        elif (current_san < 50 and 96 <= roll_result <= 100) or (current_san >= 50 and roll_result == 100):
            # 大失败
            max_san = self.get_max_san(sender_user_id, slot_id)
            new_san -= max_san
        elif roll_result <= current_san:
            # 成功
            new_san -= int(self.parse_dice(success_loss))
        else:
            # 失败
            new_san -= int(self.parse_dice(fail_loss))

        # 更新SAN值
        self.update_san(sender_user_id, slot_id, new_san)

        loss_san = new_san - current_san

        if new_san <= 0:
            result_text = f"理智检定结果: {roll_result}, 当前SAN值: {new_san}[{loss_san}], 理智耗尽"
        elif loss_san <= -5:
            result_text = f"理智检定结果: {roll_result}, 当前SAN值: {new_san}[{loss_san}], 需要一次INT检定（要疯喽）"
        else:
            result_text = f"理智检定结果: {roll_result}, 当前SAN值: {new_san}[{loss_san}]"
        if reason:
            result_text = f" ({reason})" + result_text
            
        page_content = None
        page_content =  await self.jrpg_events['auto_event']('sc_update', 'san', sender_user_id, group_id)
        if page_content:
            return ['\n'.join(result_text), page_content]

        return result_text

    def get_current_san(self, user_id, slot_id, provided_san=None):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT san FROM status WHERE user_id = ? AND slot_id = ?", (user_id, slot_id, ))
        result = cursor.fetchone()
        if result:
            return provided_san if provided_san is not None else result[0]
        return None

    def get_max_san(self, user_id, slot_id):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT pow FROM users WHERE user_id = ? AND slot_id = ?", (user_id, slot_id, ))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    def update_san(self, user_id, slot_id, new_san):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("UPDATE status SET san = ? WHERE user_id = ? AND slot_id = ?", (new_san, slot_id, user_id))
        self.sqlite_conn.commit()

    def parse_dice(self, dice_str):
        if 'd' in dice_str:
            num_dice, sides = map(int, dice_str.split('d'))
            return sum(random.randint(1, sides) for _ in range(num_dice))
        else:
            return int(dice_str)