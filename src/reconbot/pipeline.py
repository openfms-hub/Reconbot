"""Main orchestration pipeline — coordinates collectors, analyzers, and reporters."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from reconbot.config import Settings, CompanyProfile
from reconbot.collectors.base import TargetCompany, CollectorResult
from reconbot.collectors import WebsiteCollector, ExaCollector, TavilyCollector, GoogleCollector
from reconbot.analyzers.profiler import analyze_company
from reconbot.analyzers.matcher import analyze_partnership
from reconbot.reporters import MarkdownReporter

console = Console()


def _build_collectors(settings: Settings) -> list:
    """Instantiate enabled collectors based on settings."""
    collectors = []

    cfg = settings.collectors.get("website")
    if cfg and cfg.enabled:
        collectors.append(WebsiteCollector(
            timeout=cfg.extra.get("timeout", 30),
            max_pages=cfg.extra.get("max_pages", 10),
        ))

    cfg = settings.collectors.get("exa")
    if cfg and cfg.enabled and cfg.api_key:
        collectors.append(ExaCollector(
            api_key=cfg.api_key,
            num_results=cfg.extra.get("num_results", 10),
        ))

    cfg = settings.collectors.get("tavily")
    if cfg and cfg.enabled and cfg.api_key:
        collectors.append(TavilyCollector(
            api_key=cfg.api_key,
            max_results=cfg.extra.get("max_results", 10),
        ))

    cfg = settings.collectors.get("google")
    if cfg and cfg.enabled and cfg.api_key:
        collectors.append(GoogleCollector(
            api_key=cfg.api_key,
            cx=cfg.extra.get("cx", ""),
            num_results=cfg.extra.get("num_results", 10),
        ))

    return collectors


async def _run_collectors(
    collectors: list, target: TargetCompany
) -> list[CollectorResult]:
    """Run all collectors in parallel."""
    tasks = [c.collect(target) for c in collectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed: list[CollectorResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append(CollectorResult(
                source=collectors[i].name,
                success=False,
                error=str(result),
            ))
        else:
            processed.append(result)

    return processed


async def run_research(
    target: TargetCompany,
    settings: Settings,
    our_profile: CompanyProfile,
    model: str | None = None,
) -> Path:
    """Execute the full research pipeline: collect → analyze → report."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # Phase 1: Parallel intelligence gathering
        task_collect = progress.add_task("情报采集中 (多路并行)...", total=None)
        collectors = _build_collectors(settings)

        if not collectors:
            console.print("[red]错误: 没有启用任何采集器，请检查 settings.yaml[/red]")
            raise SystemExit(1)

        console.print(f"  启用采集器: {', '.join(c.name for c in collectors)}")
        results = await _run_collectors(collectors, target)

        for r in results:
            status = "[green]✓[/green]" if r.success else f"[red]✗ {r.error}[/red]"
            console.print(f"  [{r.source}] {status} — {len(r.raw_texts)} 段数据")
        progress.update(task_collect, completed=True)

        # Check if we have any data
        successful = [r for r in results if r.success and r.raw_texts]
        if not successful:
            console.print("[red]错误: 所有采集器均未返回有效数据[/red]")
            raise SystemExit(1)

        # Phase 2: LLM analysis — company profile
        task_profile = progress.add_task("LLM 分析: 公司画像...", total=None)
        profile_analysis = await analyze_company(
            llm_config=settings.llm,
            company_name=target.name,
            results=results,
            language=settings.output.language,
            model=model,
        )
        progress.update(task_profile, completed=True)

        # Phase 3: LLM analysis — partnership matching
        task_match = progress.add_task("LLM 分析: 合作潜力...", total=None)
        partnership_analysis = await analyze_partnership(
            llm_config=settings.llm,
            company_name=target.name,
            company_profile_text=profile_analysis,
            our_profile=our_profile,
            language=settings.output.language,
            model=model,
        )
        progress.update(task_match, completed=True)

        # Phase 4: Generate report
        task_report = progress.add_task("生成报告...", total=None)

        collector_summary = {}
        for r in results:
            collector_summary[r.source] = {
                "success": r.success,
                "error": r.error,
                "text_count": len(r.raw_texts),
                "url_count": len(r.urls),
            }

        reporter = MarkdownReporter(template_name=settings.output.template)
        report_content = reporter.render(
            company_name=target.name,
            company_profile_analysis=profile_analysis,
            partnership_analysis=partnership_analysis,
            collector_summary=collector_summary,
            our_company_name=our_profile.name,
        )

        filepath = reporter.save(
            content=report_content,
            output_dir=settings.output.dir,
            company_name=target.name,
        )
        progress.update(task_report, completed=True)

    return filepath
