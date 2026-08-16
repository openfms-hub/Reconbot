# ReconBot

海外目标公司自动调研与合作潜力分析 CLI 工具。

输入一家公司名称，ReconBot 自动完成多源情报采集、LLM 深度分析，输出一份结构化的公司背景调查 + 合作潜力评估报告。专为 B2B 硬件出海团队设计——在接触潜在客户/分销商前，快速摸清对方底细。

## 调研方法

ReconBot 采用 **"多源采集 → LLM 分析 → 结构化报告"** 三阶段流水线，整个过程全自动，无需人工干预。

### 第一阶段：多源情报采集（并行）

三路采集器同时出击，从不同维度抓取目标公司的公开信息：

| 采集器 | 数据来源 | 采集策略 | 擅长获取的信息 |
|--------|----------|----------|---------------|
| **Website** | 目标公司官网 | 两级深度爬取：首页 → 高价值子页面（about/services/contact/login 等） → 二级链接。支持子域名发现，提取 HTML 正文 + meta 标签 | 服务范围、产品列表、联系方式、技术平台线索（如登录页 URL 暗示 Wialon/CMSV6） |
| **Exa** | Exa 语义搜索引擎 | 三路查询：① 公司核心信息 ② 技术栈与软件平台 ③ 法人主体与工商信息（如 S.A. de C.V.、RFC） | 行业报道、公司历史、技术合作关系、法人实体名称 |
| **Tavily** | Tavily 深度搜索 | 三路查询：① 公司概况与服务（advanced 模式，含原始网页内容） ② 社交媒体账号 ③ 客户评价与口碑 | 社交媒体画像、Google 评价、新闻动态、行业口碑 |

三路采集器并行执行，互不阻塞。采集结果去重后合并，总数据量控制在 50,000 字符以内供后续分析。

### 第二阶段：LLM 深度分析（两轮）

采集到的原始数据进入两轮 LLM 分析：

1. **公司画像分析（Profiler）** — 从原始情报中提取结构化公司档案。LLM 被要求特别关注三类关键信号：
   - 法人主体：页面 footer、版权声明、隐私政策中的公司全称
   - 软件平台：登录页 URL、平台名称（Wialon / CMSV6 / Navixy 等）、子域名线索
   - 硬件品牌：产品页面中的设备型号与供应商名称

2. **合作潜力分析（Matcher）** — 将目标公司画像与我方公司 Profile 进行匹配，评估合作可行性，输出包含当地语言接洽话术的行动方案。

### 第三阶段：报告生成

Profiler 和 Matcher 的分析结果通过 Jinja2 模板合并为一份完整的 Markdown 报告。

## 报告结构

生成的报告包含以下章节：

### 公司背景部分（Profiler 输出）

| 章节 | 内容 |
|------|------|
| **一、公司概况** | 品牌名、法人主体、总部地址、成立时间、公司规模、联系方式、管理设备量、融资情况（表格） |
| **二、业务定位与服务矩阵** | 行业定位一句话定性 + 服务类别明细表 |
| **三、客户群体** | 核心 / 重要 / 辅助客户类型及说明 |
| **四、技术栈分析** | 软件平台（自研 vs 第三方）、硬件策略（品牌型号）、协议与 API 开放性 |
| **五、商业模式与定价** | 收入模式、定价线索、设备模式（买断/租赁）、覆盖范围 |
| **六、资质与认证** | 行业认证、许可、协会会员 |
| **七、社交媒体与市场口碑** | 各平台账号数据 + 客户评价正负面摘要 |
| **八、竞争对手** | 同区域竞品对比 |
| **九、关键发现** | 3-5 条最重要的发现 |

### 合作评估部分（Matcher 输出）

| 章节 | 内容 |
|------|------|
| **一、合作机会评级** | ⭐ 1-5 星评级 + 一句话定性 |
| **二、为什么值得跟进** | 七维度匹配分析表（业务需求、硬件中立性、技术兼容性、客户群重合、规模与采购量、定价敏感度、地理辐射） |
| **三、推荐产品匹配** | 目标公司具体需求场景 → 我方匹配产品 → 竞争优势（表格） |
| **四、潜在风险** | 风险点 + 缓解措施 |
| **五、接洽策略** | 三步走方案：建立联系（含当地语言开场话术 + 中文翻译）→ 技术对接 → 商务谈判 |
| **六、关键结论** | 3-5 条可直接执行的要点 |

### 附录

数据源采集概况表（各采集器状态、数据段数、来源 URL 数）。

## 安装

### 方式一：venv + pip（推荐）

```bash
# 克隆项目
git clone <repo-url> && cd reconbot

# 一键安装（创建虚拟环境 + 安装依赖）
make install

# 激活环境
source .venv/bin/activate

# 验证安装
reconbot --help
```

> 也可直接手动执行：
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> pip install -e .
> ```

### 方式二：uv（可选）

```bash
uv sync
```

## 配置

编辑 `config/settings.yaml` 配置 API Key 和采集器开关：

```yaml
llm:
  default_model: "openai/qwen-plus"
  providers:
    # 每个 provider 通过 models 声明它负责的模型列表
    # 匹配规则：模型名包含或前缀匹配 models 中的任意项
    dashscope:
      api_key: "your-dashscope-api-key"
      api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
      models: ["qwen-max", "qwen-plus", "qwen-turbo"]
    moonshot:
      api_key: "your-moonshot-api-key"
      api_base: "https://api.moonshot.cn/v1"
      models: ["moonshot-v1", "kimi"]
    deepseek:
      api_key: "your-deepseek-api-key"
      api_base: "https://api.deepseek.com/v1"
      models: ["deepseek-chat", "deepseek-coder"]
    # 新增模型只需添加 provider + models 声明，无需改代码
    dots:
      api_key: "your-dots-api-key"
      api_base: "https://note3-prev-api.askdiandian.com/v1"
      models: ["dots3-note-prev"]

    > ⚠ **api_base 必须包含版本前缀（如 /v1）**。LiteLLM 会在 api_base 后追加
    > `/chat/completions`，所以完整 URL 应为 `.../v1/chat/completions`。

collectors:
  website:
    enabled: true
    max_pages: 10
  exa:
    enabled: true
    api_key: "your-exa-api-key"
  tavily:
    enabled: true
    api_key: "your-tavily-api-key"
```

编辑 `config/company_profile.yaml` 填入我方公司信息（产品线、优势、合作偏好），用于合作潜力匹配分析。

### 新增 LLM 模型

ReconBot 使用 **声明式模型路由**：每个 `provider` 通过 `models` 字段声明它负责的模型列表。调用 LLM 时按以下顺序解析：

1. **精确匹配** — 模型名是否被某个 provider 的 `models` 列表包含（或作为前缀）
2. **关键词兜底** — 含 "qwen" → dashscope，含 "kimi"/"moonshot" → moonshot，含 "deepseek" → deepseek（兼容旧配置）

**新增模型只需两步**（无需改代码）：

1. 在 `settings.yaml` 的 `llm.providers` 下新增一个 provider 块，填写 `api_key`、`api_base` 和 `models`
2. 兼容 OpenAI Chat Completions 的模型（如 Dots、Claude via API 等）直接可用，无需额外适配

### 模型名称解析规则（优先级从高到低）

| 优先级 | 格式 | 示例 | 说明 |
|--------|------|------|------|
| 1 | `provider/model` | `dots/dots3-note-prev` | **推荐**，完全消除歧义 |
| 2 | 裸模型名 + `models` 匹配 | `dots3-note-prev` | 自动路由到声明了该模型的 provider |
| 3 | 关键词兜底 | `qwen-max` | 兼容旧配置，自动路由 |

### 多 Provider 模型名冲突处理

如果两个 provider 都声明了同一个模型名，ReconBot 会在启动时输出 **⚠ 警告到 stderr**。

**最佳实践：始终使用 `provider/model` 全限定格式**：
```bash
reconbot research "Company" --model dots/dots3-note-prev
reconbot research "Company" --model dashscope/qwen-max
```

这样无论 `models` 列表如何配置，路由结果都完全确定。
```yaml
llm:
  default_model: "dots3-note-prev"
  providers:
    dots:
      api_key: "your-dots-api-key"
      api_base: "https://note3-prev-api.askdiandian.com/v1"
      models: ["dots3-note-prev"]
```

## 使用

### 单家公司调研

```bash
reconbot research "Vectro Rastreo Vehicular" \
  --website https://www.vectro.com.mx \
  --country Mexico \
  --city Guadalajara \
  --phone "+52 33 3635 4809"
```

### 批量调研

准备 CSV 文件（必须包含 `name` 列，可选 `website`、`country`、`city`、`phone`、`email`、`industry`）：

```bash
reconbot batch leads.csv
```

### 查看当前配置

```bash
reconbot config
```

### 指定 LLM 模型

```bash
reconbot research "Target Company" --model openai/qwen-max
```

报告自动保存到 `reports/` 目录，文件名格式：`{公司名}_调研报告_{日期}.md`。

### 通过 Makefile 快捷操作

安装好依赖后，可直接使用 `make` 命令：

```bash
# 查看配置
make config

# 调研单家公司（设置环境变量）
COMPANY="Vectro Rastreo" WEBSITE="https://www.vectro.com.mx" COUNTRY="Mexico" make research

# 批量调研
CSV_FILE=leads.csv make batch
```

环境变量也可写入 `.env` 文件持久化（不会被提交到 Git）：
```bash
echo 'COMPANY="Vectro Rastreo"' > .env
echo 'WEBSITE="https://www.vectro.com.mx"' >> .env
make research
```

## 常见问题与故障排查

### 1. 新增 AI 模型后 LLM 调用失败

| 症状 | 原因 | 解决 |
|------|------|------|
| `BadRequestError: LLM Provider NOT provided` | LiteLLM 无法识别裸模型名 | 模型自动加 `openai/` 前缀路由，`api_base` 必须包含 `/v1` |
| `400: Invalid provider request` | `max_tokens` 值过大，超出 API 限制 | 调低至 `4096`（约 2-3 页报告输出） |
| `404 page not found` | `api_base` 缺少版本前缀 | `https://xxx.com` → `https://xxx.com/v1` |

**api_base 格式规则：**

```
api_base: "https://note3-prev-api.askdiandian.com/v1"  ← 包含 /v1
                                                          ↓
LiteLLM 拼成: https://note3-prev-api.askdiandian.com/v1/chat/completions
```

完整示例：

```yaml
llm:
  default_model: "dots/dots3-note-prev"    # 全限定名，消除歧义
  max_tokens: 4096                           # 不要设置过大（512KB 等值会 400）
  providers:
    dots:
      api_key: "your-key"
      api_base: "https://note3-prev-api.askdiandian.com/v1"  # ← 注意 /v1
      models: ["dots3-note-prev"]
```

**模型名解析规则（优先级从高到低）：**

| 优先级 | 格式 | 示例 |
|--------|------|------|
| 1 | `provider/model` 全限定名 | `dots/dots3-note-prev` ← **推荐** |
| 2 | 裸模型名 + `models` 匹配 | `dots3-note-prev` |
| 3 | 关键词兜底 | `qwen-max` → dashscope |

### 2. 多个 Provider 声明了同名模型

启动时输出警告：

```
[reconbot] ⚠ 模型 'xxx' 被多个 provider 声明: dots, dashscope。
  建议使用 'provider/model' 格式明确指定。
```

**最佳实践：始终使用 `provider/model` 全限定格式**，如：
```bash
reconbot research "Company" --model dots/dots3-note-prev
```

### 3. Arch Linux 环境搭建

```
bash
# 安装 Python（Arch 默认不带）
sudo pacman -S python

# 安装 make（Arch 默认不带）
sudo pacman -S make

# 验证
python3 --version
make --version

# 安装项目
make install
```

> 如果 `pacman` 报 404，镜像源未同步，执行 `sudo pacman -Syu` 刷新。

### 4. 快速验证 LLM 配置是否正确

```bash
# 激活环境后
source .venv/bin/activate

# 查看配置（验证 API Key 是否已加载）
reconbot config

# 如果显示 API Key 已配置，即可正常调研
```

---

## 项目结构

```
reconbot/
├── config/
│   ├── settings.yaml          # 全局配置（LLM、采集器、输出）
│   └── company_profile.yaml   # 我方公司 Profile
├── requirements.txt           # pip 依赖清单
├── Makefile                   # 快捷命令（install / research / batch）
├── src/reconbot/
│   ├── cli.py                 # Typer CLI 入口
│   ├── config.py              # 配置加载
│   ├── pipeline.py            # 主流水线编排
│   ├── collectors/            # 情报采集器
│   │   ├── website.py         # 官网爬虫（两级深度 + 子域名）
│   │   ├── exa.py             # Exa 语义搜索（三路查询）
│   │   ├── tavily.py          # Tavily 深度搜索（三路查询）
│   │   └── google.py          # Google Custom Search（可选）
│   ├── analyzers/             # LLM 分析器
│   │   ├── profiler.py        # 公司画像提取
│   │   └── matcher.py         # 合作潜力匹配
│   ├── reporters/             # 报告生成
│   │   └── markdown.py        # Markdown 报告输出
│   └── templates/
│       └── default.md.j2      # 报告 Jinja2 模板
├── reports/                   # 生成的报告（自动创建）
└── pyproject.toml
```

## 桌面应用（Tauri）

ReconBot 提供基于 Tauri 的桌面 GUI 应用，无需命令行操作，双击即可使用。

### 运行开发模式

```bash
# 前置要求: Rust (rustup), Tauri CLI
source ~/.cargo/env
cd src-tauri
cargo tauri dev
```

### 打包发布

```bash
cd src-tauri
cargo tauri build
```

产物位于 `src-tauri/target/release/bundle/`（macOS: `.dmg`, Windows: `.msi`, Linux: `.deb`）。

### 目录结构

```
src-tauri/
├── frontend/            # HTML/CSS/JS 前端
│   ├── index.html
│   ├── style.css
│   └── app.js
├── src/
│   ├── main.rs          # Tauri 入口
│   └── lib.rs           # 桥接命令（list_reports, do_research 等）
├── tauri.conf.json      # Tauri 配置
├── Cargo.toml
└── capabilities/
```

---

## 技术栈

- Python 3.12+
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — CLI 框架
- [LiteLLM](https://docs.litellm.ai/) — 统一 LLM 调用（DashScope/Qwen、Kimi、DeepSeek）
- [httpx](https://www.python-httpx.org/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — 网页爬取与解析
- [Exa](https://exa.ai/) — 语义搜索引擎
- [Tavily](https://tavily.com/) — AI 搜索引擎
- [Jinja2](https://jinja.palletsprojects.com/) — 报告模板引擎
