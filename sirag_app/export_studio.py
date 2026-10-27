"""
Pure Native QImage + QPainter High-Resolution Studio Renderer
Generates:
1) 1080x1350 Golden Station Poster PNG
2) 1600x1120 Personalized Golden Khatmah Completion Certificate PNG
Zero browser or HTML canvas required.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)


def _draw_octagram(painter: QPainter, cx: float, cy: float, r: float, color: QColor):
    painter.save()
    painter.setPen(QPen(color, 1.8))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for rot in (0, 45):
        path = QPainterPath()
        for i in range(4):
            ang = math.radians(rot + i * 90)
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        painter.drawPath(path)
    painter.restore()


def render_station_poster(event: dict, serif_family: str, ui_family: str) -> QImage:
    W, H = 1080, 1350
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    # Royal midnight gradient background
    bg = QLinearGradient(0, 0, W, H)
    bg.setColorAt(0.0, QColor("#060b14"))
    bg.setColorAt(0.5, QColor("#0e1c30"))
    bg.setColorAt(1.0, QColor("#07101c"))
    p.fillRect(0, 0, W, H, bg)

    # Subtle radial gold aura
    aura = QRadialGradient(W / 2, 260, 460)
    aura.setColorAt(0.0, QColor(212, 175, 55, 52))
    aura.setColorAt(1.0, QColor(212, 175, 55, 0))
    p.fillRect(0, 0, W, H, aura)

    # Double golden Islamic manuscript border
    p.setPen(QPen(QColor("#d4af37"), 4))
    p.drawRoundedRect(QRectF(36, 36, W - 72, H - 72), 28, 28)
    p.setPen(QPen(QColor(245, 215, 127, 110), 1.5))
    p.drawRoundedRect(QRectF(52, 52, W - 104, H - 104), 20, 20)

    for cx, cy in ((96, 96), (W - 96, 96), (96, H - 96), (W - 96, H - 96)):
        _draw_octagram(p, cx, cy, 24, QColor(212, 175, 55, 160))

    # Top Header
    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(serif_family, 24, QFont.Weight.Bold))
    p.drawText(QRectF(80, 82, W - 160, 50), Qt.AlignmentFlag.AlignCenter, "سراج أطلس السيرة النبوية ﷺ")

    p.setPen(QColor("#2dd4bf"))
    p.setFont(QFont(ui_family, 15, QFont.Weight.DemiBold))
    meta = f"{event.get('yearLabel', '')}  •  {event.get('locationName', '')}  •  المحطة {event.get('order', 1)} من 18"
    p.drawText(QRectF(80, 140, W - 160, 40), Qt.AlignmentFlag.AlignCenter, meta)

    # Event Title
    p.setPen(QColor("#ffffff"))
    p.setFont(QFont(serif_family, 38, QFont.Weight.Bold))
    p.drawText(
        QRectF(85, 200, W - 170, 110),
        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
        event.get("title", ""),
    )

    # Story Box
    story_rect = QRectF(85, 330, W - 170, 390)
    p.setPen(QPen(QColor(212, 175, 55, 130), 2))
    p.setBrush(QColor(13, 24, 40, 210))
    p.drawRoundedRect(story_rect, 20, 20)

    p.setPen(QColor("#f8f4ea"))
    p.setFont(QFont(ui_family, 18))
    story_txt = event.get("depths", {}).get("story", "")
    p.drawText(
        story_rect.adjusted(32, 28, -32, -28),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
        story_txt,
    )

    # Quranic Wahi Box
    wahi = event.get("wahi", {})
    wahi_rect = QRectF(85, 755, W - 170, 380)
    p.setPen(QPen(QColor("#2dd4bf"), 2.2))
    p.setBrush(QColor(11, 38, 44, 220))
    p.drawRoundedRect(wahi_rect, 20, 20)

    p.setPen(QColor("#2dd4bf"))
    p.setFont(QFont(ui_family, 16, QFont.Weight.Bold))
    p.drawText(
        QRectF(115, 778, W - 230, 36),
        Qt.AlignmentFlag.AlignCenter,
        f"✨ نبض الوحي المتزامن — {wahi.get('surah', '')}",
    )

    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(serif_family, 27, QFont.Weight.Bold))
    p.drawText(
        QRectF(115, 825, W - 230, 175),
        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
        wahi.get("ayah", ""),
    )

    p.setPen(QColor("#c5bfb0"))
    p.setFont(QFont(ui_family, 14))
    p.drawText(
        QRectF(115, 1010, W - 230, 105),
        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
        wahi.get("context", ""),
    )

    # Footer Signature
    p.setPen(QColor("#d4af37"))
    p.setFont(QFont(ui_family, 14, QFont.Weight.DemiBold))
    p.drawText(
        QRectF(80, H - 125, W - 160, 45),
        Qt.AlignmentFlag.AlignCenter,
        "سراج أطلس السيرة النبوية ﷺ  •  تم التطوير بواسطة محمد صلاح عبد الخالق",
    )

    p.end()
    return img


def render_khatmah_certificate(
    reader_name: str,
    completed_councils: int,
    mastery_pct: int,
    hijri_str: str,
    serif_family: str,
    ui_family: str,
) -> QImage:
    W, H = 1600, 1120
    img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    bg = QLinearGradient(0, 0, W, H)
    bg.setColorAt(0.0, QColor("#070d18"))
    bg.setColorAt(0.5, QColor("#102038"))
    bg.setColorAt(1.0, QColor("#070d18"))
    p.fillRect(0, 0, W, H, bg)

    aura = QRadialGradient(W / 2, H / 2, 620)
    aura.setColorAt(0.0, QColor(212, 175, 55, 55))
    aura.setColorAt(1.0, QColor(212, 175, 55, 0))
    p.fillRect(0, 0, W, H, aura)

    p.setPen(QPen(QColor("#d4af37"), 5))
    p.drawRoundedRect(QRectF(42, 42, W - 84, H - 84), 30, 30)
    p.setPen(QPen(QColor("#f5d77f"), 1.8))
    p.drawRoundedRect(QRectF(62, 62, W - 124, H - 124), 22, 22)

    for cx, cy in ((112, 112), (W - 112, 112), (112, H - 112), (W - 112, H - 112)):
        _draw_octagram(p, cx, cy, 34, QColor("#d4af37"))

    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(serif_family, 28, QFont.Weight.Bold))
    p.drawText(QRectF(100, 95, W - 200, 55), Qt.AlignmentFlag.AlignCenter, "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ")

    p.setPen(QColor("#2dd4bf"))
    p.setFont(QFont(ui_family, 17, QFont.Weight.Bold))
    p.drawText(
        QRectF(100, 165, W - 200, 42),
        Qt.AlignmentFlag.AlignCenter,
        "وثيقة إجازة واستكشاف معرفي — سراج أطلس السيرة النبوية ﷺ",
    )

    p.setPen(QColor("#ffffff"))
    p.setFont(QFont(serif_family, 44, QFont.Weight.Bold))
    p.drawText(
        QRectF(100, 225, W - 200, 80),
        Qt.AlignmentFlag.AlignCenter,
        "شهادة إتمام ومدارسة السيرة النبوية الشريفة",
    )

    p.setPen(QColor("#c5bfb0"))
    p.setFont(QFont(ui_family, 19))
    p.drawText(
        QRectF(150, 330, W - 300, 48),
        Qt.AlignmentFlag.AlignCenter,
        "يشهد «سراج أطلس السيرة النبوية» بأن المستكشف الكريم / المستكشفة الكريمة:",
    )

    # Honoree Name Banner
    display_name = reader_name.strip() or "محبُّ السيرة النبوية ﷺ"
    name_rect = QRectF(310, 395, W - 620, 115)
    p.setPen(QPen(QColor("#f5d77f"), 2.5))
    p.setBrush(QColor(212, 175, 55, 36))
    p.drawRoundedRect(name_rect, 20, 20)

    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(serif_family, 40, QFont.Weight.Bold))
    p.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, display_name)

    p.setPen(QColor("#f8f4ea"))
    p.setFont(QFont(ui_family, 19))
    body = (
        f"قد أتمّ مدارسة واستكشاف محطات السيرة النبوية الشريفة ومجالسها التفاعلية\n"
        f"بإنجاز ({completed_councils} من 30 مجلساً) ونسبة استكشاف شاملة ({mastery_pct}%) في الأطلس والمشاهد النبوية،\n"
        f"سائلين الله تعالى أن يرزقه شفاعة نبيه المصطفى ﷺ وحُسن الاقتداء بهديه الشريف."
    )
    p.drawText(
        QRectF(160, 540, W - 320, 175),
        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
        body,
    )

    # Prophetic Seal Emblem at Bottom Center
    seal_cx, seal_cy = W / 2, 835
    _draw_octagram(p, seal_cx, seal_cy, 68, QColor("#f5d77f"))
    p.setPen(QPen(QColor("#d4af37"), 2.5))
    p.setBrush(QColor("#0b1628"))
    p.drawEllipse(QPointF(seal_cx, seal_cy), 54, 54)
    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(serif_family, 16, QFont.Weight.Bold))
    p.drawText(
        QRectF(seal_cx - 50, seal_cy - 44, 100, 88),
        Qt.AlignmentFlag.AlignCenter,
        "الله\nرسول\nمحمد",
    )

    # Date & Developer Attribution
    p.setPen(QColor("#2dd4bf"))
    p.setFont(QFont(ui_family, 16, QFont.Weight.Bold))
    p.drawText(QRectF(120, 945, 520, 42), Qt.AlignmentFlag.AlignCenter, f"التاريخ الهجري: {hijri_str}")

    p.setPen(QColor("#f5d77f"))
    p.setFont(QFont(ui_family, 15, QFont.Weight.Bold))
    p.drawText(
        QRectF(W - 680, 945, 560, 42),
        Qt.AlignmentFlag.AlignCenter,
        "تم التطوير بواسطة محمد صلاح عبد الخالق",
    )

    p.end()
    return img
