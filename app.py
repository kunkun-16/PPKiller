import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- 1. 全局页面配置 ---
st.set_page_config(
    page_title="作业狗AI降重 - 2026专业版",
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
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)

    # 1. 先强制转为字符串
    df['username'] = df['username'].astype(str)
    df['password'] = df['password'].astype(str)

    # 2. 【核心修复】去掉讨厌的 ".0"
    # 正则表达式的意思是：如果字符串结尾是 .0，就把它删掉
    df['username'] = df['username'].str.replace(r'\.0$', '', regex=True)
    df['password'] = df['password'].str.replace(r'\.0$', '', regex=True)

    # 3. 余额转数字
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)

    return df

def sync_user_to_cloud(updated_df):
    conn = get_db_connection()
    # 强制指定写入同一个 "Sheet1"
    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)

# --- 4. 登录与注册功能 (已适配云端) ---
def login_page():
    st.title("📄 Paper Killer - 让写作更简单")

    # 1. 侧边栏：登录/注册切换
    # 这一步是为了防止页面刷新后状态丢失
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

    # 使用 Tab 标签页来切换，体验更好
    tab1, tab2 = st.tabs(["🔐 登录账号", "📝 快速注册"])

    # --- 登录部分 ---
    with tab1:
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pass")
        
        if st.button("🚀 立即登录", use_container_width=True):
            if not username or not password:
                st.warning("账号密码不能为空！")
                return

            try:
                # 加载最新的用户数据
                df = load_users()
                
                # 清理输入内容的空格
                u = username.strip()
                p = password.strip()

                # 比对查找
                user_match = df[(df['username'] == u) & (df['password'] == p)]

                if not user_match.empty:
                    # 登录成功！保存状态
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.session_state['balance'] = float(user_match.iloc[0]['balance'])
                    st.success("登录成功！正在跳转...")
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误")
            
            except Exception as e:
                st.error(f"连接数据库失败: {e}")

    # --- 注册部分 ---
    with tab2:
        new_user = st.text_input("设置用户名", key="reg_user")
        new_pass = st.text_input("设置密码", type="password", key="reg_pass")
        
        if st.button("✨ 提交注册", use_container_width=True):
            if not new_user or not new_pass:
                st.warning("请填写完整信息")
                return
                
            try:
                df = load_users()
                if new_user in df['username'].values:
                    st.error("该用户名已被占用")
                else:
                    # 创建新用户数据（送 200 字）
                    new_row = pd.DataFrame([{
                        "username": new_user, 
                        "password": new_pass, 
                        "balance": 200
                    }])
                    # 合并并上传
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    sync_user_to_cloud(updated_df)
                    
                    st.success("注册成功！请切换到登录页登录。")
                    st.balloons()
            except Exception as e:
                st.error(f"注册失败: {e}")

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
    st.header("📝AI杀手")
    col_in, col_out = st.columns(2)

    with col_in:
        text = st.text_area("输入作业原文", height=400)
        word_count = len(text)
        can_run = word_count > 0 and word_count <= current_balance
        
        if st.button("🚀 开始kill...降重", type="primary", disabled=not can_run, use_container_width=True):
            with col_out:
                msg = st.empty()
                msg.info("正在挥汗改作业...")
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