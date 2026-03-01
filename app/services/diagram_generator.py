"""
Generate inline-styled HTML diagrams for proposal documents.

All methods return pure HTML with inline styles only (no CSS classes)
so that diagrams render correctly in both WeasyPrint PDF and Google Docs
HTML import (which strips <style> blocks and ignores SVG).
"""

from typing import Any


class DiagramGenerator:

    # ── Colour palette (matches proposal_template.html) ──────────────
    _DARK_BLUE = "#1E40AF"
    _MID_BLUE = "#2563EB"
    _LIGHT_BLUE = "#3B82F6"
    _SOFT_BLUE = "#60A5FA"
    _PALE_BLUE = "#93C5FD"
    _BG_BLUE = "#EFF6FF"
    _BORDER_BLUE = "#BFDBFE"
    _GRAY_700 = "#374151"
    _GRAY_500 = "#6B7280"
    _GRAY_200 = "#E5E7EB"
    _WHITE = "#ffffff"

    # ─────────────────────────────────────────────────────────────────
    # 1. System Architecture Diagram
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_architecture_diagram(
        frontend: list[str],
        backend: list[str],
        database: list[str],
        infrastructure: list[str],
        third_party: list[str],
    ) -> str:
        if not any([frontend, backend, database, infrastructure]):
            return ""

        C = DiagramGenerator

        def _tech_chips(techs: list[str], chip_bg: str, chip_color: str) -> str:
            """Render individual technology chips inside a layer."""
            if not techs:
                return '<span style="font-size:8pt; opacity:0.7;">—</span>'
            chips = "".join(
                f'<span style="display:inline-block; background:{chip_bg}; color:{chip_color};'
                f' padding:2pt 7pt; margin:2pt 3pt; font-size:7.5pt; font-weight:600;'
                f' border-radius:3pt; border:0.5pt solid {chip_color};">{t}</span>'
                for t in techs
            )
            return f'<div style="margin-top:4pt;">{chips}</div>'

        def _layer_box(label: str, techs: list[str], bg: str, chip_bg: str,
                       chip_color: str, color: str = C._WHITE) -> str:
            chips_html = _tech_chips(techs, chip_bg, chip_color)
            return (
                f'<td style="background:{bg}; color:{color}; padding:12pt 14pt;'
                f' text-align:center; border:1pt solid {C._BORDER_BLUE};">'
                f'<div style="font-weight:700; font-size:9.5pt; margin-bottom:2pt;">{label}</div>'
                f'{chips_html}'
                f'</td>'
            )

        def _arrow_row(colspan: int = 1) -> str:
            return (
                f'<tr><td colspan="{colspan}" style="text-align:center; padding:2pt 0;'
                f' font-size:12pt; color:{C._MID_BLUE}; border:none;">&#9660;</td></tr>'
            )

        # (label, techs, bg_color, chip_bg, chip_text_color)
        layers: list[tuple[str, list[str], str, str, str]] = []
        if frontend:
            layers.append(("Client / Frontend", frontend, C._DARK_BLUE, "rgba(255,255,255,0.2)", C._WHITE))
        if backend:
            layers.append(("Backend / API", backend, C._MID_BLUE, "rgba(255,255,255,0.2)", C._WHITE))
        if database:
            layers.append(("Database", database, C._LIGHT_BLUE, "rgba(255,255,255,0.25)", C._WHITE))
        if infrastructure:
            layers.append(("Infrastructure", infrastructure, C._SOFT_BLUE, "rgba(255,255,255,0.25)", C._WHITE))

        # Build main column rows
        main_rows: list[str] = []
        for i, (label, techs, bg, chip_bg, chip_color) in enumerate(layers):
            main_rows.append(f'<tr>{_layer_box(label, techs, bg, chip_bg, chip_color)}</tr>')
            if i < len(layers) - 1:
                main_rows.append(_arrow_row())

        main_column = (
            '<table style="border-collapse:collapse; width:100%;">'
            + "".join(main_rows)
            + "</table>"
        )

        # If third-party services exist, wrap in a side-by-side table
        if third_party:
            tp_items = "".join(
                f'<div style="padding:4pt 6pt; margin:2pt 0; font-size:8pt; font-weight:600;'
                f' background:{C._WHITE}; border:0.5pt solid {C._BORDER_BLUE};'
                f' border-radius:3pt; text-align:center;">{t}</div>'
                for t in third_party
            )
            sidebar = (
                f'<td style="width:28%; vertical-align:top; padding-left:10pt;">'
                f'<table style="border-collapse:collapse; width:100%;">'
                f'<tr><td style="background:{C._PALE_BLUE}; color:{C._DARK_BLUE}; padding:10pt 10pt;'
                f' text-align:center; border:1pt solid {C._BORDER_BLUE};">'
                f'<div style="font-weight:700; font-size:9pt; margin-bottom:6pt;">Third-party Services</div>'
                f'{tp_items}'
                f'</td></tr></table></td>'
            )
            body = (
                f'<table style="border-collapse:collapse; width:100%;">'
                f'<tr><td style="width:70%; vertical-align:top; border:none;">{main_column}</td>'
                f'{sidebar}</tr></table>'
            )
        else:
            body = main_column

        return (
            f'<div style="background:{C._BG_BLUE}; border:1pt solid {C._BORDER_BLUE};'
            f' padding:14pt; margin:8pt 0 12pt;">'
            f'{body}'
            f'</div>'
        )

    # ─────────────────────────────────────────────────────────────────
    # 2. Feature Category Distribution
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_feature_category_diagram(
        features: list[dict[str, Any]],
        category_breakdown: dict[str, float],
    ) -> str:
        if not features:
            return ""

        C = DiagramGenerator

        # Group features by description (category)
        groups: dict[str, list[str]] = {}
        for f in features:
            cat = f.get("description", "General") or "General"
            groups.setdefault(cat, []).append(f.get("name", "Unnamed"))

        # Calculate hours per category from category_breakdown or features
        cat_hours: dict[str, float] = {}
        if category_breakdown:
            cat_hours = {k: float(v) for k, v in category_breakdown.items()}
        else:
            for f in features:
                cat = f.get("description", "General") or "General"
                cat_hours[cat] = cat_hours.get(cat, 0) + float(f.get("estimated_hours", 0))

        max_hours = max(cat_hours.values()) if cat_hours else 1

        # Colours for cards (cycle)
        card_colors = [C._DARK_BLUE, C._MID_BLUE, C._LIGHT_BLUE, C._SOFT_BLUE]

        cards: list[str] = []
        for idx, cat in enumerate(groups):
            color = card_colors[idx % len(card_colors)]
            count = len(groups[cat])
            hours = cat_hours.get(cat, 0)
            bar_pct = max(int((hours / max_hours) * 100), 4) if max_hours > 0 else 4

            # Feature bullet list (cap at 5)
            names = groups[cat][:5]
            bullets = "".join(
                f'<div style="font-size:7.5pt; color:{C._GRAY_700}; padding:1.5pt 0;">&#9656; {n}</div>'
                for n in names
            )
            if len(groups[cat]) > 5:
                bullets += (
                    f'<div style="font-size:7.5pt; color:{C._GRAY_500}; padding:1.5pt 0;">'
                    f'+{len(groups[cat]) - 5} more</div>'
                )

            card = (
                f'<td style="width:50%; vertical-align:top; padding:4pt;">'
                f'<div style="border:1pt solid {C._GRAY_200}; padding:8pt 10pt; background:{C._WHITE};">'
                # Header
                f'<div style="font-weight:700; font-size:9pt; color:{color}; margin-bottom:4pt;">{cat}</div>'
                # Stats
                f'<div style="font-size:8pt; color:{C._GRAY_500}; margin-bottom:4pt;">'
                f'{count} feature{"s" if count != 1 else ""} &middot; {int(hours)} hrs</div>'
                # Bar
                f'<div style="background:{C._GRAY_200}; height:6pt; width:100%; margin-bottom:6pt;">'
                f'<div style="background:{color}; height:6pt; width:{bar_pct}%;"></div>'
                f'</div>'
                # Bullets
                f'{bullets}'
                f'</div></td>'
            )
            cards.append(card)

        # Layout cards in a two-column grid
        rows: list[str] = []
        for i in range(0, len(cards), 2):
            pair = cards[i : i + 2]
            if len(pair) == 1:
                pair.append('<td style="width:50%;"></td>')
            rows.append(f'<tr>{"".join(pair)}</tr>')

        return (
            f'<table style="border-collapse:collapse; width:100%; margin:8pt 0 12pt;">'
            + "".join(rows)
            + "</table>"
        )

    # ─────────────────────────────────────────────────────────────────
    # 3. Project Phase Timeline
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_phase_timeline_diagram(
        phase_split: dict[str, float],
        timeline_weeks: Any,
        total_hours: float,
    ) -> str:
        if not phase_split:
            return ""

        C = DiagramGenerator

        # Default phase percentages if phase_split has raw hours
        total_phase = sum(float(v) for v in phase_split.values())
        if total_phase == 0:
            return ""

        # Phase colours — gradient from dark to light
        phase_colors = [C._DARK_BLUE, C._MID_BLUE, C._LIGHT_BLUE, C._PALE_BLUE, C._SOFT_BLUE]

        cells: list[str] = []
        for idx, (phase, hours) in enumerate(phase_split.items()):
            hours = float(hours)
            pct = max(int((hours / total_phase) * 100), 5) if total_phase > 0 else 10
            color = phase_colors[idx % len(phase_colors)]
            label = phase.replace("_", " ").title()

            cells.append(
                f'<td style="width:{pct}%; background:{color}; color:{C._WHITE};'
                f' text-align:center; padding:10pt 4pt; font-size:8pt;'
                f' border-right:2pt solid {C._WHITE};">'
                f'<div style="font-weight:700; margin-bottom:2pt;">{label}</div>'
                f'<div>{int(hours)} hrs</div>'
                f'<div style="font-size:7pt; opacity:0.8;">{pct}%</div>'
                f'</td>'
            )

        # Summary row
        weeks_label = f"{timeline_weeks} weeks" if timeline_weeks else ""
        summary = (
            f'<tr><td colspan="{len(cells)}" style="padding:6pt 0 0; font-size:8pt;'
            f' color:{C._GRAY_500}; text-align:center; border:none;">'
            f'Total: {int(total_hours)} hours'
            f'{" &middot; " + weeks_label if weeks_label else ""}'
            f'</td></tr>'
        )

        return (
            f'<table style="border-collapse:collapse; width:100%; margin:8pt 0 12pt;">'
            f'<tr>{"".join(cells)}</tr>'
            f'{summary}'
            f'</table>'
        )
