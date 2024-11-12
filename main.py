import os
import json
import logging
import sqlite3
import importlib.util

logger = logging.getLogger("jrpgbot")

def register_plugin(register, config, perm_system):
    # register.command("jrpg", "jrpgbot.jrpg.jrpg_command", help="jrpgbot.jrpg.help")
    perm_system.register_perm("jrpgbot", "Base permission for the jrpgbot plugin.")
    perm_system.register_perm("jrpgbot.control", "Permission to control the jrpgbot plugin.")
    register.register_event("prepare_reply", "jrpg", JRPGBot(register, config, perm_system).jrpg_command, 1)


class JRPGBot:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.register = register
        self.config = config
        self.perm_system = perm_system
        self.jrpg_functions = {}
        self.jrpg_events = {}
        self.load_db()
        self.load_functions()
        self.bot_status = False

    def load_functions(self):
        self.jrpg_functions['bot'] = self.bot_control
        self.jrpg_functions['info'] = self.info
        for file in os.listdir(os.path.join(os.path.dirname(__file__), "utils")):
            if file.endswith(".py") and not file.startswith("__init__"):
                spec = importlib.util.spec_from_file_location(file[:-3], os.path.join(os.path.dirname(__file__), "utils", file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "register_function"):
                    module.register_function(self.jrpg_functions, self.jrpg_events, self.conn)
        logger.info(f"Loaded {len(self.jrpg_functions)} jrpg functions.")

    async def jrpg_command(self, message, **kwargs):
        raw_message = message['message']
        sender_user_id = message['sender_user_id']
        group_id = message['group_id']

        if not raw_message.startswith('.'):
            return {"message": None, "sender_user_id": sender_user_id, "group_id": group_id}, False, False, 1

        logger.info(f"Received jrpg command from {sender_user_id} in {group_id}: {raw_message}")

        try:
            command = raw_message[1:].split()[0]
            args = raw_message[1:].split()[1:]
        except IndexError:
            return {"message": "Invalid command format.", "sender_user_id": sender_user_id, "group_id": group_id}, True, False, 1
        
        if not self.bot_status and command not in ["bot", "info"]:
                return {"message": None, "sender_user_id": sender_user_id, "group_id": group_id}, False, False, 1

        if command not in self.jrpg_functions:
            return {"message": f"Command {command} not found.", "sender_user_id": sender_user_id, "group_id": group_id}, True, False, 1
        
        try:
            result = await self.jrpg_functions[command](args, self.userslot, sender_user_id, group_id)
        except Exception as e:
            logger.exception(f"Error executing command {command}: {e}")
            return {"message": f"Error executing command: {e}", "sender_user_id": sender_user_id, "group_id": group_id}, True, False, 1

        slot_id = self.userslot.get(sender_user_id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM users WHERE user_id =? AND slot_id =?", (sender_user_id, slot_id,))
        name = cursor.fetchone()

        if isinstance(result, list):
            if name is not None:
                result[0] = f"[{name[0]}] {result[0]}"
                result[0] = f"[CQ:at,qq={sender_user_id}]\n{result[0]}"

            if group_id == -1:
                result[0] = f"{result[0]}\n警告：你正在私聊模式下使用JRPG Bot，可能无法正常运行。"
        else:
            if name is not None:
                result = f"[{name[0]}] {result}"

            result = f"[CQ:at,qq={sender_user_id}]\n{result}"

            if group_id == -1:
                result = f"{result}\n警告：你正在私聊模式下使用JRPG Bot，可能无法正常运行。"

        return {"message": result, "sender_user_id": sender_user_id, "group_id": group_id}, True, False, 1
    
    async def bot_control(self, args, userslot, sender_user_id, group_id):
        if not self.perm_system.check_perm(["jrpgbot", "jrpgbot.control"], sender_user_id, group_id):
            return "You don't have permission to control the jrpgbot plugin."
        if len(args) > 0 and args[0].startswith("on"):
            self.bot_status = True
            return "JRPG Bot is now on."
        elif len(args) > 0 and args[0].startswith("off"):
            self.bot_status = False
            return "JRPG Bot is now off."
        else:
            return "Invalid command format. Usage: .bot [on|off]"

    def load_db(self):
        if not os.path.exists("./data/jrpgbot"):
            os.makedirs("./data/jrpgbot")
        try:
            self.conn = sqlite3.connect("./data/jrpgbot/usertable.db", check_same_thread=False)
            with self.conn:
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
        except sqlite3.Error as e:
            raise e
        self.userslot = UserSlot("./data/jrpgbot/userslot.json")
        logger.info("Loaded database.")


    async def info(self, *args, **kwargs):
        coral_ver = self.config.get("coral_version")
        return f"JRPG Bot v0.1.1, by Akina絵\nRunning on Coral {coral_ver}"
    

class UserSlot:
    slot_path = "./data/jrpgbot/userslot.json"

    def __init__(self, slot_path):
        self.slot_path = slot_path
        if not os.path.exists(self.slot_path):
            with open(self.slot_path, "w") as f:
                json.dump({}, f, indent=4)
        with open(self.slot_path, "r") as f:
            self.slot_id = json.load(f)

    def get(self, user_id):
        user_id = str(user_id)
        if user_id not in self.slot_id:
            self.slot_id[user_id] = 1
            self.save()
        return self.slot_id[user_id]

    def set(self, user_id, slot_id):
        self.slot_id[str(user_id)] = int(slot_id)
        self.save()

    def save(self):
        with open(self.slot_path, "w") as f:
            json.dump(self.slot_id, f, indent=4)