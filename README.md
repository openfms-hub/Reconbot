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

```bash
# 克隆项目
git clone <repo-url> && cd reconbot

# 使用 uv 安装（推荐）
uv sync
```

## 配置

编辑 `config/settings.yaml` 配置 API Key 和采集器开关：

```yaml
llm:
  default_model: "openai/qwen-plus"
  providers:
    dashscope:
      api_key: "your-dashscope-api-key"
      api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"

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

## 项目结构

```
reconbot/
├── config/
│   ├── settings.yaml          # 全局配置（LLM、采集器、输出）
│   └── company_profile.yaml   # 我方公司 Profile
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

## 技术栈

- Python 3.12+
- [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) — CLI 框架
- [LiteLLM](https://docs.litellm.ai/) — 统一 LLM 调用（DashScope/Qwen、Kimi、DeepSeek）
- [httpx](https://www.python-httpx.org/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — 网页爬取与解析
- [Exa](https://exa.ai/) — 语义搜索引擎
- [Tavily](https://tavily.com/) — AI 搜索引擎
- [Jinja2](https://jinja.palletsprojects.com/) — 报告模板引擎
