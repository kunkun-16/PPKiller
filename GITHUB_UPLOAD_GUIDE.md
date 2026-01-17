# GitHub 上传指南

## 方法一：使用命令行（推荐）

### 步骤 1：在 GitHub 上创建新仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 **+** 号，选择 **New repository**
3. 填写仓库信息：
   - Repository name: `Paper-Killer`（或你喜欢的名字）
   - Description: 论文去AI痕迹神器 - 2026专业版
   - 选择 **Public** 或 **Private**
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有文件）
4. 点击 **Create repository**

### 步骤 2：在本地初始化 Git 并上传

打开 PowerShell 或命令提示符，进入项目目录，然后依次执行以下命令：

```powershell
# 1. 进入项目目录（如果还没在的话）
cd C:\Users\qq\Desktop\Paper-Killer

# 2. 初始化 Git 仓库
git init

# 3. 添加所有文件到暂存区
git add .

# 4. 提交文件
git commit -m "Initial commit: 论文去AI痕迹神器"

# 5. 添加远程仓库（将 YOUR_USERNAME 替换为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/Paper-Killer.git

# 6. 重命名主分支为 main（如果 GitHub 要求）
git branch -M main

# 7. 推送到 GitHub
git push -u origin main
```

### 步骤 3：输入 GitHub 凭证

- 如果提示输入用户名和密码，使用：
  - 用户名：你的 GitHub 用户名
  - 密码：使用 **Personal Access Token**（不是 GitHub 密码）
  
  如何获取 Personal Access Token：
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. 点击 "Generate new token (classic)"
  3. 勾选 `repo` 权限
  4. 生成后复制 token，作为密码使用

---

## 方法二：使用 GitHub Desktop（图形界面，更简单）

### 步骤 1：下载安装 GitHub Desktop

1. 访问 https://desktop.github.com
2. 下载并安装 GitHub Desktop

### 步骤 2：使用 GitHub Desktop 上传

1. 打开 GitHub Desktop
2. 点击 **File** → **Add Local Repository**
3. 选择项目文件夹：`C:\Users\qq\Desktop\Paper-Killer`
4. 如果提示需要初始化，点击 **create a repository**
5. 在左侧填写提交信息，例如："Initial commit: 论文去AI痕迹神器"
6. 点击 **Commit to main**
7. 点击右上角的 **Publish repository**
8. 填写仓库名称和描述，选择 Public/Private
9. 点击 **Publish Repository**

---

## 方法三：使用 VS Code（如果你用 VS Code）

1. 在 VS Code 中打开项目文件夹
2. 点击左侧的源代码管理图标（或按 `Ctrl+Shift+G`）
3. 点击 **Initialize Repository**
4. 点击 **+** 号添加所有文件
5. 在消息框输入提交信息，点击 ✓ 提交
6. 点击 **...** → **Publish Branch**
7. 选择 GitHub，登录并创建仓库

---

## 后续更新代码

每次修改代码后，使用以下命令更新 GitHub：

```powershell
git add .
git commit -m "描述你的修改内容"
git push
```

---

## 注意事项

1. **不要上传敏感信息**：`.gitignore` 文件已经排除了敏感文件，但请确保不要将 API Key 硬编码在代码中
2. **README.md**：项目已有 README.md，GitHub 会自动显示
3. **requirements.txt**：已包含，其他用户可以轻松安装依赖

---

## 常见问题

**Q: 提示 "remote origin already exists"**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/Paper-Killer.git
```

**Q: 提示 "failed to push some refs"**
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

**Q: 忘记添加 .gitignore 中的文件**
```powershell
# 如果已经提交了敏感文件，需要从历史中删除
git rm --cached 文件名
git commit -m "Remove sensitive file"
git push
```
