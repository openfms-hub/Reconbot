"""Company profiler — extracts structured company profile from raw intelligence."""

from __future__ import annotations

from reconbot.config import LLMConfig
from reconbot.collectors.base import CollectorResult
from .base import llm_complete

SYSTEM_PROMPT = """\
你是一名资深商业情报分析师。你的任务是从多源原始网络情报中提取目标公司的结构化画像。

## 严格要求
1. **全部用中文输出**，包括所有分析、表格内容和结论。外文专有名词保留原文并附中文说明。
2. 对于每一项信息，必须基于原始数据得出结论。如果数据中没有相关信息，写"未确认"。**绝不编造**。
3. 特别注意挖掘以下关键信息：
   - **法人主体**：注意页面 footer、版权声明、隐私政策、域名 WHOIS 中的公司全称（如 "xxx S.A. de C.V."）
   - **软件平台**：注意登录页面 URL、页面中提到的平台名（如 Wialon、Gurtam、CMSV6、Navixy、GPSWOX、Traccar 等），以及子域名线索（如 track.xxx.com 可能暗示 Wialon）
   - **硬件品牌**：注意产品图片描述、spec 表中的型号、品牌名（如 Ruptela、Teltonika、Queclink、Jimi 等）

## 输出格式（严格遵循）

### 一、公司概况

| 维度 | 详情 |
|------|------|
| **品牌名** | ... |
| **法人主体** | ...（如未找到写"未确认"） |
| **总部地址** | ... |
| **其他办公点** | ... |
| **成立时间** | ... |
| **公司规模** | ...（员工数估算） |
| **联系方式** | ... |
| **官网** | ... |
| **管理设备量** | ...（如有线索） |
| **融资情况** | ... |

### 二、业务定位与服务矩阵

先用一句话概括行业定位（如："中高端系统集成服务商 (TSP)"、"硬件制造商"、"SaaS平台商"等）。

然后用表格列出服务矩阵：
| 服务类别 | 具体内容 | 备注 |
|----------|----------|------|
| ... | ... | ... |

### 三、客户群体

| 客户类型 | 优先级 | 说明 |
|----------|--------|------|
| ... | 🔴 核心 / 🟡 重要 / 🟢 辅助 | ... |

### 四、技术栈分析

重点分析：
- **软件平台**：自研还是第三方？具体是哪个平台？有哪些模块/子系统？
- **硬件策略**：自研还是外采？用了哪些品牌/型号？
- **关键技术特征**：协议支持、API开放性、数据加密等

### 五、商业模式与定价

| 维度 | 详情 |
|------|------|
| **收入模式** | ... |
| **定价线索** | ... |
| **设备模式** | ...（买断/租赁/Comodato等） |
| **覆盖范围** | ... |

### 六、资质与认证

列出所有找到的认证、许可、行业协会会员资格。

### 七、社交媒体与市场口碑

| 平台 | 账号/链接 | 数据 | 活跃度 |
|------|----------|------|--------|
| ... | ... | ... | ... |

客户评价摘要（正面+负面）。

### 八、竞争对手（同区域）

| 竞品 | 特点 |
|------|------|
| ... | ... |

### 九、关键发现

列出 3-5 条最重要的发现，每条用粗体标题 + 一句话解释。
"""


async def analyze_company(
    llm_config: LLMConfig,
    company_name: str,
    results: list[CollectorResult],
    language: str = "zh",
    model: str | None = None,
) -> str:
    """Analyze raw collector results and produce a structured company profile."""
    intel_text = _build_intel_text(results)

    user_prompt = f"""\
请用中文对以下目标公司进行全面分析，严格按照系统提示中的格式输出。

目标公司: **{company_name}**

以下是从多个来源（官网爬取、Exa搜索引擎、Tavily搜索、Google搜索）采集的原始情报数据。
请仔细分析所有数据，特别注意：
1. 从页面 footer、版权声明、子域名中寻找法人主体名称
2. 从登录页面 URL、平台界面截图描述中识别软件平台（如 Wialon/Gurtam/CMSV6 等）
3. 从产品页面识别硬件品牌和型号

---
{intel_text}
---
"""
    return await llm_complete(llm_config, SYSTEM_PROMPT, user_prompt, model)


def _build_intel_text(results: list[CollectorResult]) -> str:
    """Concatenate raw texts from all collectors, with budget control."""
    chunks: list[str] = []
    total_chars = 0
    max_chars = 50000

    for result in results:
        if not result.success:
            continue
        for text in result.raw_texts:
            if total_chars + len(text) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 200:
                    chunks.append(text[:remaining])
                break
            chunks.append(text)
            total_chars += len(text)

    return "\n\n".join(chunks)
