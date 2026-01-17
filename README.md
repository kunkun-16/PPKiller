# 论文去AI痕迹神器 - 2026专业版

一个基于 Streamlit 的论文降重工具，使用 DeepSeek API 对论文进行智能改写，以规避 AI 检测。

## 功能特点

- 📝 简洁直观的三栏布局
- 🚀 一键降重处理
- 📋 一键复制结果
- 🔐 安全的 API Key 管理（存储在侧边栏）

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
streamlit run app.py
```

## 使用方法

1. 在侧边栏输入您的 DeepSeek API Key
2. 在左侧文本框中输入需要降重的论文内容
3. 点击"开始降重"按钮
4. 等待处理完成后，在右侧查看结果
5. 点击"一键复制"按钮复制结果

## 注意事项

- 需要有效的 DeepSeek API Key
- 处理时间取决于文本长度和网络状况
- API Key 仅存储在会话中，刷新页面后需要重新输入
