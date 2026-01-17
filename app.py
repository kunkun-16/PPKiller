import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sqlite3
import json
import os

# --- 1. 页面配置 & 样式注入 ---
st.set_page_config(
    page_title="Paper Killer Pro",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="collapsed",  # 登录页默认收起侧边栏，更美观
)

def set_bg(state):
    """
    根据登录状态动态切换背景
    state: 'login' (显示动漫背景) 或 'main' (显示纯白背景)
    """
    if state == 'login':
        # 这里用的是 Unsplash 的高清动漫风风景图，你可以随意换
        bg_url = "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=1920"
        
        css = f"""
        <style>
            /* 1. 背景铺满 */
            .stApp {{
                background-image: url("{bg_url}") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            
            /* 2. 隐藏 Header */
            header[data-testid="stHeader"] {{
                background-color: rgba(0,0,0,0) !important;
            }}
            
            /* 3. 【核心技巧】自动美化登录框所在的“中间列” */
            /* 这里的逻辑是：找到第 2 个列 (column)，给它加玻璃特效 */
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {{
                background: rgba(255, 255, 255, 0.85); /* 半透明白 */
                backdrop-filter: blur(20px);             /* 磨砂质感 */
                border-radius: 20px;                     /* 圆角 */
                padding: 40px;                           /* 内边距 */
                box-shadow: 0 10px 40px rgba(0,0,0,0.2); /* 阴影 */
                border: 1px solid rgba(255,255,255,0.5); /* 描边 */
            }}
            
            /* 输入框美化 */
            .stTextInput input {{
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #ddd;
            }}
            
            /* 隐藏页脚 */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
        </style>
        """
    else:
        # 主界面 CSS (保持不变)
        css = """
        <style>
            .stApp {background-image: none !important; background-color: #f8f9fa !important;}
            header[data-testid="stHeader"] {background-color: rgba(255,255,255,1) !important;}
            .pricing-card {
                border: 1px solid #e0e0e0; border-radius: 12px; padding: 25px;
                text-align: center; background-color: white; transition: all 0.3s ease;
            }
            .pricing-card:hover {
                transform: translateY(-5px); box-shadow: 0 10px 20px rgba(255, 75, 75, 0.2); border-color: #ff4b4b;
            }
            .price-tag {color: #ff4b4b; font-size: 1.8em; font-weight: bold; margin: 10px 0;}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

DB_PATH = "paper_killer.db"

# 通义千问 / 代理 API 配置（请在此处填入您的 API Key 和模型）
# ⚠️ 已为你填入当前使用的 key，如需更换只改这一行即可
QWEN_API_KEY = "sk-LoIz4cW9EQC2Dz05vhCf5QBCNwpXHX6wrak5vsGtZecRqsOH"
QWEN_MODEL = "Qwen3-235B-A22B"  # 代理平台上的模型名称，例如 Qwen3-235B-A22B


def get_db_connection():
    """获取 SQLite 连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    初始化本地 SQLite 数据库：
    - 创建 users 表
    - 创建 coupons 表
    - 创建 usage_logs 表（使用记录）
    - 创建 recharge_logs 表（充值记录）
    - 从 users.json 和 coupons.json 导入初始数据（如果存在且未导入）
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 创建用户表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # 创建卡密表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            words INTEGER NOT NULL,
            status TEXT NOT NULL,
            used_by TEXT,
            used_time TEXT
        )
        """
    )

    # 创建使用记录表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            words_used INTEGER NOT NULL,
            operation_time TEXT NOT NULL,
            operation_type TEXT DEFAULT '降重'
        )
        """
    )

    # 创建充值记录表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recharge_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            code TEXT,
            words_added INTEGER NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            recharge_time TEXT NOT NULL
        )
        """
    )

    # 从 users.json 导入用户（如果文件存在）
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            users_data = json.load(f)
        for username, info in users_data.items():
            # 检查用户是否已存在
            cur.execute("SELECT username FROM users WHERE username = ?", (username,))
            existing = cur.fetchone()
            if not existing:
                # 用户不存在，插入
                cur.execute(
                    "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                    (username, str(info.get("password", "")), int(info.get("balance", 0))),
                )
            else:
                # 用户存在，确保密码和余额正确（特别是主账号）
                cur.execute(
                    "UPDATE users SET password = ?, balance = ? WHERE username = ?",
                    (str(info.get("password", "")), int(info.get("balance", 0)), username),
                )
    
    # 确保 admin 账号一定存在（即使 users.json 不存在或没有 admin）
    cur.execute("SELECT username FROM users WHERE username = ?", ("admin",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
            ("admin", "123", 999999),
        )

    # 从 coupons.json 导入卡密（如果文件存在且表为空）
    cur.execute("SELECT COUNT(*) AS c FROM coupons")
    if cur.fetchone()["c"] == 0 and os.path.exists("coupons.json"):
        with open("coupons.json", "r", encoding="utf-8") as f:
            coupons_data = json.load(f)
        for code, info in coupons_data.items():
            cur.execute(
                """
                INSERT OR REPLACE INTO coupons (code, words, status, used_by, used_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    code,
                    int(info.get("words", 0)),
                    info.get("status", "unused"),
                    info.get("used_by"),
                    info.get("used_time"),
                ),
            )

    conn.commit()
    conn.close()


def load_users():
    """从 SQLite 读取所有用户为 DataFrame"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT username, password, balance FROM users", conn)
    conn.close()
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0)
    return df


def redeem_code(username, code_input):
    """验证卡密并充值（SQLite 版），并记录充值日志"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        code_input = code_input.strip()

        # 1. 查找未使用的卡密
        cur.execute(
            "SELECT code, words, status FROM coupons WHERE code = ? AND status = 'unused'",
            (code_input,),
        )
        row = cur.fetchone()

        if not row:
            return False, "卡密无效、已被使用或不存在"

        add_words = int(row["words"])

        # 2. 获取充值前余额
        cur.execute("SELECT balance FROM users WHERE username = ?", (username,))
        user_row = cur.fetchone()
        balance_before = int(user_row["balance"]) if user_row else 0

        # 3. 标记卡密为已使用
        used_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            UPDATE coupons
            SET status = 'used', used_by = ?, used_time = ?
            WHERE code = ?
            """,
            (username, used_time, code_input),
        )

        # 4. 更新用户余额
        cur.execute(
            "UPDATE users SET balance = balance + ? WHERE username = ?",
            (add_words, username),
        )

        # 5. 读取最新余额
        cur.execute(
            "SELECT balance FROM users WHERE username = ?",
            (username,),
        )
        user_row = cur.fetchone()
        balance_after = int(user_row["balance"]) if user_row else 0

        # 6. 记录充值日志
        cur.execute(
            """
            INSERT INTO recharge_logs (username, code, words_added, balance_before, balance_after, recharge_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, code_input, add_words, balance_before, balance_after, used_time),
        )

        conn.commit()
        st.session_state["balance"] = balance_after
        return True, add_words

    except Exception as e:
        conn.rollback()
        return False, f"系统错误: {e}"
    finally:
        conn.close()


def export_db_to_json() -> str:
    """导出当前 SQLite 数据为 JSON 字符串"""
    conn = get_db_connection()
    cur = conn.cursor()

    # 导出用户
    cur.execute("SELECT username, password, balance FROM users")
    users = {}
    for row in cur.fetchall():
        users[row["username"]] = {
            "password": row["password"],
            "balance": int(row["balance"]),
        }

    # 导出卡密
    cur.execute("SELECT code, words, status, used_by, used_time FROM coupons")
    coupons = {}
    for row in cur.fetchall():
        coupons[row["code"]] = {
            "words": int(row["words"]),
            "status": row["status"],
            "used_by": row["used_by"],
            "used_time": row["used_time"],
        }

    conn.close()

    data = {
        "users": users,
        "coupons": coupons,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

# --- 4. 界面函数：登录页 (带海报版) ---
# --- 4. 界面函数：登录页 (带海报版) ---
def login_page():
    set_bg('login')
    
    # 三列布局：1:1.2:1，中间稍微宽一点点
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # 1. 【新增】顶部海报/Logo
       with col2:
        # --- 🔴 删除旧代码，从这里开始替换 ---
        
        # 1. 创建两个子列来实现“水平并排”
        # 比例 [1.2, 3] 表示左边占 1.2 份宽度，右边占 3 份宽度
        # gap="small" 让图文靠得近一点
        head_c1, head_c2 = st.columns([1.2, 3], gap="small")
        
        # 2. 左边放图片 (Logo)
        with head_c1:
            # 确保文件名和 GitHub 上的一模一样 (注意 .png 后缀)
            st.image("logo.jpg", width=110, use_container_width=False)
            
        # 3. 右边放文字 (标题)
        with head_c2:
            # 使用 HTML/CSS 精细控制对齐
            # padding-top: 15px 是为了让文字下沉，和图片的中心对齐
            st.markdown("""
                <div style="padding-top: 15px; text-align: left;">
                    <h1 style="margin: 0; padding: 0; font-size: 34px; color: #2c3e50; font-weight: 800; line-height: 1.2;">
                        Paper Killer
                    </h1>
                    <p style="margin: 5px 0 0 0; color: #ff4b4b; font-size: 14px;font-weight: bold">
                        ✨作业狗AI降AI助手
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
        # --- 🟢 替换结束 ---
        
        # 下面是原来的 tab 代码，保持不动
        st.markdown("<br>", unsafe_allow_html=True) # 加个空行隔开
        
        # 3. 登录/注册表单
        tab1, tab2 = st.tabs(["🔐 账号登录", "🎁 快速注册"])
        
        with tab1:
            u = st.text_input("用户名", key="l_u", placeholder="请输入账号")
            p = st.text_input("密码", type="password", key="l_p", placeholder="请输入密码")
            st.markdown(" <br>", unsafe_allow_html=True)
            
            if st.button("🚀 登录工作台", use_container_width=True, type="primary"):
                if u and p:
                    try:
                        # 使用 SQLite 校验用户
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT username, balance FROM users WHERE username = ? AND password = ?",
                            (u, p),
                        )
                        row = cur.fetchone()
                        conn.close()

                        if row:
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = row["username"]
                            st.session_state['balance'] = float(row["balance"])
                            st.toast("登录成功！", icon="🎉")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ 账号或密码错误")
                    except Exception as e:
                        st.error(f"本地数据库错误: {e}")
                        # 调试信息：显示数据库中的用户
                        try:
                            conn_debug = get_db_connection()
                            cur_debug = conn_debug.cursor()
                            cur_debug.execute("SELECT username, password FROM users")
                            users_list = cur_debug.fetchall()
                            conn_debug.close()
                            if users_list:
                                st.info(f"数据库中的用户: {', '.join([row[0] for row in users_list])}")
                        except:
                            pass

        with tab2:
            ru = st.text_input("设置用户名", key="r_u", placeholder="建议使用字母或数字")
            rp = st.text_input("设置密码", type="password", key="r_p", placeholder="6位以上字符")
            st.markdown(" <br>", unsafe_allow_html=True)
            
            if st.button("✨ 立即注册 (领200字)", use_container_width=True):
                if ru and rp:
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        # 检查是否存在
                        cur.execute("SELECT 1 FROM users WHERE username = ?", (ru,))
                        if cur.fetchone():
                            conn.close()
                            st.error("⚠️ 用户名已存在")
                        else:
                            cur.execute(
                                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                                (ru, rp, 200),
                            )
                            conn.commit()
                            conn.close()
                            st.balloons()
                            st.success("✅ 注册成功！请切换到登录页。")
                    except Exception as e:
                        st.error(f"注册失败: {e}")

# --- 5. 界面函数：主程序 (已增加 1000 字限制) ---
def main_app():
    # 切换回主界面背景
    set_bg('main') 
    
    # ... 下面是原本的代码 ...
    with st.sidebar:
        # ...
    # 侧边栏：用户信息与导航
        # 使用 Dicebear 生成头像
        st.image(f"https://api.dicebear.com/7.x/avataaars/svg?seed={st.session_state['username']}", width=100)
        st.markdown(f"### Hi, {st.session_state['username']}")
        
        balance = st.session_state.get('balance', 0)
        st.metric("剩余字数", f"{int(balance)} 字")
        
        st.divider()
        
        # 根据用户身份显示菜单
        is_admin = st.session_state.get('username') == 'admin'
        if is_admin:
            menu = st.radio("功能导航", ["📝 论文降AI", "💎 充值中心", "👤 个人中心", "⚙️ 管理员功能"])
        else:
            menu = st.radio("功能导航", ["📝 论文降AI", "💎 充值中心", "👤 个人中心"])
        
        if st.button("退出登录"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 右侧主界面
    if menu == "📝 论文降AI":
        st.header("📝 降AI工作台")
        
        # 显示当前使用的模型
        model_display = {
            'qwen-turbo': '🚀 快速版',
            'qwen-plus': '⚡ 平衡版',
            'qwen-max': '🔥 最强版'
        }
        st.info(f"💡作业狗正在加速中，请耐心等待...")
        
        # 定义单次限制
        MAX_ONCE_LIMIT = 5000

        col1, col2 = st.columns([1, 1])
        with col1:
            # 左侧：输入框
            text_input = st.text_area("请输入需要降AI的文本", height=400, placeholder="在此粘贴您的文本段落...")
            word_count = len(text_input)
            
            # 左侧底部：字数统计
            if word_count > MAX_ONCE_LIMIT:
                st.markdown(f":red[⚠️ 当前字数: {word_count} / {MAX_ONCE_LIMIT} (已超限)]")
            else:
                st.caption(f"当前字数: {word_count} / {MAX_ONCE_LIMIT}")
        
        with col2:
            # 右侧：结果框
            # 1. 删掉了原来的 st.write("降重结果预览")，防止顶部不齐
            
            # 2. 创建占位容器
            result_area = st.empty()
            
            # 3. 将标题 "降重结果预览" 直接作为 text_area 的 label 参数
            # 这样左右两边的标题高度就完全一样了
            result_area.text_area("降AI结果预览", height=400, disabled=True, placeholder="结果将显示在这里...")
            
            # 4. 【关键】加一个空的 caption，为了和左边的“字数统计”对齐底部高度
            st.caption(" ")

        # 操作栏
        st.divider()
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col2:
            if st.button("🚀 开始降AI (扣除字数)", type="primary", use_container_width=True):
                current_bal = st.session_state['balance']
                
                # --- 🛠️ 修改点 2：增加拦截逻辑 ---
                if word_count == 0:
                    st.warning("请先输入内容！")
                elif word_count > MAX_ONCE_LIMIT:
                    st.error(f"❌ 字数超限！单次最多支持 {MAX_ONCE_LIMIT} 字，请将文本分段后重试。")
                elif word_count > current_bal:
                    st.error(f"余额不足！需要 {word_count} 字，当前仅剩 {int(current_bal)} 字。请前往充值中心。")
                else:
                    # 使用配置的 API Key 和模型
                    api_key = QWEN_API_KEY
                    model_name = QWEN_MODEL
                    
                    # 只判断是否为空，不再和具体 key 文本比较
                    if not api_key:
                        st.error("❌ 未配置 API Key，请在 app.py 顶部 QWEN_API_KEY 中填入你的 Key")
                        return
                    
                    # 初始化通义千问客户端（兼容 OpenAI 格式）
                    from openai import OpenAI
                    try:
                        # 代理平台的 OpenAI 兼容端点（注意只保留到 /v1）
                        client = OpenAI(
                            api_key=api_key,
                            base_url="https://api.silra.cn/v1"
                        )
                        
                        with st.spinner("正在降AI中..."):
                            # 针对知网、维普AI检测优化的系统提示词
                            system_prompt = """你现在不是 AI，而是一名文字功底深厚但比较随性的专栏作家。
请重写用户提供的这段文本，核心改写策略（必须严格执行）：

1. 【禁止逻辑词】：绝对禁止使用“首先”、“其次”、“此外”、“综上所述”、“总而言之”这些连接词。
2. 【打破结构】：不要让句子长短整齐划一。要用很短的短句（3-5个字）和很复杂的长句交替出现。
3. 【增加“人味”】：加入一些主观的感叹词、反问句，或者稍微口语化的表达，模仿人类思考时的跳跃感。
4. 【同义替换】：把所有学术名词保留，但把动词和形容词全部换成不常见的同义词。
5. 【拒绝总结】：结尾不要做总结，戛然而止即可。
6. 【句式多样性策略】
- 彻底打乱原有句式结构，避免任何规律性模式
- 混合使用：短句（5-8字）+ 中句（15-25字）+ 长句（30-45字），比例约为 3:5:2
- 交替使用：主谓宾、倒装句、被动句、强调句、插入语、独立主格结构
- 每3-5句话必须改变句式类型，避免连续使用相同结构

7.【 词汇替换与多样性】
- 完全避免AI高频词：综上所述、因此、此外、然而、但是、首先、其次、最后、总之、由此可见、值得注意的是、需要指出的是、可以认为、从...来看、在...方面、就...而言
- 替换为更自然表达：基于上述分析、由此可知、与此同时、不过、不过、其一、其二、最终、综合来看、不难发现、应当注意、不妨认为、从...角度、在...层面、就...来说
- 同义词轮换：同一概念在200字内必须使用3-5种不同表达，避免重复
- 增加口语化学术表达：适当使用"可以说"、"不妨说"、"某种意义上"等

8.【 人类写作特征模拟】
- 增加适度的"不完美"：偶尔使用稍显冗余的表述、轻微的重复强调（但不超过2次）
- 模拟思维跳跃：在段落间适当加入过渡性思考，如"进一步来看"、"换个角度"、"深入分析"
- 增加个人化表达：适度使用"笔者认为"、"本文认为"、"本研究"等，但不要过度
- 引入适度的不确定性：使用"可能"、"或许"、"在一定程度上"等模糊化表达

9.【 逻辑连贯性优化】
- 避免过于完美的逻辑链条，适当加入"虽然...但是"、"尽管...然而"等转折
- 段落间使用多样化的过渡词：不仅...而且、一方面...另一方面、既...又、不仅...还
- 避免"首先-其次-最后"的机械式结构，改用"其一-其二-其三"或直接分段论述

10.【 语言风格调整】
- 避免过于正式和刻板的学术语言，适当融入更自然的表达
- 增加具体例证和细节描述，减少抽象概括
- 使用更多具体动词，减少"进行"、"开展"、"实施"等万能动词
- 适当使用比喻、类比等修辞手法（学术范围内）

11.【 文本结构重组】
- 彻底重组段落结构，但保持核心论点不变
- 将长段落拆分为2-3个短段落，或将短段落合并（但要自然）
- 调整句子顺序，但保持逻辑关系清晰
- 在适当位置增加解释性语句，丰富内容

12.【知网/维普特定优化】
- 避免使用过于新颖的网络用语或流行语
- 保持学术规范，但语言要自然流畅
- 适当使用专业术语的同义表达，避免单一术语重复
- 增加文献引用风格的多样性（如果原文有引用）

【8. 输出要求】
- 直接输出改写后的完整文本，不要任何解释或说明
- 保持原文的核心观点、数据和结论完全一致
- 字数应与原文相近（±5%范围内）
- 确保改写后的文本读起来自然流畅，像人类学者手写的一样

现在请开始改写用户提供的文本。"""

                            # 发送真实请求到通义千问（优化参数以提升降重效果）
                            resp = client.chat.completions.create(
                                model=model_name,  # 使用通义千问模型
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": text_input}
                                ],
                                temperature=0.9,  # 提高温度值，增加随机性和多样性（通义千问支持更高温度）
                                top_p=0.95,  # 核采样参数，增加词汇多样性
                                # 注意：通义千问可能不支持frequency_penalty和presence_penalty，先注释掉
                                # frequency_penalty=0.3,  # 频率惩罚，减少重复
                                # presence_penalty=0.3,  # 存在惩罚，鼓励使用新词汇
                            )
                            # 获取结果
                            real_result = resp.choices[0].message.content
                            
                            # 扣费逻辑：SQLite 版，并记录使用日志
                            try:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                new_bal = current_bal - word_count
                                cur.execute(
                                    "UPDATE users SET balance = ? WHERE username = ?",
                                    (int(new_bal), st.session_state['username']),
                                )
                                # 记录使用日志
                                operation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cur.execute(
                                    """
                                    INSERT INTO usage_logs (username, words_used, operation_time, operation_type)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (st.session_state['username'], word_count, operation_time, '降重'),
                                )
                                conn.commit()
                                conn.close()
                            except Exception as db_e:
                                st.error(f"扣费失败: {db_e}")
                                return
                            
                            # 更新 Session 和界面
                            st.session_state['balance'] = new_bal
                            result_area.text_area("降重结果", value=real_result, height=400)
                            st.success(f"成功！消耗 {word_count} 字")
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                            st.error("❌ API Key 无效或已过期，请检查您的通义千问 API Key")
                        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                            st.error("❌ API 调用额度不足，请检查您的账户余额")
                        elif "model" in error_msg.lower():
                            st.error("❌ 模型名称错误，请检查模型选择")
                        else:
                            st.error(f"❌ 运行出错: {error_msg}")
                            st.info("💡 提示：请确保已正确输入通义千问 API Key，并检查网络连接")

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
            请联系客服购买卡密：
            - **客服**：1914952638
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
        
        # 使用记录
        st.subheader("📊 使用记录")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT words_used, operation_time, operation_type 
            FROM usage_logs 
            WHERE username = ? 
            ORDER BY operation_time DESC 
            LIMIT 20
            """,
            (st.session_state['username'],),
        )
        usage_records = cur.fetchall()
        if usage_records:
            usage_df = pd.DataFrame([
                {
                    "时间": row["operation_time"],
                    "消耗字数": row["words_used"],
                    "操作类型": row["operation_type"]
                }
                for row in usage_records
            ])
            st.dataframe(usage_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无使用记录")
        
        # 充值记录
        st.subheader("💰 充值记录")
        cur.execute(
            """
            SELECT code, words_added, balance_before, balance_after, recharge_time 
            FROM recharge_logs 
            WHERE username = ? 
            ORDER BY recharge_time DESC 
            LIMIT 20
            """,
            (st.session_state['username'],),
        )
        recharge_records = cur.fetchall()
        if recharge_records:
            recharge_df = pd.DataFrame([
                {
                    "时间": row["recharge_time"],
                    "卡密": row["code"],
                    "充值字数": row["words_added"],
                    "充值前余额": row["balance_before"],
                    "充值后余额": row["balance_after"]
                }
                for row in recharge_records
            ])
            st.dataframe(recharge_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无充值记录")
        
        conn.close()
        
        st.divider()
        st.subheader("数据备份 / 导出")
        backup_json = export_db_to_json()
        backup_file_name = f"paper_killer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.download_button(
            "📤 导出数据库为 JSON",
            data=backup_json,
            file_name=backup_file_name,
            mime="application/json",
            use_container_width=True,
        )
    
    elif menu == "⚙️ 管理员功能":
        st.header("⚙️ 管理员功能")
        
        if st.session_state.get('username') != 'admin':
            st.error("❌ 仅管理员可访问此功能")
            return
        
        # 卡密生成功能
        st.subheader("🎫 生成卡密")
        
        col_gen1, col_gen2 = st.columns([1, 1])
        with col_gen1:
            card_type = st.selectbox(
                "选择卡密类型",
                ["1000字 (¥3)", "2000字 (¥5)", "5000字 (¥12)", "10000字 (¥22)", "20000字 (¥40)"]
            )
            words_map = {
                "1000字 (¥3)": 1000,
                "2000字 (¥5)": 2000,
                "5000字 (¥12)": 5000,
                "10000字 (¥22)": 10000,
                "20000字 (¥40)": 20000
            }
            words_value = words_map[card_type]
        
        with col_gen2:
            count = st.number_input("生成数量", min_value=1, max_value=100, value=10, step=1)
        
        if st.button("🚀 生成卡密", type="primary", use_container_width=True):
            import random
            import string
            
            def generate_code(prefix):
                """生成类似 '1000-ABCD1234EF' 的卡密"""
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                return f"{prefix}-{suffix}"
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            generated_codes = []
            for _ in range(count):
                code = generate_code(str(words_value))
                try:
                    cur.execute(
                        """
                        INSERT INTO coupons (code, words, status, used_by, used_time)
                        VALUES (?, ?, 'unused', NULL, NULL)
                        """,
                        (code, words_value),
                    )
                    generated_codes.append(code)
                except sqlite3.IntegrityError:
                    # 如果卡密已存在，重新生成
                    continue
            
            conn.commit()
            conn.close()
            
            if generated_codes:
                st.success(f"✅ 成功生成 {len(generated_codes)} 张卡密！")
                st.code("\n".join(generated_codes), language=None)
                
                # 提供下载
                codes_text = "\n".join(generated_codes)
                st.download_button(
                    "📥 下载卡密列表",
                    data=codes_text,
                    file_name=f"coupons_{words_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.error("生成失败，请重试")
        
        st.divider()
        
        # 用户管理
        st.subheader("👥 用户管理")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, password, balance FROM users ORDER BY username")
        all_users = cur.fetchall()
        if all_users:
            users_df = pd.DataFrame([
                {
                    "用户名": row["username"],
                    "密码": row["password"],
                    "余额": row["balance"]
                }
                for row in all_users
            ])
            st.dataframe(users_df, use_container_width=True, hide_index=True)
            
            # 重置 admin 账号按钮
            if st.button("🔄 重置 Admin 账号", use_container_width=True):
                cur.execute(
                    "UPDATE users SET password = ?, balance = ? WHERE username = ?",
                    ("123", 999999, "admin"),
                )
                # 如果 admin 不存在，则插入
                if cur.rowcount == 0:
                    cur.execute(
                        "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                        ("admin", "123", 999999),
                    )
                conn.commit()
                st.success("✅ Admin 账号已重置！用户名: admin, 密码: 123")
                st.rerun()
        conn.close()
        
        st.divider()
        
        # 卡密统计
        st.subheader("📈 卡密统计")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 统计各类型卡密
        cur.execute("""
            SELECT words, status, COUNT(*) as count 
            FROM coupons 
            GROUP BY words, status
            ORDER BY words, status
        """)
        stats = cur.fetchall()
        
        if stats:
            stats_df = pd.DataFrame([
                {
                    "面值": f"{row['words']} 字",
                    "状态": "已使用" if row['status'] == 'used' else "未使用",
                    "数量": row['count']
                }
                for row in stats
            ])
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        conn.close()

# --- 6. 主入口 ---
# 初始化数据库（只需在程序加载时运行一次）
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()
