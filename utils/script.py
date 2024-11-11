import os
import re

"""
.script [页码] //翻页
.script load [剧本] //加载剧本

lua剧本脚本example:
text = {
[1]=
[[太阳高悬天空，无情地释放着热量。当你来到奥斯本药店门口的汽车站时，感觉自己都要被烤熟了。
你放下沉重的行李箱，摘下帽子，终于得到片刻休息。你往脸上扇了扇风。
在你的家乡，夏天总是漫长；但这个夏天格外令你空虚。 前往 2。]],
[2]=
[[
text
text
{xxx}text]],
...}
"""

def register_function(jrpg_functions, sqlite_conn):
    ScriptReader_instance = ScriptReader(sqlite_conn)
    jrpg_functions['script'] = ScriptReader_instance.scriptreader

class ScriptReader:
    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn
        self.script_path = './data/jrpgbot/scripts'
        self.reload_script()

    def reload_script(self):
        self.script_list = []
        self.script = {}
        self.script_name = ''
        if not os.path.exists(self.script_path):
            os.makedirs(self.script_path)
            
        for script_name in os.listdir(self.script_path):
            script_path = os.path.join(self.script_path, script_name)
            if not os.path.isdir(script_path):
                continue
            script_file = os.path.join(script_path, 'script.lua')
            if os.path.exists(script_file):
                self.script_list.append(script_name)

    async def scriptreader(self, args, userslot, sender_user_id, group_id):
        if len(args) == 0:
            return '请输入指令。'
        
        command = args[0]

        if command == 'reload':
            self.reload_script()
            return f'列表已刷新。共检测到 {len(self.script_list)} 个剧本。'
        
        elif command == 'info':
            if not self.script_name:
                return '请先加载剧本。'
            if os.path.exists(os.path.join(self.script_path, self.script_name, 'script.info')):
                with open(os.path.join(self.script_path, self.script_name, 'script.info'), 'r', encoding='utf-8') as f:
                    info = f.read()
                    return f'已加载剧本 {self.script_name} \n信息：\n{info}'
            else:
                return f'已加载剧本 {self.script_name} 未提供信息。'
            
        elif command == 'load':
            if len(args) < 2:
                return f'可加载剧本：{", ".join(self.script_list)}'
            script_name = args[1]
            if script_name in self.script_list:
                try:
                    with open(os.path.join(self.script_path, script_name, 'script.lua'), 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 使用正则表达式匹配多行剧本内容
                        matches = re.finditer(r'\[(\d+)\]\s*=\s*\[\[(.*?)\]\]', content, re.S | re.M)
                        self.script = {int(match.group(1)): match.group(2).strip() for match in matches}
                        self.script_name = script_name
                    return f'{script_name} 加载成功，共 {len(self.script)} 页。'
                except Exception as e:
                    return f'加载剧本失败: {str(e)}'
            else:
                return '剧本不存在。'

        # 检测是否存在角色卡
        slot_id = userslot.get(sender_user_id)
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND slot_id = ?", (sender_user_id, slot_id,))
        result = cursor.fetchone()
        cursor.close()  # 关闭游标
        if not result:
            return '你还没有角色卡，请先创建角色卡。'

        if command.isdigit():
            page = int(command)
            script_page = self.script.get(page, '')
            if page == self.script.get(max(self.script.keys()), 0):
                return script_page + '\n\n(已到达最后一页)'
            if script_page:
                return script_page
            else:
                return '指定页码未找到，请确认已加载正确的剧本。'
        else:
            return '请输入正确的页码或命令。'
        
    