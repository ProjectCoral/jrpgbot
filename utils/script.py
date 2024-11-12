import os
import re
import json

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

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    ScriptReader_instance = ScriptReader(jrpg_functions, jrpg_events, sqlite_conn)
    jrpg_functions['script'] = ScriptReader_instance.scriptreader

class ScriptReader:
    jrpg_functions = None
    jrpg_events = None
    sqlite_conn = None

    def __init__(self, jrpg_functions, jrpg_events, sqlite_conn):
        self.jrpg_functions = jrpg_functions
        self.jrpg_events = jrpg_events
        self.sqlite_conn = sqlite_conn
        self.script_path = './data/jrpgbot/scripts'
        self.script_list = []
        self.script = {}
        self.script_name = ''
        self.current_page = None
        self.last_group_id = None
        self.ScriptEvent_instance = ScriptEvent(self)
        self.reload_script()

    def reload_script(self):
        self.script_list = []
        self.script = {}
        self.script_name = ''
        self.current_page = None
        self.ScriptEvent_instance.clear()
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
                    if os.path.exists(os.path.join(self.script_path, script_name,'auto.json')):
                        self.ScriptEvent_instance.load(os.path.join(self.script_path, script_name,'auto.json'))
                        return f'{script_name} 加载成功，共 {len(self.script)} 页。\n已加载 {len(self.ScriptEvent_instance.auto_event)} 个自动事件。'
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

        self.last_group_id = group_id

        if command.isdigit():
            return self.get_page_content(command)
        else:
            return '请输入正确的页码或命令。'
        
    def get_page_content(self, page_num):
        page = int(page_num)
        if page < 1 or page > len(self.script):
            return '指定页码不存在。'
        script_page = self.script.get(page, '')
        if script_page:
            self.current_page = int(page)
            return script_page
        else:
            return '指定页码不存在。'

class ScriptEvent:
    Reader = None

    def __init__(self, Reader):
        self.Reader = Reader
        self.jrpg_functions = Reader.jrpg_functions
        self.jrpg_events = Reader.jrpg_events
        self.sqlite_conn = Reader.sqlite_conn
        self.auto_event = {}
        self.clear()
        self.jrpg_events['auto_event'] = self.script_event

    def clear(self):
        self.auto_event = {}

    def load(self, auto_json_path):
        with open(auto_json_path, 'r', encoding='utf-8') as f:
            self.auto_event = json.load(f)

    async def script_event(self, event_name, skill_name, sender_user_id, group_id):
        current_page = self.Reader.current_page 
        if current_page is None or self.auto_event is None:
            return None
        
        if self.Reader.last_group_id is not None and group_id != self.Reader.last_group_id:
            return None

        current_page = str(current_page)
        if current_page in self.auto_event:
            auto_event = self.auto_event[current_page]
        else:
            return None

        if event_name not in auto_event:
            return None

        event_content = auto_event[event_name]
        if isinstance(event_content, dict):
            if skill_name in event_content:
                goto_page = event_content[skill_name]
            else:
                return None
        else:
            goto_page = event_content
        
        if goto_page == 'end':
            return '剧本结束。'
        else:
            page_content = self.Reader.get_page_content(int(goto_page))
            return f'自动跳转到 {goto_page} 页。\n {page_content}'


