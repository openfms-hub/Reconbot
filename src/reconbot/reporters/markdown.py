"""Markdown report generator — renders final report using Jinja2 template."""

from __future__ import annotations

import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class MarkdownReporter:
    def __init__(self, template_name: str = "default"):
        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            keep_trailing_newline=True,
        )
        self.template_name = template_name

    def render(
        self,
        company_name: str,
        company_profile_analysis: str,
        partnership_analysis: str,
        collector_summary: dict[str, dict],
        our_company_name: str = "",
    ) -> str:
        """Render the final Markdown report."""
        template = self.env.get_template(f"{self.template_name}.md.j2")
        return template.render(
            company_name=company_name,
            our_company_name=our_company_name,
            company_profile_analysis=company_profile_analysis,
            partnership_analysis=partnership_analysis,
            collector_summary=collector_summary,
            generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    def save(self, content: str, output_dir: str, company_name: str) -> Path:
        """Save report to file and return the path."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in company_name
        ).strip()
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"{safe_name}_调研报告_{date_str}.md"

        filepath = output_path / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath
