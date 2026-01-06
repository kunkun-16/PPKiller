import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- 1. 全局页面配置 ---
st.set_page_config(
    page_title="写作狗AI降重 - 2026专业版",
    page_icon="🐶",
    layout="wide"
)

# --- 2. 核心配置 (请务必填入你的信息) ---
# 粘贴你从 Google 表格“共享”获取的链接
SHEET_URL = "https://docs.google.com/spreadsheets/d/1jbHWvatK4VGlSgPYgBLXF9CqQugceCw9T20iXuXAGMg/edit?usp=sharing"

# 填入你的 DeepSeek API Key
SYSTEM_API_KEY = "sk-8b582db9fd144de4935b1957db1deb2e"

# --- 3. 数据库连接工具 (Service Account 版) ---
# 记得把下面这个链接换成你自己的 Google 表格链接！
SHEET_URL = "https://docs.google.com/spreadsheets/d/1jbHWvatK4VGlSgPYgBLXF9CqQugceCw9T20iXuXAGMg/edit?usp=sharing"

def get_db_connection():
    # 建立连接，会自动使用 Secrets 里的服务账号密钥
    return st.connection("gsheets", type=GSheetsConnection)

# --- 3. 数据库连接工具 (修正版) ---

def load_users():
    conn = get_db_connection()
    # 强制指定读取 "Sheet1" (或者你表格左下角显示的那个名字)
    return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)

def sync_user_to_cloud(updated_df):
    conn = get_db_connection()
    # 强制指定写入同一个 "Sheet1"
    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)

# --- 4. 登录与注册功能 (已适配云端) ---
def login_page():
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.image("https://img.freepik.com/free-vector/blogging-concept-illustration_114360-1038.jpg", width=500)
    
    with col2:
        st.title("让学术写作更简单")
        tab1, tab2 = st.tabs(["🔐 账号登录", "🆕 快速注册"])
        
        df = load_users() # 预加载数据

        with tab1:
            u = st.text_input("用户名", key="l_user")
            p = st.text_input("密码", type="password", key="l_pass")
            if st.button("立即登录", type="primary", use_container_width=True):
                # 匹配账号密码
                user_match = df[(df['username'].astype(str) == u) & (df['password'].astype(str) == p)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    # 获取当前用户的余额
                    st.session_state.balance = int(user_match.iloc[0]['balance'])
                    st.success("登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("账号或密码错误")

        with tab2:
            reg_u = st.text_input("设置用户名", key="r_user")
            reg_p = st.text_input("设置密码", type="password", key="r_pass")
            if st.button("提交注册", use_container_width=True):
                if reg_u in df['username'].astype(str).values:
                    st.error("用户名已存在")
                elif not reg_u or not reg_p:
                    st.warning("请填写完整")
                else:
                    # 将新用户拼接到现有数据中
                    new_row = pd.DataFrame([{"username": reg_u, "password": reg_p, "balance": 200}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    sync_user_to_cloud(updated_df)
                    st.success("注册成功！送200字，请切换到登录页。")

# --- 5. 主程序 (降重工作台) ---
def main_app():
    user = st.session_state.username
    
    # 侧边栏：显示余额和登出
    with st.sidebar:
        st.title("🐶 个人中心")
        # 每次刷新重新从云端取一次余额，确保准确
        df = load_users()
        current_balance = int(df[df['username'] == user].iloc[0]['balance'])
        st.metric("剩余字数额度", value=f"{current_balance} 字")
        
        if st.button("退出登录"):
            st.session_state.logged_in = False
            st.rerun()
            
        st.markdown("---")
        st.caption("提示：如需充值请联系管理员手动修改余额")

    # 主界面
    st.header("📝论文降重")
    col_in, col_out = st.columns(2)

    with col_in:
        text = st.text_area("输入论文原文", height=400)
        word_count = len(text)
        can_run = word_count > 0 and word_count <= current_balance
        
        if st.button("🚀 开始降重", type="primary", disabled=not can_run, use_container_width=True):
            with col_out:
                msg = st.empty()
                msg.info("AI 正在深度重写...")
                try:
                    client = OpenAI(api_key=SYSTEM_API_KEY, base_url="https://api.deepseek.com")
                    resp = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是一个论文去痕修改专家。请重写用户文本，目的是大幅降低AIGC检测率。要求：1. 彻底打破原有句式结构，多用倒装、插入语。2. 替换所有AI高频词（如'综上所述'、'这一点'）。3. 模拟人类写作的离散度（Burstiness）。你是一个学术论文修改专家。目标是规避 AI 检测。4. 增加语句结构的复杂度，混合使用倒装句、强调句。5. 替换常见的 AI 惯用词（如‘显著地’、‘此外’）为更地道的学术表达。6. 引入适度的‘困惑度’（Perplexity），模拟人类思维的非线性跳跃。7. 保持原文核心逻辑不变，但彻底重组句式。请直接输出修改后的文本，不要废话。"},
                                 {"role": "user", "content": text}]
                    )
                    res = resp.choices[0].message.content
                    
                    # 扣费：更新云端表格
                    df.loc[df['username'] == user, 'balance'] = current_balance - word_count
                    sync_user_to_cloud(df)
                    
                    msg.success(f"完成！扣除 {word_count} 字")
                    st.text_area("结果", value=res, height=400)
                except Exception as e:
                    msg.error(f"出错：{e}")

# --- 6. 程序入口 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_page()