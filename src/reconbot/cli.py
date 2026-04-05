"""ReconBot CLI — company research from the command line."""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from reconbot.config import load_settings, load_company_profile
from reconbot.collectors.base import TargetCompany
from reconbot.pipeline import run_research

app = typer.Typer(
    name="reconbot",
    help="ReconBot — 海外目标公司自动调研与合作潜力分析工具",
    no_args_is_help=True,
)
console = Console()


@app.command()
def research(
    company_name: str = typer.Argument(..., help="目标公司名称"),
    website: Optional[str] = typer.Option(None, "--website", "-w", help="公司官网 URL"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="所在国家"),
    city: Optional[str] = typer.Option(None, "--city", help="所在城市"),
    phone: Optional[str] = typer.Option(None, "--phone", "-p", help="联系电话"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="联系邮箱"),
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="所属行业"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM 模型 (覆盖默认配置)"),
    config_dir: Optional[str] = typer.Option(None, "--config", help="配置文件目录路径"),
) -> None:
    """调研指定公司并生成分析报告。"""
    config_path = Path(config_dir) if config_dir else None

    try:
        settings = load_settings(config_path)
        our_profile = load_company_profile(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]配置错误: {e}[/red]")
        raise typer.Exit(1)

    target = TargetCompany(
        name=company_name,
        website=website or "",
        country=country or "",
        city=city or "",
        phone=phone or "",
        email=email or "",
        industry=industry or "",
    )

    console.print()
    console.rule(f"[bold]ReconBot — 调研目标: {company_name}[/bold]")
    console.print()

    _print_target_info(target)

    filepath = asyncio.run(
        run_research(target, settings, our_profile, model)
    )

    console.print()
    console.rule("[bold green]调研完成[/bold green]")
    console.print(f"  报告已保存: [bold]{filepath}[/bold]")
    console.print()


@app.command()
def batch(
    csv_file: str = typer.Argument(..., help="CSV 文件路径 (必须包含 name 列)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM 模型"),
    config_dir: Optional[str] = typer.Option(None, "--config", help="配置文件目录路径"),
) -> None:
    """批量调研 CSV 中的公司列表。"""
    config_path = Path(config_dir) if config_dir else None

    try:
        settings = load_settings(config_path)
        our_profile = load_company_profile(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]配置错误: {e}[/red]")
        raise typer.Exit(1)

    csv_path = Path(csv_file)
    if not csv_path.exists():
        console.print(f"[red]文件不存在: {csv_file}[/red]")
        raise typer.Exit(1)

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        console.print("[red]CSV 文件为空[/red]")
        raise typer.Exit(1)

    console.rule(f"[bold]ReconBot — 批量调研: {len(rows)} 家公司[/bold]")
    console.print()

    results: list[tuple[str, str, str]] = []  # (name, status, path)

    for idx, row in enumerate(rows, 1):
        name = row.get("name", "").strip()
        if not name:
            continue

        console.print(f"\n[bold]({idx}/{len(rows)}) {name}[/bold]")

        target = TargetCompany(
            name=name,
            website=row.get("website", "").strip(),
            country=row.get("country", "").strip(),
            city=row.get("city", "").strip(),
            phone=row.get("phone", "").strip(),
            email=row.get("email", "").strip(),
            industry=row.get("industry", "").strip(),
        )

        try:
            filepath = asyncio.run(
                run_research(target, settings, our_profile, model)
            )
            results.append((name, "✅", str(filepath)))
        except Exception as e:
            results.append((name, "❌", str(e)))
            console.print(f"  [red]失败: {e}[/red]")

    # Print summary
    console.print()
    console.rule("[bold]批量调研完成[/bold]")
    table = Table(title="调研结果汇总")
    table.add_column("公司", style="bold")
    table.add_column("状态")
    table.add_column("报告路径")
    for name, status, path in results:
        table.add_row(name, status, path)
    console.print(table)


@app.command()
def config(
    config_dir: Optional[str] = typer.Option(None, "--config", help="配置文件目录路径"),
) -> None:
    """查看当前配置。"""
    config_path = Path(config_dir) if config_dir else None

    try:
        settings = load_settings(config_path)
        our_profile = load_company_profile(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]配置错误: {e}[/red]")
        raise typer.Exit(1)

    console.rule("[bold]ReconBot 配置[/bold]")

    # LLM config
    console.print("\n[bold]LLM 配置[/bold]")
    console.print(f"  默认模型: {settings.llm.default_model}")
    console.print(f"  Temperature: {settings.llm.temperature}")
    console.print(f"  Max Tokens: {settings.llm.max_tokens}")
    for name, provider in settings.llm.providers.items():
        key = provider.get("api_key", "")
        masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else ("✓ 已配置" if key else "✗ 未配置")
        console.print(f"  {name}: {masked}")

    # Collectors
    console.print("\n[bold]采集器配置[/bold]")
    for name, cfg in settings.collectors.items():
        status = "[green]启用[/green]" if cfg.enabled else "[red]禁用[/red]"
        key_status = ""
        if cfg.api_key:
            key_status = " (API Key ✓)" if cfg.api_key else " (API Key ✗)"
        console.print(f"  {name}: {status}{key_status}")

    # Output
    console.print("\n[bold]输出配置[/bold]")
    console.print(f"  目录: {settings.output.dir}")
    console.print(f"  语言: {settings.output.language}")
    console.print(f"  模板: {settings.output.template}")

    # Our company
    console.print(f"\n[bold]我方公司: {our_profile.name}[/bold]")
    console.print(f"  行业: {our_profile.industry}")
    console.print(f"  目标市场: {our_profile.target_market}")
    console.print(f"  产品数: {len(our_profile.products)}")
    console.print()


def _print_target_info(target: TargetCompany) -> None:
    """Print target company info summary."""
    table = Table(title="目标公司信息", show_header=False)
    table.add_column("字段", style="bold")
    table.add_column("值")
    table.add_row("公司名称", target.name)
    if target.website:
        table.add_row("官网", target.website)
    if target.country:
        table.add_row("国家", target.country)
    if target.city:
        table.add_row("城市", target.city)
    if target.phone:
        table.add_row("电话", target.phone)
    if target.email:
        table.add_row("邮箱", target.email)
    if target.industry:
        table.add_row("行业", target.industry)
    console.print(table)
    console.print()
