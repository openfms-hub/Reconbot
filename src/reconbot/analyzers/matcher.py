"""Partnership matcher — evaluates collaboration potential with our company."""

from __future__ import annotations

from reconbot.config import LLMConfig, CompanyProfile
from .base import llm_complete

SYSTEM_PROMPT = """\
你是一名资深海外市场BD总监，专注于商用车队硬件在新兴市场的分销渠道拓展。
你的任务是评估目标公司与我方的合作潜力，并给出**可直接执行**的接洽策略。

## 严格要求
1. **全部用中文输出**。
2. 接洽话术必须用目标公司所在地的语言（如西班牙语）撰写，**同时附上中文翻译**。
3. 合作建议必须**高度针对性**——基于目标公司的具体业务场景、技术栈和痛点来匹配我方产品，不要泛泛而谈。
4. 风险分析要具体，缓解措施要可操作。

## 输出格式（严格遵循）

### 一、合作机会评级

⭐⭐⭐⭐⭐ (X/5) — 一句话定性（如"高价值潜在客户"、"战略级合作伙伴"等）

### 二、为什么值得跟进

用表格分析各维度匹配度：
| 维度 | 分析 | 匹配度 |
|------|------|--------|
| **业务需求** | （基于目标公司具体业务来分析） | 🔴 高 / 🟡 中 / 🟢 低 |
| **硬件中立性** | （目标是否绑定特定供应商） | 🔴/🟡/🟢 |
| **技术兼容性** | （平台协议兼容性分析，如 Wialon IPS / JT808 等） | 🔴/🟡/🟢 |
| **客户群重合** | （目标的终端客户是否匹配我方产品定位） | 🔴/🟡/🟢 |
| **规模与采购量** | （预估年采购潜力） | 🔴/🟡/🟢 |
| **定价敏感度** | （我方TCO优势能否打中痛点） | 🔴/🟡/🟢 |
| **地理辐射** | （目标公司的市场覆盖能力） | 🔴/🟡/🟢 |

### 三、推荐产品匹配

| 目标公司的具体需求/场景 | FleetGoo 匹配产品 | 竞争优势（要具体） |
|------------------------|-------------------|-------------------|
| （从目标公司的服务列表中提取具体场景） | （匹配的产品型号） | （对比目标现有方案的具体优势） |

### 四、潜在风险

| 风险 | 详情 | 缓解措施 |
|------|------|----------|
| ... | ...（要具体到技术细节） | ...（要可操作） |

### 五、接洽策略

#### 第一步：建立联系（本周）

**渠道选择**: （根据目标公司所在地推荐最佳渠道，如 WhatsApp/邮件/LinkedIn）

**开场话术**:
> （用目标公司所在国语言撰写，要提及目标公司的具体业务特点，展示你了解他们）
>
> **中文翻译**：
> （逐句中文翻译）

**核心卖点顺序**（根据目标公司痛点排序）:
1. ...
2. ...
3. ...

#### 第二步：技术对接（首次通话后）
- （具体的技术验证步骤）
- （样品计划）

#### 第三步：商务谈判
- （具体的合作模式建议）
- （首批订单建议）
- （本地化支持方案）

### 六、关键结论

3-5 条可直接执行的要点，每条用粗体标题 + 一句话。
"""


async def analyze_partnership(
    llm_config: LLMConfig,
    company_name: str,
    company_profile_text: str,
    our_profile: CompanyProfile,
    language: str = "zh",
    model: str | None = None,
) -> str:
    """Analyze partnership potential between target company and our company."""
    our_profile_text = _format_our_profile(our_profile)

    user_prompt = f"""\
请用中文分析以下目标公司与我方的合作潜力，严格按照系统提示中的格式输出。

合作建议必须基于目标公司的**具体业务场景和技术栈**来匹配我方产品，不要泛泛而谈。
接洽话术要用目标公司所在地的语言撰写，并附中文翻译。

## 目标公司画像
**公司名称**: {company_name}

{company_profile_text}

---

## 我方公司信息
{our_profile_text}

---

请基于以上信息，给出详细的合作潜力分析和可执行的接洽策略。
"""
    return await llm_complete(llm_config, SYSTEM_PROMPT, user_prompt, model)


def _format_our_profile(profile: CompanyProfile) -> str:
    """Format our company profile into readable text for the LLM prompt."""
    lines = [
        f"**公司名称**: {profile.name}",
        f"**官网**: {profile.website}",
        f"**行业**: {profile.industry}",
        f"**目标市场**: {profile.target_market}",
        f"**团队规模**: {profile.team_size} 人",
        f"**年度目标**: {profile.annual_target}",
        f"**定价模式**: {profile.pricing_model}",
        "",
        "**产品线**:",
    ]
    for p in profile.products:
        lines.append(f"- **{p.get('name', '')}** ({p.get('category', '')}): {p.get('description', '')}")

    lines.append("")
    lines.append("**平台能力**:")
    platform = profile.platform
    lines.append(f"- 名称: {platform.get('name', '')}")
    lines.append(f"- 定价: {platform.get('pricing', '')}")
    for feat in platform.get("features", []):
        lines.append(f"  - {feat}")

    lines.append("")
    lines.append("**核心竞争优势**:")
    for a in profile.advantages:
        lines.append(f"- {a}")

    lines.append("")
    lines.append("**合作模式偏好**:")
    for p in profile.partnership_preferences:
        lines.append(f"- {p.get('type', '')}: {p.get('description', '')}")

    return "\n".join(lines)
