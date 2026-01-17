import pandas as pd
import random
import string

# --- 配置区 ---
COUNT = 20           # 想要生成多少张卡
WORDS = 1000         # 每张卡的面值 (比如 1000 字)
FILENAME = "1000字卡密.csv" # 保存的文件名
# ----------------

def generate_code(length=10):
    # 生成随机的大写字母+数字组合
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# 1. 生成数据
data = []
for _ in range(COUNT):
    data.append({
        "code": generate_code(),  # 随机卡密
        "words": WORDS,           # 面值
        "status": "unused",       # 状态 (直接帮你填好 unused)
        "used_by": "",            # 空着
        "used_time": ""           # 空着
    })

# 2. 保存为 CSV
df = pd.DataFrame(data)
df.to_csv(FILENAME, index=False)

print(f"✅ 成功生成 {COUNT} 张卡密！")
print(f"请打开 '{FILENAME}'，把里面的内容复制到你的 Google 表格里。")