import random
"""
.name //随机生成9个名字
"""

eng_first_names = ['John', 'Mary', 'David', 'Emily', 'Olivia', 'Sophia', 'William', 'Lucas', 'Isabella', 'Emma', 'Ava', 'Abigail', 'Emily', 'Sophia', 'Olivia', 'Sophia', 'William', 'Lucas', 'Isabella', 'Emma', 'Ava', 'Abigail']
eng_last_names = ['Smith', 'Johnson', 'Brown', 'Taylor', 'Williams', 'Davis', 'Miller', 'Wilson', 'Moore', 'White', 'Lopez', 'Garcia', 'Martinez', 'Hernandez', 'Lopez', 'Garcia', 'Martinez', 'Hernandez', 'Lopez', 'Garcia', 'Martinez', 'Hernandez']

chi_first_names = ['张', '李', '王', '赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈', '褚', '卫', '蒋', '沈', '韩', '杨', '朱', '秦', '尤', '许', '何', '吕', '施', '张', '孔', '曹', '严', '华', '金', '魏', '陶', '姜', '戚', '谢', '邹', '瑜', '叶', '黄']
chi_middle_names = ['晓', '子', '文', '琳', '雅', '静', '雪', '晴', '晶', '雨', '冰', '轩', '雅', '静', '淼', '华', '花', '琦', '琪', '琳', '琼', '琴', '琬', '琮', '琯', '琰', '琱', '琲', '琳', '琴', '琵', '琶', '琷', '琸', '琹', '琺', '琻', '琼', '思', '施', '昊', '昕', '昙', '春', '昭', '晓', '晔', '晗', '晙', '晟', '晡', '晦', '晨', '晩', '晫', '晬', '普', '独', '晴', '晶', '晷', '晸', '晹', '智', '秋', '秀', '秉', '秋', '秌', '秋', '秘', '秦', '博', '晨', '浩']
chi_last_names = ['华', '强', '杰', '宇', '轩', '淼', '晓', '子', '文', '琳', '雅', '静', '雪', '晴', '晶', '雨', '冰', '轩', '雅', '静', '淼', '华', '花', '琦', '琪', '琳', '琼', '琴', '琬', '琮', '琯', '琰', '琱', '琲', '琳', '琴', '伟', '伦', '涵', '通', '达', '迅', '飞', '风', '刚', '高', '鹏', '鹤', '岱', '黛', '月', '悦', '桧', '梓', '梦', '超', '智', '秀', '空', '破', '立', '笑', '笛', '笙', '玖', '玲', '珊', '珍', '珠', '琳', '琴', '琼', '瑞', '瑶', '璐', '璞', '璧', '璨', '瓒', '瓦', '甫', '田', '甲', '申', '电', '男', '甸', '畅', '留', '略', '畴', '疏', '疾', '痕', '癫', '白', '白', '百', '皓', '皮', '皿', '盈', '盛', '盟', '目', '眉', '眠', '眸', '睿', '瞳', '矛', '矢', '知', '石', '研', '砂', '砚', '砺']

def register_function(jrpg_functions, jrpg_events, sqlite_conn):
    jrpg_functions['name'] = name_generator

async def name_generator(args, userslot, sender_user_id, group_id):
    names = []
    for _ in range(3):
        first_name = random.choice(eng_first_names)
        last_name = random.choice(eng_last_names)
        names.append(f"{last_name} {first_name}")
    for _ in range(3):
        first_name = random.choice(chi_first_names)
        last_name = random.choice(chi_last_names)
        names.append(f"{first_name}{last_name}")
    for _ in range(3):
        first_name = random.choice(chi_first_names)
        middle_name = random.choice(chi_middle_names)
        last_name = random.choice(chi_last_names)
        names.append(f"{first_name}{middle_name}{last_name}")
    return '生成的名字：\n' + ';'.join(names)