import random

"""
.coc COC人物作成

用法：.coc (d)

    .coc ([name])//默认生成7版人物
    .coc d ([name] [level] [hp] [mp] [atk] [def] [spd] [vit] [agi] [int] [luk]) //接d为详细作成，一次只能作成一个 


.dnd DND人物作成

用法：.dnd

    .dnd [name]//默认生成5版人物


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
    Card_instance = Card(sqlite_conn)
    jrpg_functions['coc'] = Card_instance.coc
    # jrpg_functions['dnd'] = Card_instance.dnd

class Card:
    sqlite_conn = None

    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn

    async def coc(self, args, sender_user_id, group_id):
        if isinstance(args, list):
            args =' '.join(args)

        if 'd' in args:
            # 分割参数
            try:
                args = args.split(' ')
                name = args[1]
                str = int(args[2])
                con = int(args[3])
                siz = int(args[4])
                dex = int(args[5])
                app = int(args[6])
                INT = int(args[7])
                POW = int(args[8])
                edu = int(args[9])
                luk = int(args[10])
                # 计算点数
                point = str + con + siz + dex + app + INT + POW + edu
                san = POW
                HP = (siz + con) // 2
                MP = POW // 5
                if 2 <= str + siz <= 64:
                    DMG = -2
                    DEF = -2
                elif 65 <= str + siz <= 84:
                    DMG = -1
                    DEF = -1
                elif 85 <= str + siz <= 124:
                    DMG = 0
                    DEF = 0
                elif 125 <= str + siz <= 164:
                    DMG = '1d4'
                    DEF = 1
                else:
                    DMG = '1d6'
                    DEF = 2
                # 插入数据库
                with self.sqlite_conn:
                    self.sqlite_conn.execute("INSERT INTO users (user_id, name, str, con, siz, dex, app, int, pow, edu, luk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (sender_user_id, name, str, con, siz, dex, app, INT, POW, edu, luk))
                    self.sqlite_conn.execute("INSERT INTO status (user_id, name, hp, mp, dmg, def, san) VALUES (?, ?, ?, ?, ?, ?, ?)", (sender_user_id, name, HP, MP, DMG, DEF, san))
                return f"你已成功创建{name}的人物！\n点数：{point}\n属性：\n{self.rich_text(str, con, siz, dex, app, INT, POW, edu, luk)}\n状态：\nHP：{HP}\nMP：{MP}\nDMG：{DMG}\nDEF：{DEF}\nSAN：{san}"
            except Exception as e:
                return f"参数错误，请检查输入！\n{e}"
        # 默认生成7版人物
        if not args:
            name = '未命名'
        else:
            name = args
        with self.sqlite_conn:
            cursor = self.sqlite_conn.execute("SELECT * FROM users WHERE user_id=?", (sender_user_id,))
            row = cursor.fetchone()
    
            if row is not None:
                # 如果存在，则删除对应的记录
                self.sqlite_conn.execute("DELETE FROM users WHERE user_id=?", (sender_user_id,))
                self.sqlite_conn.execute("DELETE FROM status WHERE user_id=?", (sender_user_id,))
                self.sqlite_conn.execute("DELETE FROM skills WHERE user_id=?", (sender_user_id,))

            # 随机生成属性
            str = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            con = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            siz = (random.randint(1, 6) + random.randint(1, 6) + 6) * 5
            dex = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            app = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            INT = (random.randint(1, 6) + random.randint(1, 6) + 6) * 5
            POW = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            edu = (random.randint(1, 6) + random.randint(1, 6) + 6) * 5
            luk = (random.randint(1, 6) + random.randint(1, 6) + random.randint(1, 6)) * 5
            # 计算点数
            point = str + con + siz + dex + app + INT + POW + edu
            san = POW
            HP = (siz + con) // 2
            MP = POW // 5
            if 2 <= str + siz <= 64:
                DMG = -2
                DEF = -2
            elif 65 <= str + siz <= 84:
                DMG = -1
                DEF = -1
            elif 85 <= str + siz <= 124:
                DMG = 0
                DEF = 0
            elif 125 <= str + siz <= 164:
                DMG = '1d4'
                DEF = 1
            else:
                DMG = '1d6'
                DEF = 2
            # 插入数据库
            self.sqlite_conn.execute("INSERT INTO users (user_id, name, str, con, siz, dex, app, int, pow, edu, luk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (sender_user_id, name, str, con, siz, dex, app, INT, POW, edu, luk))
            self.sqlite_conn.execute("INSERT INTO status (user_id, name, hp, mp, dmg, def, san) VALUES (?, ?, ?, ?, ?, ?, ?)", (sender_user_id, name, HP, MP, DMG, DEF, san))
        return f"你已成功创建{name}的人物！\n点数：{point}\n属性：\n{self.rich_text(str, con, siz, dex, app, INT, POW, edu, luk)}\n状态：\nHP：{HP}\nMP：{MP}\nDMG：{DMG}\nDEF：{DEF}\nSAN：{san}"
                

    def rich_text(self, STR, con, siz, dex, app, int, POW, edu, luk):
        """
        根据属性值，生成富文本
        """
        
        if STR >= 120:
            STR = str(STR) + '（你解开限制器了？）'
        elif STR >= 100:
            STR = str(STR) + '（人类巅峰）'
        elif STR >= 80:
            STR = str(STR) + '（谁家大力王转世）'
        elif STR >= 60:
            STR = str(STR) + '（你见过力气最大的人）'
        elif STR >= 40:
            STR = str(STR) + '（普通人）'
        elif STR >= 20:
            STR = str(STR) + '（弱鸡）'
        else:
            STR = str(STR) + "（YOU CAN'T HURT ME, JACK）"

        if con >= 120:
            con = str(con) + '（你解开限制器了？）'
        elif con >= 100:
            con = str(con) + '（钢铁之躯）'
        elif con >= 80:
            con = str(con) + '（不惧严寒）'
        elif con >= 60:
            con = str(con) + '（隔壁大壮）'
        elif con >= 40:
            con = str(con) + '（普通人）'
        elif con >= 20:
            con = str(con) + '（身体虚弱）'
        elif con >= 1:
            con = str(con) + '（体弱多病）'
        elif con == 0:
            con = str(con) + '（死亡）'

        if siz >= 120:
            siz = str(siz) + '（你解开限制器了？）'
        elif siz >= 100:
            siz = str(siz) + '（巨人）'
        elif siz >= 80:
            siz = str(siz) + '（马或牛）'
        elif siz >= 60:
            siz = str(siz) + '（强健？强监！）'
        elif siz >= 40:
            siz = str(siz) + '（普通人）'
        elif siz >= 20:
            siz = str(siz) + '（矮人）'
        else:
            siz = str(siz) + '（婴儿）'

        if dex >= 120:
            dex = str(dex) + '（你解开限制器了？）'
        elif dex >= 100:
            dex = str(dex) + '（神龙）'
        elif dex >= 80:
            dex = str(dex) + '（世界级运动员）'
        elif dex >= 60:
            dex = str(dex) + '（杂技演员）'
        elif dex >= 40:
            dex = str(dex) + '（普通人）'
        elif dex >= 20:
            dex = str(dex) + '（笨拙）'
        else:
            dex = str(dex) + '（霍金belike）'

        if app >= 100:
            app = str(app) + '（车的什么玩意这是）'
        elif app >= 80:
            app = str(app) + '（世界巨星）'
        elif app >= 60:
            app = str(app) + '（万雌王）'
        elif app >= 40:
            app = str(app) + '（普通人）'
        elif app >= 20:
            app = str(app) + '（挫）'
        else:
            app = str(app) + '（十分甚至九分的池沼）'
        
        if int >= 100:
            int = str(int) + '（车的什么玩意这是）'
        elif int >= 80:
            int = str(int) + '（世界顶尖科学家）'
        elif int >= 60:
            int = str(int) + '（天才）'
        elif int >= 40:
            int = str(int) + '（普通人）'
        elif int >= 20:
            int = str(int) + '（学渣）'
        else:
            int = str(int) + '（白傻子）'

        if POW >= 120:
            POW = str(POW) + '（你解开限制器了？）'
        elif POW >= 100:
            POW = str(POW) + '（超越人类）'
        elif POW >= 80:
            POW = str(POW) + '（钢铁之心）'
        elif POW >= 60:
            POW = str(POW) + '（坚强之心）'
        elif POW >= 40:
            POW = str(POW) + '（普通人）'
        elif POW >= 20:
            POW = str(POW) + '（意志力弱）'
        else:
            POW = str(POW) + '（无能之人）'

        if edu >= 100:
            edu = str(edu) + '（车的什么玩意这是）'
        elif edu >= 90:
            edu = str(edu) + '（世界权威）'
        elif edu >= 75:
            edu = str(edu) + '（博士）'
        elif edu >= 65:
            edu = str(edu) + '（研究生毕业）'
        elif edu >= 50:
            edu = str(edu) + '（大学毕业）'
        elif edu >= 40:
            edu = str(edu) + '（高中毕业）'
        elif edu >= 20:
            edu = str(edu) + '（没怎么受过教育）'
        else:
            edu = str(edu) + '（新生儿）'

        if luk >= 100:
            luk = str(luk) + '（车的什么玩意这是）'
        elif luk >= 80:
            luk = str(luk) + '（气运之子）'
        elif luk >= 60:
            luk = str(luk) + '（幸运儿）'
        elif luk >= 40:
            luk = str(luk) + '（命格平庸）'
        elif luk >= 20:
            luk = str(luk) + '（有点倒霉）'
        else:
            luk = str(luk) + '（班尼特）'

        return f"力量：{STR}\n体质：{con}\n体型：{siz}\n敏捷：{dex}\n外貌：{app}\n智力：{int}\n精神：{POW}\n教育：{edu}\n幸运：{luk}"