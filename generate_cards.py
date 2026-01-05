import json
import random
import string

# 定义面值规则（字数）
CARD_TYPES = {
    "MINI": {"words": 1000, "price": "3元", "count": 20},    # 生成20张
    "SMALL": {"words": 2000, "price": "6元", "count": 20},   # 生成20张
    "MEDIUM": {"words": 5000, "price": "15元", "count": 20}, # 生成20张
    "LARGE": {"words": 10000, "price": "30元", "count": 10}, # 生成10张
    "SUPER": {"words": 20000, "price": "60元", "count": 10}, # 生成10张
}

def generate_code(prefix):
    """生成类似 '1K-ABCD-1234' 的卡密"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{suffix}"

database = {}

print("正在生成卡密...")
for c_type, info in CARD_TYPES.items():
    prefix = str(info['words']) # 卡密前缀，如 1000
    for _ in range(info['count']):
        code = generate_code(prefix)
        # 存入数据库：状态为 'unused' (未使用)
        database[code] = {"words": info['words'], "status": "unused"}
    print(f"✅ 已生成 {info['count']} 张 [{info['price']}/{info['words']}字] 的卡密")

# 保存到文件
with open("coupons.json", "w", encoding="utf-8") as f:
    json.dump(database, f, indent=4)

print("\n🎉 成功！卡密已保存到 'coupons.json'。")
print("请把 coupons.json 和主程序 app.py 放在同一个文件夹下！")