#!/usr/bin/env python3
"""Render a one-page Chinese resume from JSON without a TeX dependency."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


THEMES = {
    "internet": {
        "left": 13.0 * mm,
        "right": 13.0 * mm,
        "top": 7.8 * mm,
        "bottom": 6.8 * mm,
        "body_size": 10.5,
        "leading": 12.25,
        "section_size": 12.3,
        "entry_size": 10.5,
        "section_before": 4.2,
        "section_after": 1.4,
        "entry_gap": 1.2,
        "bullet_gap": 1.1,
    },
    "finance": {
        "left": 13.0 * mm,
        "right": 13.0 * mm,
        "top": 7.2 * mm,
        "bottom": 7.2 * mm,
        "body_size": 10.4,
        "leading": 11.75,
        "section_size": 12.3,
        "entry_size": 10.4,
        "section_before": 3.7,
        "section_after": 1.2,
        "entry_gap": 1.0,
        "bullet_gap": 0.9,
    },
}


def _first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def register_fonts() -> tuple[str, str]:
    """Prefer Microsoft YaHei; fall back to common CJK fonts."""
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    custom_regular = os.environ.get("RESUME_FONT")
    custom_bold = os.environ.get("RESUME_FONT_BOLD")
    regular = _first_existing(
        [
            Path(custom_regular) if custom_regular else Path("__missing__"),
            windows / "msyh.ttc",
            windows / "simhei.ttf",
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            windows / "simsun.ttc",
        ]
    )
    bold = _first_existing(
        [
            Path(custom_bold) if custom_bold else Path("__missing__"),
            windows / "msyhbd.ttc",
            windows / "simhei.ttf",
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            regular or Path("__missing__"),
        ]
    )
    if not regular or not bold:
        raise RuntimeError(
            "未找到可用中文字体。请安装 Microsoft YaHei/Noto Sans CJK，或设置 RESUME_FONT 与 RESUME_FONT_BOLD。"
        )
    pdfmetrics.registerFont(TTFont("ResumeSans", str(regular)))
    pdfmetrics.registerFont(TTFont("ResumeSans-Bold", str(bold)))
    pdfmetrics.registerFontFamily(
        "ResumeSans",
        normal="ResumeSans",
        bold="ResumeSans-Bold",
        italic="ResumeSans",
        boldItalic="ResumeSans-Bold",
    )
    return "ResumeSans", "ResumeSans-Bold"


def esc(value: Any) -> str:
    text = str(value or "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ResumeRenderer:
    def __init__(self, data: dict[str, Any], output: Path, theme: str) -> None:
        self.data = data
        self.output = output
        self.theme_name = theme
        self.cfg = THEMES[theme]
        self.width, self.height = A4
        self.x = self.cfg["left"]
        self.content_width = self.width - self.cfg["left"] - self.cfg["right"]
        self.y = self.height - self.cfg["top"]
        self.font, self.bold = register_fonts()
        self.pdf = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
        profile = data.get("profile", {})
        self.pdf.setTitle(str(profile.get("name", "中文简历")))
        self.pdf.setAuthor(str(profile.get("name", "候选人")))
        self.pdf.setSubject("由秋招简历 AI 定制系统生成")

    def style(
        self,
        *,
        size: float | None = None,
        leading: float | None = None,
        alignment: int = TA_LEFT,
        font: str | None = None,
        left_indent: float = 0,
        first_indent: float = 0,
    ) -> ParagraphStyle:
        return ParagraphStyle(
            name="inline",
            fontName=font or self.font,
            fontSize=size or self.cfg["body_size"],
            leading=leading or self.cfg["leading"],
            textColor="#000000",
            alignment=alignment,
            leftIndent=left_indent,
            firstLineIndent=first_indent,
            spaceBefore=0,
            spaceAfter=0,
            allowWidows=0,
            allowOrphans=0,
            splitLongWords=1,
        )

    def paragraph(
        self,
        html: str,
        x: float,
        width: float,
        style: ParagraphStyle,
        y: float | None = None,
    ) -> float:
        top = self.y if y is None else y
        para = Paragraph(html, style)
        _, height = para.wrap(width, self.height)
        para.drawOn(self.pdf, x, top - height)
        return top - height

    def header(self) -> None:
        profile = self.data["profile"]
        name = esc(profile.get("name", "候选人"))
        target = esc(profile.get("target", ""))
        contacts = [esc(item) for item in profile.get("contacts", []) if item]

        if self.theme_name == "internet":
            right_width = 68 * mm
            left_width = self.content_width - right_width - 5 * mm
            self.paragraph(
                f"<b>{name}</b>", self.x, left_width,
                self.style(size=20.5, leading=22.0), y=self.y
            )
            if target:
                self.paragraph(target, self.x, left_width, self.style(size=11.0, leading=12.0), y=self.y - 23.0)
            contact_html = "<br/>".join(contacts[:3])
            self.paragraph(
                contact_html,
                self.x + self.content_width - right_width,
                right_width,
                self.style(size=9.1, leading=10.6, alignment=TA_RIGHT),
                y=self.y - 1.0,
            )
            self.y -= 42.0
        else:
            photo = profile.get("photo")
            show_photo = bool(profile.get("show_photo") and photo)
            photo_width = 22 * mm if show_photo else 0
            name_width = self.content_width - photo_width - (5 * mm if show_photo else 0)
            self.paragraph(
                f"<b>{name}</b>", self.x, name_width,
                self.style(size=20.5, leading=22.0), y=self.y
            )
            subline = " ｜ ".join(contacts)
            if target:
                subline = f"{target} ｜ {subline}" if subline else target
            self.paragraph(subline, self.x, name_width, self.style(size=9.8, leading=11.2), y=self.y - 23.0)
            if show_photo:
                photo_path = Path(str(photo))
                if not photo_path.is_absolute():
                    photo_path = (self.output.parent / photo_path).resolve()
                if photo_path.exists():
                    self.pdf.drawImage(
                        str(photo_path),
                        self.x + self.content_width - photo_width,
                        self.y - 29 * mm,
                        width=photo_width,
                        height=29 * mm,
                        preserveAspectRatio=True,
                        anchor="c",
                        mask="auto",
                    )
                    self.y -= 31 * mm
                else:
                    self.y -= 40.0
            else:
                self.y -= 40.0

    def section_title(self, title: str) -> None:
        self.y -= self.cfg["section_before"]
        self.y = self.paragraph(
            f"<b>{esc(title)}</b>",
            self.x,
            self.content_width,
            self.style(size=self.cfg["section_size"], leading=13.2),
        )
        self.pdf.setStrokeColorRGB(0.25, 0.25, 0.25)
        self.pdf.setLineWidth(0.55)
        self.pdf.line(self.x, self.y + 0.8, self.x + self.content_width, self.y + 0.8)
        self.y -= self.cfg["section_after"]

    def entry(self, item: dict[str, Any]) -> None:
        date = esc(item.get("date", ""))
        right_width = 35 * mm
        left_width = self.content_width - right_width - 2 * mm
        title = esc(item.get("title", ""))
        subtitle = esc(item.get("subtitle", ""))
        left = f"<b>{title}</b>"
        if subtitle:
            left += f" ｜ {subtitle}"
        left_y = self.paragraph(left, self.x, left_width, self.style(size=self.cfg["entry_size"], leading=11.6), y=self.y)
        right_y = self.paragraph(date, self.x + self.content_width - right_width, right_width, self.style(size=self.cfg["entry_size"], leading=11.6, alignment=TA_RIGHT), y=self.y)
        self.y = min(left_y, right_y) - self.cfg["entry_gap"]

        for bullet in item.get("bullets", []):
            if isinstance(bullet, str):
                label, text = "", bullet
            else:
                label, text = bullet.get("label", ""), bullet.get("text", "")
            body = esc(text)
            if label:
                body = f"<b>{esc(label)}：</b>{body}"
            bullet_x = self.x + 5.3
            bullet_width = self.content_width - 5.3
            self.pdf.setFillColorRGB(0, 0, 0)
            self.pdf.circle(self.x + 2.1, self.y - self.cfg["body_size"] * 0.52, 1.15, fill=1, stroke=0)
            self.y = self.paragraph(body, bullet_x, bullet_width, self.style(), y=self.y)
            self.y -= self.cfg["bullet_gap"]

    def render(self) -> None:
        self.header()
        for section in self.data.get("sections", []):
            self.section_title(section.get("title", ""))
            for item in section.get("entries", []):
                self.entry(item)

        if self.y < self.cfg["bottom"]:
            raise RuntimeError(
                f"内容超出单页 {self.cfg['bottom'] - self.y:.1f} pt；请删减或改写内容，不要缩小模板字号。"
            )
        self.pdf.showPage()
        self.pdf.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 JSON 生成一页中文 PDF 简历")
    parser.add_argument("--input", required=True, type=Path, help="结构化简历 JSON")
    parser.add_argument("--output", required=True, type=Path, help="输出 PDF")
    parser.add_argument("--theme", choices=sorted(THEMES), default="internet")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.input.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ResumeRenderer(data, args.output, args.theme).render()
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
