"""
Royal Astronomical Night & Antique Parchment Qt6 StyleSheets (QSS)
with dynamic Arabic font scaling.
"""

FONT_SCALES = {
    "small": 0.90,
    "normal": 1.00,
    "large": 1.12,
    "xlarge": 1.24,
}

PALETTES = {
    "night": {
        "bg_abyss": "#060a11",
        "bg_deep": "#0b1320",
        "bg_panel": "#0f1b2d",
        "bg_card": "#15253d",
        "bg_hover": "#1d3252",
        "gold_bright": "#f5d77f",
        "gold_primary": "#d4af37",
        "gold_dark": "#9e7c1f",
        "border_gold": "#5d4c1e",
        "border_subtle": "#243754",
        "teal": "#2dd4bf",
        "teal_bg": "#0d2d33",
        "emerald": "#10b981",
        "amber": "#f59e0b",
        "text_main": "#f8f4ea",
        "text_sec": "#c5bfb0",
        "text_muted": "#8892a4",
        "btn_gold_fg": "#070b12",
    },
    "parchment": {
        "bg_abyss": "#f4ede0",
        "bg_deep": "#ebe0ca",
        "bg_panel": "#fffaf0",
        "bg_card": "#f3e8d2",
        "bg_hover": "#e7d8b9",
        "gold_bright": "#7a5306",
        "gold_primary": "#9c6f12",
        "gold_dark": "#75510a",
        "border_gold": "#c7a65c",
        "border_subtle": "#d8c9aa",
        "teal": "#0f766e",
        "teal_bg": "#dff5f0",
        "emerald": "#059669",
        "amber": "#d97706",
        "text_main": "#1d160d",
        "text_sec": "#4a3d2a",
        "text_muted": "#6e5f47",
        "btn_gold_fg": "#fffdf7",
    },
}


def get_palette(theme_name: str) -> dict:
    return PALETTES.get(theme_name, PALETTES["night"])


def build_stylesheet(theme_name: str, scale_key: str, ui_font: str, serif_font: str) -> str:
    p = get_palette(theme_name)
    s = FONT_SCALES.get(scale_key, 1.0)

    def px(base: int) -> str:
        return f"{max(10, round(base * s))}px"

    return f"""
    QMainWindow, QDialog {{
        background-color: {p['bg_abyss']};
        color: {p['text_main']};
        font-family: "{ui_font}", "Sans Serif";
        font-size: {px(14)};
    }}
    QWidget {{
        color: {p['text_main']};
        font-family: "{ui_font}", "Sans Serif";
        font-size: {px(14)};
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel[role="title"] {{
        font-family: "{serif_font}", "{ui_font}";
        font-size: {px(23)};
        font-weight: bold;
        color: {p['gold_bright']};
    }}
    QLabel[role="section-title"] {{
        font-family: "{serif_font}", "{ui_font}";
        font-size: {px(24)};
        font-weight: bold;
        color: {p['gold_bright']};
    }}
    QLabel[role="subtitle"] {{
        color: {p['text_sec']};
        font-size: {px(13)};
    }}
    QLabel[role="ayah"] {{
        font-family: "{serif_font}", "{ui_font}";
        font-size: {px(22)};
        color: {p['text_main']};
        padding: 8px;
    }}
    QLabel[role="badge"] {{
        background-color: {p['bg_card']};
        color: {p['gold_bright']};
        border: 1px solid {p['gold_primary']};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: {px(12)};
        font-weight: 600;
    }}
    QLabel[role="teal-badge"] {{
        background-color: {p['teal_bg']};
        color: {p['teal']};
        border: 1px solid {p['teal']};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: {px(12)};
        font-weight: bold;
    }}
    QFrame[panel="header"] {{
        background-color: {p['bg_deep']};
        border-bottom: 1px solid {p['gold_primary']};
    }}
    QFrame[panel="navstrip"] {{
        background-color: {p['bg_deep']};
        border-bottom: 1px solid {p['border_subtle']};
    }}
    QFrame[panel="memory"] {{
        background-color: {p['bg_panel']};
        border: 1px solid {p['gold_primary']};
        border-radius: 12px;
    }}
    QFrame[panel="glass"] {{
        background-color: {p['bg_panel']};
        border: 1px solid {p['border_gold']};
        border-radius: 16px;
    }}
    QFrame[panel="card"] {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border_subtle']};
        border-radius: 12px;
    }}
    QFrame[panel="wahi"] {{
        background-color: {p['teal_bg']};
        border: 1px solid {p['teal']};
        border-radius: 14px;
    }}
    QFrame[panel="footer"] {{
        background-color: {p['bg_deep']};
        border-top: 1px solid {p['border_gold']};
    }}
    QPushButton {{
        background-color: {p['bg_card']};
        color: {p['text_main']};
        border: 1px solid {p['border_gold']};
        border-radius: 10px;
        padding: 7px 14px;
        font-size: {px(13)};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {p['bg_hover']};
        border-color: {p['gold_bright']};
        color: {p['gold_bright']};
    }}
    QPushButton[btn="gold"] {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {p['gold_primary']}, stop:1 {p['gold_dark']});
        color: {p['btn_gold_fg']};
        border: 1px solid {p['gold_bright']};
        font-weight: bold;
    }}
    QPushButton[btn="gold"]:hover {{
        background-color: {p['gold_bright']};
        color: #070b12;
    }}
    QPushButton[btn="nav"] {{
        border-radius: 16px;
        padding: 7px 14px;
        background-color: {p['bg_card']};
        color: {p['text_sec']};
        border: 1px solid {p['border_subtle']};
    }}
    QPushButton[btn="nav"][active="true"] {{
        background-color: {p['gold_primary']};
        color: {p['btn_gold_fg']};
        border: 1px solid {p['gold_bright']};
        font-weight: bold;
    }}
    QPushButton[btn="pill"][active="true"] {{
        background-color: {p['bg_hover']};
        color: {p['gold_bright']};
        border: 1.5px solid {p['gold_primary']};
        font-weight: bold;
    }}
    QPushButton[btn="dev"] {{
        background-color: {p['bg_panel']};
        color: {p['gold_bright']};
        border: 1.5px solid {p['gold_primary']};
        border-radius: 16px;
        padding: 6px 18px;
        font-weight: bold;
    }}
    QPushButton[btn="dev"]:hover {{
        background-color: {p['gold_primary']};
        color: {p['btn_gold_fg']};
    }}
    QLineEdit {{
        background-color: {p['bg_card']};
        color: {p['text_main']};
        border: 1px solid {p['gold_primary']};
        border-radius: 10px;
        padding: 7px 12px;
        font-size: {px(14)};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {p['bg_abyss']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border_gold']};
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p['gold_primary']};
    }}
    QScrollBar:horizontal {{
        background: {p['bg_abyss']};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p['border_gold']};
        min-width: 28px;
        border-radius: 4px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0px;
        height: 0px;
    }}
    QSlider::groove:horizontal {{
        height: 8px;
        background: {p['bg_card']};
        border: 1px solid {p['border_gold']};
        border-radius: 4px;
    }}
    QSlider::sub-page:horizontal {{
        background: {p['gold_primary']};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {p['gold_bright']};
        border: 2px solid #070b12;
        width: 20px;
        height: 20px;
        margin: -7px 0;
        border-radius: 10px;
    }}
    QProgressBar {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border_gold']};
        border-radius: 8px;
        text-align: center;
        color: {p['text_main']};
        min-height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {p['emerald']};
        border-radius: 7px;
    }}
    """
