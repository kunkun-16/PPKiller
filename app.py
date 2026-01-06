import streamlit as st
from openai import OpenAI
import json
import os
import time

# --- 1. 全局配置 ---
st.set_page_config(
    page_title="口袋狗AI降重 - 2026专业版",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. 核心配置区 (请修改这里) ---
# 你的 DeepSeek API Key (必须填，否则跑不通)
SYSTEM_API_KEY = "sk-8b582db9fd144de4935b1957db1deb2e" 

# 文件路径
USER_DB = "users.json"
COUPON_DB = "coupons.json"

# --- 3. 数据库工具函数 ---
def init_db():
    """确保数据库文件存在，防止报错"""
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w") as f: json.dump({}, f)
    if not os.path.exists(COUPON_DB):
        with open(COUPON_DB, "w") as f: json.dump({}, f)

def load_json(path):
    init_db()
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

# --- 替换原来的 save_json 函数 ---
def save_json(path, data):
    try:
        # 尝试写入文件
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except PermissionError:
        # 如果报错，提示用户
        st.error(f"❌ 写入失败！文件 {path} 被占用了。")
        st.warning("💡 请检查：你是不是在 Cursor 或其他软件里打开了这个文件？请先关闭它！")
        # 停止运行，防止数据丢失
        st.stop()

def update_balance(username, amount):
    users = load_json(USER_DB)
    if username in users:
        users[username]['balance'] += amount
        save_json(USER_DB, users)
        st.session_state.user_info['balance'] = users[username]['balance']
        return True
    return False

# --- 4. 登录/注册页面 (仿写作狗) ---
def login_page():
    st.markdown("""
    <style>
        .big-font {font-size:30px !important; font-weight: bold;}
        .sub-font {font-size:16px; color: #666;}
        .login-box {border: 1px solid #ddd; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px #eee;}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.image("https://img.freepik.com/free-vector/blogging-concept-illustration_114360-1038.jpg", width=500)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="big-font">让学术写作更简单</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-font">DeepSeek V3 强力驱动 · 专攻 AIGC 检测 · 深度去痕</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 账号登录", "🆕 快速注册"])
        
        with tab1:
            username = st.text_input("用户名", key="l_user")
            password = st.text_input("密码", type="password", key="l_pass")
            
            if st.button("登录", type="primary", use_container_width=True):
                # 1. 尝试加载数据库
                users = load_json(USER_DB)
                
                # 2. 超级后门：如果输入 admin / 123，直接通过，不管数据库里有没有
                if username == "admin" and password == "123":
                    st.session_state.logged_in = True
                    st.session_state.username = "admin"
                    st.session_state.user_info = {"password": "123", "balance": 999999}
                    st.success("管理员登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                
                # 3. 普通用户逻辑
                elif username in users and users[username]['password'] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_info = users[username]
                    st.success("登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 账号或密码错误")

        with tab2:
            new_user = st.text_input("设置用户名", key="r_user")
            new_pass = st.text_input("设置密码", type="password", key="r_pass")
            if st.button("注册并登录", use_container_width=True):
                users = load_json(USER_DB)
                if new_user in users:
                    st.error("用户名已存在")
                elif not new_user or not new_pass:
                    st.warning("请填写完整")
                else:
                    # 注册送200字
                    users[new_user] = {"password": new_pass, "balance": 200} 
                    save_json(USER_DB, users)
                    st.success("注册成功！请切换到登录页使用 admin / 123 或您的新账号。")

# --- 5. 主工作台 (Main App) ---
def main_app():
    user = st.session_state.username
    balance = st.session_state.user_info.get('balance', 0)
    
    # --- 侧边栏 ---
    with st.sidebar:
        st.title("🐶 口袋狗工作台")
        st.info(f"👤 用户：{user}")
        
        # 钱包展示
        st.metric(label="剩余字数额度", value=balance)
        if balance < 500:
            st.warning("⚠️ 余额不足，请充值")
        
        st.markdown("---")
        
        # 充值模块
        st.subheader("💎 卡密充值")
        code_input = st.text_input("输入兑换码", placeholder="例如: 1000-xxxx")
        code = code_input.strip() # 去空格
        
        if st.button("立即兑换", use_container_width=True):
            coupons = load_json(COUPON_DB)
            if code in coupons and coupons[code]['status'] == 'unused':
                add_words = coupons[code]['words']
                # 1. 核销卡密
                coupons[code]['status'] = 'used'
                coupons[code]['used_by'] = user
                save_json(COUPON_DB, coupons)
                # 2. 增加余额
                update_balance(user, add_words)
                st.balloons()
                st.success(f"充值成功！账户增加 {add_words} 字")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 无效卡密或已被使用")
        
        # 购买链接
        st.markdown("---")
        st.markdown("#### 🛒 如何获取卡密？")
        # 这里放你的发卡网链接 https://hwv430.blogspot.com/
        st.markdown("[👉 点击这里购买充值卡 (3元起)](#)")

        # 管理员调试工具
        with st.expander("👨‍💻 管理员工具"):
            if st.checkbox("显示可用卡密"):
                coupons = load_json(COUPON_DB)
                valid = [k for k,v in coupons.items() if v['status'] == 'unused']
                if valid:
                    st.code(valid[0])
                    st.write(f"剩余库存: {len(valid)} 张")
                else:
                    st.write("无可用库存")
            if st.button("退出登录"):
                st.session_state.logged_in = False
                st.rerun()

    # --- 主界面 ---
    st.header("📝 口袋狗2026专业论文降重 ")
    
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.subheader("原文输入")
        text = st.text_area("请粘贴需要降重的文本", height=500, placeholder="在此处粘贴...")
        text_len = len(text)
        st.caption(f"当前字数: {text_len} | 您的余额: {balance}")
        
        # 按钮状态逻辑
        if text_len == 0:
            btn_state = True # 为了美观不禁用，但点击会提示
            btn_txt = "🚀 请先输入内容"
        elif text_len > balance:
            btn_state = False # 余额不足禁用
            btn_txt = f"❌ 余额不足 (需 {text_len} 字)"
        else:
            btn_state = True
            btn_txt = f"🚀 开始降重 (扣除 {text_len} 字)"

        start_btn = st.button(btn_txt, type="primary", disabled=(text_len > balance), use_container_width=True)

    if start_btn:
        if text_len == 0:
            st.warning("请先输入内容！")
            st.stop()
            
        if "sk-" not in SYSTEM_API_KEY:
            st.error("❌ 管理员未配置  Key，请联系客服。")
            st.stop()

        with col_out:
            st.subheader("降重结果")
            box = st.empty()
            box.info("🔄  正在深度思考重写策略 (预计 10-20秒)...")
            
            try:
                # 调用 DeepSeek API
                client = OpenAI(api_key=SYSTEM_API_KEY, base_url="https://api.deepseek.com")
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一个论文去痕修改专家。请重写用户文本，目的是大幅降低AIGC检测率。要求：1. 彻底打破原有句式结构，多用倒装、插入语。2. 替换所有AI高频词（如'综上所述'、'这一点'）。3. 模拟人类写作的离散度（Burstiness）。你是一个学术论文修改专家。目标是规避 AI 检测。4. 增加语句结构的复杂度，混合使用倒装句、强调句。5. 替换常见的 AI 惯用词（如‘显著地’、‘此外’）为更地道的学术表达。6. 引入适度的‘困惑度’（Perplexity），模拟人类思维的非线性跳跃。7. 保持原文核心逻辑不变，但彻底重组句式。请直接输出修改后的文本，不要废话。"},
                        {"role": "user", "content": text},
                    ],
                    stream=False
                )
                
                result = response.choices[0].message.content
                
                # 扣费
                update_balance(user, -text_len)
                
                # 显示结果
                box.success(f"✅ 成功！已扣除 {text_len} 字。")
                st.text_area("建议修改为：", value=result, height=500)
                
            except Exception as e:
                box.error(f"❌ 出错啦：{e}")
                st.write("请检查网络或  Key 余额。")

# --- 6. 程序入口 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_page()