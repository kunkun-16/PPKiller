import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. 页面配置 & 样式注入 ---
st.set_page_config(
    page_title="作业狗 AI Killer ",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 动漫风格登录页 + 专业版主页 CSS
CUSTOM_CSS = """
<style>
    /* 全局字体 */
    .stApp {
        font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    
    /* 登录页背景 (二次元风格) */
    .login-bg {
        background-image: url("https://api.paugram.com/wallpaper?source=gh"); /* 随机二次元壁纸接口 */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        padding: 50px;
        border-radius: 15px;
    }
    
    /* 玻璃拟态卡片 */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }

    /* 商业化卡片样式 */
    .pricing-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s;
        background-color: white;
    }
    .pricing-card:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border-color: #ff4b4b;
    }
    .price-tag {
        color: #ff4b4b;
        font-size: 1.5em;
        font-weight: bold;
    }
    
    /* 隐藏默认 Streamlit 菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- 2. 数据库连接配置 (Service Account) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1jbHWvatK4VGlSgPYgBLXF9CqQugceCw9T20iXuXAGMg/edit?usp=sharing" # ⚠️⚠️⚠️ 请务必换回你的链接 ⚠️⚠️⚠️

def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_users():
    conn = get_db_connection()
    # 强制读取 Sheet1
    df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
    # 类型清洗
    df['username'] = df['username'].astype(str).str.replace(r'\.0$', '', regex=True)
    df['password'] = df['password'].astype(str).str.replace(r'\.0$', '', regex=True)
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
    return df

def sync_user_to_cloud(updated_df):
    conn = get_db_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)

# --- 3. 核心功能：卡密充值逻辑 ---
def redeem_code(username, code_input):
    """验证卡密并充值"""
    conn = get_db_connection()
    try:
        # 1. 读取卡密表 (RedemptionCodes)
        codes_df = conn.read(spreadsheet=SHEET_URL, worksheet="RedemptionCodes", ttl=0)
        
        # 2. 查找卡密
        code_input = code_input.strip()
        mask = (codes_df['code'].astype(str) == code_input) & (codes_df['status'] == 'unused')
        
        if not codes_df[mask].empty:
            # 找到有效卡密
            idx = codes_df[mask].index[0]
            add_words = int(codes_df.at[idx, 'words'])
            
            # 3. 更新卡密状态为已使用
            codes_df.at[idx, 'status'] = 'used'
            codes_df.at[idx, 'used_by'] = username
            codes_df.at[idx, 'used_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.update(spreadsheet=SHEET_URL, worksheet="RedemptionCodes", data=codes_df)
            
            # 4. 更新用户余额
            users_df = load_users()
            user_idx = users_df[users_df['username'] == username].index[0]
            current_bal = users_df.at[user_idx, 'balance']
            users_df.at[user_idx, 'balance'] = current_bal + add_words
            sync_user_to_cloud(users_df)
            
            # 5. 更新 Session
            st.session_state['balance'] = current_bal + add_words
            return True, add_words
        else:
            return False, "卡密无效或已被使用"
            
    except Exception as e:
        return False, f"系统错误: {e}"

# --- 4. 界面函数：登录页 (动漫风) ---
def login_page():
    # 使用列布局来居中显示登录框
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-bg">', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        st.title("🐾 Paper Killer 登录")
        st.markdown("### 作业狗AI论文降重助手")
        
        tab1, tab2 = st.tabs(["🔐 账号登录", "✨ 快速注册"])
        
        with tab1:
            u = st.text_input("用户名", key="l_u")
            p = st.text_input("密码", type="password", key="l_p")
            if st.button("🚀 进入工作台", use_container_width=True, type="primary"):
                if u and p:
                    try:
                        df = load_users()
                        user = df[(df['username'] == u) & (df['password'] == p)]
                        if not user.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = u
                            st.session_state['balance'] = float(user.iloc[0]['balance'])
                            st.success("欢迎回来！")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("账号或密码错误")
                    except Exception as e:
                        st.error(f"连接失败: {e}")

        with tab2:
            ru = st.text_input("设置用户名", key="r_u")
            rp = st.text_input("设置密码", type="password", key="r_p")
            if st.button("立即注册 (赠送200字)", use_container_width=True):
                if ru and rp:
                    try:
                        df = load_users()
                        if ru in df['username'].values:
                            st.error("用户已存在")
                        else:
                            new_row = pd.DataFrame([{"username": ru, "password": rp, "balance": 200}])
                            sync_user_to_cloud(pd.concat([df, new_row], ignore_index=True))
                            st.success("注册成功！请登录")
                    except Exception as e:
                        st.error(f"注册失败: {e}")

        st.markdown('</div></div>', unsafe_allow_html=True)

# --- 5. 界面函数：主程序 (已增加 1000 字限制) ---
def main_app():
    # 侧边栏：用户信息与导航
    with st.sidebar:
        # 使用 Dicebear 生成头像
        st.image(f"https://api.dicebear.com/7.x/avataaars/svg?seed={st.session_state['username']}", width=100)
        st.markdown(f"### Hi, {st.session_state['username']}")
        
        balance = st.session_state.get('balance', 0)
        st.metric("剩余字数", f"{int(balance)} 字")
        
        st.divider()
        menu = st.radio("功能导航", ["📝 论文降重", "💎 充值中心", "👤 个人中心"])
        
        if st.button("退出登录"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 右侧主界面
    if menu == "📝 论文降重":
        st.header("📝 降重工作台")
        st.info("💡 提示：作业狗正在挥汗加速中...")
        
        # 定义单次限制
        MAX_ONCE_LIMIT = 1000

        col1, col2 = st.columns([1, 1])
        with col1:
            text_input = st.text_area("请输入需要降重的文本", height=400, placeholder="在此粘贴您的论文段落...")
            word_count = len(text_input)
            
            # --- 🛠️ 修改点 1：字数提示与警告 ---
            if word_count > MAX_ONCE_LIMIT:
                st.markdown(f":red[⚠️ 当前字数: {word_count} / {MAX_ONCE_LIMIT} (已超限)]")
            else:
                st.caption(f"当前字数: {word_count} / {MAX_ONCE_LIMIT}")
        
        with col2:
            st.write("降重结果预览")
            result_area = st.empty()
            result_area.text_area("结果将显示在这里", height=400, disabled=True)

        # 操作栏
        st.divider()
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col2:
            if st.button("🚀 开始降重 (扣除字数)", type="primary", use_container_width=True):
                current_bal = st.session_state['balance']
                
                # --- 🛠️ 修改点 2：增加拦截逻辑 ---
                if word_count == 0:
                    st.warning("请先输入内容！")
                elif word_count > MAX_ONCE_LIMIT:
                    st.error(f"❌ 字数超限！单次最多支持 {MAX_ONCE_LIMIT} 字，请将文本分段后重试。")
                elif word_count > current_bal:
                    st.error(f"余额不足！需要 {word_count} 字，当前仅剩 {int(current_bal)} 字。请前往充值中心。")
                else:
                    # --- 这里填入你的真实 API ---
                    SYSTEM_API_KEY = "sk-8b582db9fd144de4935b1957db1deb2e"  # ⚠️⚠️⚠️ 记得填回你的 Key ⚠️⚠️⚠️
                    
                    # 初始化客户端
                    from openai import OpenAI
                    try:
                        client = OpenAI(api_key=SYSTEM_API_KEY, base_url="https://api.deepseek.com")
                        
                        with st.spinner("作业狗正在极速降重中..."):
                            # 发送真实请求
                            resp = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[
                                    {"role": "system", "content": "你是一个学术降重专家，请重写用户文本，目的是大幅降低AIGC检测率，规避 AI 检测。要求：1. 彻底打破原有句式结构，多用倒装、插入语。2. 替换所有AI高频词（如'综上所述'、'这一点'）。3. 模拟人类写作的离散度（Burstiness）。4. 增加语句结构的复杂度，混合使用倒装句、强调句。5. 替换常见的 AI 惯用词（如‘显著地’、‘此外’）为更地道的学术表达。6. 引入适度的‘困惑度’（Perplexity），模拟人类思维的非线性跳跃。7. 保持原文愿意不变，核心逻辑不变，但彻底重组句式。请直接输出修改后的文本，不要废话。"},
                                    {"role": "user", "content": text_input}
                                ]
                            )
                            # 获取结果
                            real_result = resp.choices[0].message.content
                            
                            # 扣费逻辑
                            df = load_users()
                            idx = df[df['username'] == st.session_state['username']].index[0]
                            new_bal = current_bal - word_count
                            df.at[idx, 'balance'] = new_bal
                            sync_user_to_cloud(df)
                            
                            # 更新 Session 和界面
                            st.session_state['balance'] = new_bal
                            result_area.text_area("降重结果", value=real_result, height=400)
                            st.success(f"成功！消耗 {word_count} 字")
                            
                    except Exception as e:
                        st.error(f"运行出错: {e}")

    elif menu == "💎 充值中心":
        st.header("💎 会员充值中心")
        st.markdown("选择适合您的套餐，购买卡密后激活即可。")
        
        cols = st.columns(5)
        packages = [
            ("尝鲜版", "1,000 字", "¥ 3"),
            ("标准版", "2,000 字", "¥ 5"),
            ("进阶版", "5,000 字", "¥ 12"),
            ("专业版", "10,000 字", "¥ 22"),
            ("尊享版", "20,000 字", "¥ 40"),
        ]
        
        for i, (name, words, price) in enumerate(packages):
            with cols[i]:
                st.markdown(f"""
                <div class="pricing-card">
                    <h4>{name}</h4>
                    <div class="price-tag">{price}</div>
                    <p>{words}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("第一步：获取卡密")
            st.markdown("""
            请扫描下方二维码或联系客服购买卡密：
            - **客服微信**：PaperKiller_Admin
            - **付款备注**：购买套餐类型
            """)
        
        with c2:
            st.subheader("第二步：激活卡密")
            code_input = st.text_input("请输入您的卡密 (Redemption Code)")
            if st.button("立即激活", type="primary"):
                if code_input:
                    with st.spinner("正在验证卡密..."):
                        success, msg = redeem_code(st.session_state['username'], code_input)
                        if success:
                            st.balloons()
                            st.success(f"充值成功！已增加 {msg} 字。")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.warning("请输入卡密")

    elif menu == "👤 个人中心":
        st.header("个人档案")
        st.write(f"当前用户: {st.session_state['username']}")
        st.write(f"当前余额: {st.session_state['balance']} 字")
        st.info("更多功能开发中...")

# --- 6. 主入口 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()