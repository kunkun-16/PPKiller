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
    # 读取数据
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
    
    # --- 🛠️ 关键修复开始 ---
    # 1. 把“用户名”和“密码”强制转为字符串 (String)
    # 这样 "123" 就能匹配 123 了
    df['username'] = df['username'].astype(str)
    df['password'] = df['password'].astype(str)
    
    # 2. 把“余额”强制转为数字 (Numeric)
    # 防止表格里有空格导致扣费计算报错，errors='coerce' 会把非数字变成 NaN
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
    # --- 🛠️ 关键修复结束 ---
    
    return df

def sync_user_to_cloud(updated_df):
    conn = get_db_connection()
    # 强制指定写入同一个 "Sheet1"
    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)

# --- 4. 登录与注册功能 (已适配云端) ---
def login_page():
    st.title("🔍 登录故障诊断模式")
    
    # 1. 尝试读取数据
    try:
        df = load_users()
        st.success("✅ 数据库连接成功！已读取到数据。")
    except Exception as e:
        st.error(f"❌ 严重错误：数据库完全读不出来。\n原因：{e}")
        st.stop()

    # 2. 【核心诊断】把程序看到的数据直接打印出来
    st.warning("👇 只有看清下面这三点，才能找到登不进去的原因：")
    
    st.write("1. 表头也就是列名 (Columns)：")
    st.write(df.columns.tolist()) 
    # ⚠️ 检查：是不是叫 'username ' (后面带空格)？或者 'User Name'？代码里必须一模一样！

    st.write("2. 前两行真实数据 (Data)：")
    st.dataframe(df.head(2))
    # ⚠️ 检查：这里面有你的账号吗？如果全是空的，说明 sheet 没选对。

    st.write("3. 数据类型 (Types)：")
    st.write(df.dtypes)
    # ⚠️ 检查：username 和 password 必须是 object (也就是字符串)。

    st.divider() # 分割线

    # 3. 原来的登录界面
    with st.tabs(["登录", "注册"]):
        st.header("请尝试登录")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")

        if st.button("登录"):
            # 4. 【比对诊断】看看输入的账号和表格里的到底哪里不一样
            # 清理一下输入（去空格）
            u = username.strip()
            p = password.strip()
            
            st.info(f"正在匹配用户: '{u}'，密码: '{p}'")
            
            # 在表格里找这一行
            user_match = df[df['username'] == u]
            
            if user_match.empty:
                st.error("❌ 找不到用户名！(请对比上面显示的真实数据)")
            else:
                # 如果用户名找到了，检查密码
                real_password = str(user_match.iloc[0]['password']).strip()
                st.write(f"🔍 找到用户了，表格里的真实密码是: '{real_password}'")
                
                if real_password == p:
                    st.success("✅ 密码匹配成功！(登录逻辑通了)")
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.session_state['balance'] = user_match.iloc[0]['balance']
                    st.rerun()
                else:
                    st.error(f"❌ 密码错误！你输入的是 '{p}'，但表格里记的是 '{real_password}'")

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