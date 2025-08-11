参考：https://missing.csail.mit.edu/2020/version-control/

为你的项目引入版本控制是保障项目健康发展、进行功能迭代（如从 V2.0 到 V3.0）最关键的一步。对于像你这样的软件项目，业界标准无疑是 **Git**。

下面我为你提供一套完整且针对你当前项目的 Git 版本控制实践方案。

### 为什么要用 Git？

  * **追踪历史**：你可以清晰地看到每一次代码的修改，知道谁、在什么时候、为什么做了修改。
  * **安全备份**：即使你本地的代码丢失或出错，也可以轻松恢复到任何一个历史版本。
  * **并行开发（分支）**：这是最重要的功能。你可以为你的 V3.0 规划创建一个完全独立的“分支”，在上面开发新功能（如支持PPT、知识图谱），而完全不影响你当前稳定可用的 V2.0 版本。开发完成后，再将新功能合并回主线。
  * **团队协作**：如果未来有其他人加入项目，Git 是最高效的协作工具。

-----

### 针对你项目的版本控制实施步骤

#### 第1步：安装与初始化

1.  **安装 Git**：如果你的电脑还没有安装 Git，请先从 [官网下载](https://git-scm.com/downloads) 并安装。

2.  **在项目根目录初始化**：打开命令行/终端，进入你的项目文件夹 `ai-notes-generator/`，然后运行以下命令：

    ```bash
    git init
    ```

    这会在你的项目文件夹里创建一个名为 `.git` 的隐藏子目录，从此 Git 开始追踪这个文件夹里的所有变动。

#### 第2步：创建 `.gitignore` 文件（非常重要！）

有些文件不应该被纳入版本控制，比如包含密码的环境变量文件、Python 缓存、以及程序运行时生成的图片。

在你的项目根目录 (`ai-notes-generator/`) 下创建一个名为 `.gitignore` 的文件，并写入以下内容：

```gitignore
# 环境变量文件，包含敏感信息
llm.env

# 运行时从PDF提取的图片，这些是生成物而非源代码
static/images/

# Python 缓存和虚拟环境
__pycache__/
*.pyc
.env
venv/
*.DS_Store
```

**为什么这么做？**

  * `llm.env` 包含你的 API Key，绝对不能上传到公共仓库（如 GitHub）。
  * `static/images/` 里的图片是每次运行程序时动态生成的，追踪它们没有意义，还会让仓库变得臃肿。

#### 第3步：提交你的 V2.0 版本作为基础

现在，我们将你当前稳定可用的 V2.0 版本作为项目的第一个历史节点。

```bash
# 将所有（未被.gitignore忽略的）文件添加到暂存区
git add .

# 提交这些更改，并附上有意义的说明
git commit -m "Initial commit: V2.0 - Core functionality working"
```

现在，你的 V2.0 代码库已经安全地记录在 Git 的历史中了。

#### 第4步：为 V3.0 创建开发分支

这是实现你宏伟蓝图的关键。我们为主版本（通常叫 `main` 或 `master`）保持稳定，为 V3.0 的新功能创建一个名为 `v3-development` 的新分支。

```bash
# 从当前主分支创建一个新分支并立即切换过去
git checkout -b v3-development
```

现在你就在 `v3-development` 分支上了。你在这里做的所有修改，比如为支持 PPT 写的代码、为生成知识图谱做的尝试，都和 `main` 分支上的 V2.0 版本是隔离的。如果搞砸了，可以随时切换回 `main` 分支，那里还是你稳定好用的 V2.0。

#### 第5步：在 V3.0 分支上开发新功能

现在你可以开始动手实现 V3.0 的功能了。一个很好的实践是**为每个小功能创建单独的分支**。

例如，你想先实现“支持 PPT 上传”的功能：

```bash
# 从 v3-development 分支上，再创建一个特性分支
git checkout -b feature/ppt-support

# --- 在这里，你开始修改代码 ---
# 1. 安装 `python-pptx`
# 2. 在 `main_v2_2.py` 中添加处理 .pptx 文件的函数
# 3. 调试代码，直到功能可用
# --- 代码修改完成 ---

# 提交这个新功能
git add .
git commit -m "feat: Add support for PPTX file uploads by converting slides to images"

# 功能完成后，切换回 V3.0 的主开发分支
git checkout v3-development

# 将 feature/ppt-support 分支上的代码合并进来
git merge feature/ppt-support
```

用同样的方法，你可以为“知识图谱”功能创建另一个分支 `feature/knowledge-graph`。这种做法让你的开发流程非常清晰、安全、可控。

#### 第6步：将代码托管到 GitHub (推荐)

为了数据备份和未来可能的协作，建议将你的代码推送到一个远程仓库，如 GitHub。

1.  在 [GitHub](https://github.com/) 上创建一个新的空仓库（不要勾选任何“Initialize this repository”相关的选项）。
2.  GitHub 会给你一个仓库地址，比如 `https://github.com/your-username/ai-notes-generator.git`。
3.  在你的本地项目文件夹中，运行：
    ```bash
    # 将本地仓库与远程仓库关联起来
    git remote add origin https://github.com/your-username/ai-notes-generator.git

    # 将你的主分支推送到远程仓库
    git push -u origin main

    # 也将你的开发分支推送上去
    git push origin v3-development
    ```

### 总结

你的版本控制流程应该是这样的：

1.  **`main` 分支**：永远存放稳定、可发布的代码（比如你现在的 V2.0）。
2.  **`development` 分支** (如 `v3-development`)：用于整合所有新功能，是开发中的最新版本。
3.  **`feature` 分支** (如 `feature/ppt-support`)：用于开发具体某个新功能，开发完成后合并到 `development` 分支，然后可以删除。

这个流程会让你在实现 V3.0 和 V4.0 宏伟蓝图时，始终保持项目代码的清晰和稳定。