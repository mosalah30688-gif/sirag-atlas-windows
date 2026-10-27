"""
Pure Native Qt6 QPainter Interactive Vector Canvases (Zero Browser / Zero HTML / Zero SVG DOM):
1. ArabiaMapCanvas       — Chrono-Spatial Prophetic Atlas with animated routes & glowing pulse
2. HijrahRouteCanvas     — 480km Secret Coastal Hijrah Route with interactive day stops
3. BattleTacticalCanvas  — Smooth-interpolated Topographical Battle Simulator (6 Battles)
4. SanctuaryBlueprintCanvas — Architectural Blueprints of Al-Masjid An-Nabawi & Al-Kaaba
5. ConstellationCanvas   — Rotating 4-Orbit Companions Constellation around the Prophetic Seal
6. LineageTreeCanvas     — Interactive Golden Prophetic Lineage Tree & Sahaba Convergences
"""

import math
import re
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget


def _map_pt(x: float, y: float, vw: float, vh: float, rect: QRectF) -> QPointF:
    scale = min(rect.width() / vw, rect.height() / vh)
    ox = rect.left() + (rect.width() - vw * scale) / 2.0
    oy = rect.top() + (rect.height() - vh * scale) / 2.0
    return QPointF(ox + x * scale, oy + y * scale)


# ==============================================================================
# 1. CHRONO-SPATIAL ARABIA ATLAS CANVAS
# ==============================================================================
ROUTE_POLYLINES = {
    "abyssinia": [(430, 336), (375, 360), (262, 405)],
    "taif": [(430, 336), (465, 350)],
    "isra": [(430, 336), (355, 210), (288, 92)],
    "hijrah": [(430, 336), (434, 349), (390, 325), (368, 282), (382, 232)],
    "badr": [(382, 232), (355, 258)],
    "uhud": [(382, 232), (385, 222)],
    "khandaq": [(382, 232), (380, 229)],
    "hudaybiyah": [(382, 232), (392, 290), (414, 332)],
    "khaybar": [(382, 232), (374, 178)],
    "mutah": [(382, 232), (345, 165), (312, 118)],
    "fath": [(382, 232), (404, 286), (430, 336)],
    "tabuk": [(382, 232), (336, 148)],
    "wada": [(382, 232), (415, 295), (430, 336)],
}


class ArabiaMapCanvas(QWidget):
    stationClicked = Signal(int)  # index in filtered list

    def __init__(self, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.serif_font = serif_font
        self.ui_font = ui_font
        self.setMinimumSize(420, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self.events = []
        self.active_index = 0
        self.phase = 0.0
        self._hit_nodes = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)

    def set_events(self, events: list, active_index: int = 0):
        self.events = events or []
        self.active_index = max(0, min(active_index, max(0, len(self.events) - 1)))
        self.update()

    def set_active_index(self, idx: int):
        if not self.events:
            return
        self.active_index = max(0, min(idx, len(self.events) - 1))
        self.update()

    def _tick(self):
        if self.isVisible():
            self.phase = (self.phase + 0.09) % (2.0 * math.pi)
            self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        r = QRectF(6, 6, self.width() - 12, self.height() - 12)
        bg = QLinearGradient(r.topLeft(), r.bottomRight())
        bg.setColorAt(0.0, QColor("#07111f"))
        bg.setColorAt(0.55, QColor("#0d1d33"))
        bg.setColorAt(1.0, QColor("#060c17"))

        clip = QPainterPath()
        clip.addRoundedRect(r, 16, 16)
        p.save()
        p.setClipPath(clip)
        p.fillRect(r, bg)

        VW, VH = 680.0, 460.0
        mp = lambda x, y: _map_pt(x, y, VW, VH, r)

        # Subtle astronomical graticule lines
        grid_pen = QPen(QColor(212, 175, 55, 22), 1, Qt.PenStyle.DotLine)
        p.setPen(grid_pen)
        for gx in range(100, 650, 90):
            p.drawLine(mp(gx, 20), mp(gx, 440))
        for gy in range(60, 440, 75):
            p.drawLine(mp(40, gy), mp(640, gy))

        # Red Sea body
        sea_poly = QPolygonF([
            mp(245, 145), mp(285, 155), mp(355, 275), mp(405, 375),
            mp(388, 445), mp(320, 445), mp(270, 325), mp(225, 190)
        ])
        p.setPen(QPen(QColor(45, 212, 191, 55), 1.3))
        p.setBrush(QColor(12, 46, 64, 155))
        p.drawPolygon(sea_poly)

        # Arabian Peninsula & Levant landmass silhouette
        land_poly = QPolygonF([
            mp(255, 55), mp(485, 55), mp(615, 185), mp(635, 345),
            mp(525, 435), mp(410, 415), mp(360, 290), mp(290, 160), mp(255, 120)
        ])
        land_grad = QLinearGradient(mp(260, 70), mp(580, 410))
        land_grad.setColorAt(0.0, QColor(24, 42, 68, 215))
        land_grad.setColorAt(1.0, QColor(15, 27, 46, 230))
        p.setPen(QPen(QColor(212, 175, 55, 95), 1.6))
        p.setBrush(land_grad)
        p.drawPolygon(land_poly)

        # Abyssinia coast (South-West across Red Sea)
        aby_poly = QPolygonF([
            mp(165, 340), mp(275, 360), mp(305, 445), mp(165, 445)
        ])
        p.setPen(QPen(QColor(212, 175, 55, 65), 1.2))
        p.setBrush(QColor(20, 35, 56, 195))
        p.drawPolygon(aby_poly)

        # Regional geographic watermarks
        p.setPen(QColor(212, 175, 55, 95))
        p.setFont(QFont(self.serif_font, 11, QFont.Weight.Bold))
        for txt, lx, ly in [
            ("بلاد الشام وبيت المقدس", 315, 78),
            ("الحجاز والمدينة المنورة", 455, 225),
            ("مكة المكرمة وأم القرى", 495, 336),
            ("أرض الحبشة", 225, 425),
            ("نجد واليمامة", 545, 265),
        ]:
            pt = mp(lx, ly)
            p.drawText(QRectF(pt.x() - 80, pt.y() - 12, 160, 24), Qt.AlignmentFlag.AlignCenter, txt)

        active_ev = self.events[self.active_index] if self.events else None
        active_route = active_ev.get("routeId") if active_ev else None

        # Draw historical routes
        for route_id, pts in ROUTE_POLYLINES.items():
            path = QPainterPath()
            for i, (rx, ry) in enumerate(pts):
                pt = mp(rx, ry)
                if i == 0:
                    path.moveTo(pt)
                else:
                    path.lineTo(pt)
            is_cur = route_id == active_route
            pen = QPen(
                QColor("#f5d77f") if is_cur else QColor(212, 175, 55, 42),
                3.2 if is_cur else 1.4,
                Qt.PenStyle.DashLine,
            )
            if is_cur:
                pen.setDashOffset(-self.phase * 6.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        # Draw event stations
        self._hit_nodes = []
        cur_order = active_ev.get("order", 1) if active_ev else 1

        for idx, ev in enumerate(self.events):
            cx = ev.get("coords", {}).get("x", 400)
            cy = ev.get("coords", {}).get("y", 260)
            pt = mp(cx, cy)
            self._hit_nodes.append((pt, idx, ev))

            is_active = idx == self.active_index
            visited = ev.get("order", 0) < cur_order

            if is_active:
                pulse_r = 15.0 + 8.0 * (0.5 + 0.5 * math.sin(self.phase * 2.2))
                glow = QRadialGradient(pt, pulse_r * 1.5)
                glow.setColorAt(0.0, QColor(245, 215, 127, 175))
                glow.setColorAt(1.0, QColor(245, 215, 127, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(glow)
                p.drawEllipse(pt, pulse_r * 1.5, pulse_r * 1.5)

                p.setPen(QPen(QColor("#f5d77f"), 2.2))
                p.setBrush(QColor("#d4af37"))
                p.drawEllipse(pt, 8.0, 8.0)
            else:
                p.setPen(QPen(QColor("#d4af37"), 1.4))
                p.setBrush(QColor("#2dd4bf") if visited else QColor("#172840"))
                p.drawEllipse(pt, 5.5, 5.5)

        # Floating callout label for active station
        if active_ev:
            pt = mp(active_ev["coords"]["x"], active_ev["coords"]["y"])
            title = f"📍 {active_ev.get('locationName', '')}"
            box = QRectF(pt.x() - 95, max(r.top() + 10, pt.y() - 40), 190, 26)
            p.setPen(QPen(QColor("#f5d77f"), 1.3))
            p.setBrush(QColor(8, 15, 28, 232))
            p.drawRoundedRect(box, 10, 10)
            p.setPen(QColor("#f5d77f"))
            p.setFont(QFont(self.ui_font, 9, QFont.Weight.Bold))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, title)

        p.restore()
        p.setPen(QPen(QColor("#d4af37"), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 16, 16)
        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        best_idx = -1
        best_d = 22.0
        for pt, idx, _ in self._hit_nodes:
            d = math.hypot(pos.x() - pt.x(), pos.y() - pt.y())
            if d < best_d:
                best_d = d
                best_idx = idx
        if best_idx >= 0:
            self.stationClicked.emit(best_idx)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        for pt, _idx, item in self._hit_nodes:
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 16.0:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                QToolTip.showText(
                    ev.globalPosition().toPoint(),
                    f"{item.get('yearLabel', '')} — {item.get('title', '')}",
                    self,
                )
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ==============================================================================
# 2. HIJRAH 480KM DAY-BY-DAY ROUTE CANVAS
# ==============================================================================
class HijrahRouteCanvas(QWidget):
    stopClicked = Signal(int)

    def __init__(self, ui_font: str, parent=None):
        super().__init__(parent)
        self.ui_font = ui_font
        self.stops = []
        self.active_idx = 0
        self.phase = 0.0
        self._pts = []
        self.setMinimumSize(380, 340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        if self.isVisible():
            self.phase = (self.phase + 0.1) % (2.0 * math.pi)
            self.update()

    def set_data(self, stops: list, active_idx: int):
        self.stops = stops or []
        self.active_idx = max(0, min(active_idx, max(0, len(self.stops) - 1)))
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(6, 6, self.width() - 12, self.height() - 12)
        p.setPen(QPen(QColor("#d4af37"), 1.5))
        p.setBrush(QColor("#081322"))
        p.drawRoundedRect(r, 16, 16)

        if not self.stops:
            p.end()
            return

        VW, VH = 560.0, 420.0
        mp = lambda x, y: _map_pt(x, y, VW, VH, r.adjusted(16, 16, -16, -16))

        # Red sea coast shimmer on the left
        coast = QPolygonF([mp(80, 20), mp(275, 20), mp(335, 400), mp(80, 400)])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(15, 58, 76, 95))
        p.drawPolygon(coast)

        pts = [mp(s["coords"]["x"], s["coords"]["y"]) for s in self.stops]
        self._pts = pts

        # Full faint path
        full_path = QPainterPath()
        for i, pt in enumerate(pts):
            if i == 0:
                full_path.moveTo(pt)
            else:
                full_path.lineTo(pt)
        p.setPen(QPen(QColor(212, 175, 55, 65), 2.2, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(full_path)

        # Traversed golden path up to active stop
        trav_path = QPainterPath()
        for i in range(self.active_idx + 1):
            if i == 0:
                trav_path.moveTo(pts[i])
            else:
                trav_path.lineTo(pts[i])
        p.setPen(QPen(QColor("#2dd4bf"), 3.8))
        p.drawPath(trav_path)

        for i, (pt, st) in enumerate(zip(pts, self.stops)):
            is_cur = i == self.active_idx
            done = i <= self.active_idx
            if is_cur:
                rad = 15 + 5 * math.sin(self.phase * 2.0)
                glow = QRadialGradient(pt, rad * 1.4)
                glow.setColorAt(0.0, QColor(245, 215, 127, 185))
                glow.setColorAt(1.0, QColor(245, 215, 127, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(glow)
                p.drawEllipse(pt, rad * 1.4, rad * 1.4)

            p.setPen(QPen(QColor("#f5d77f"), 2.0 if is_cur else 1.3))
            p.setBrush(QColor("#f5d77f") if is_cur else (QColor("#10b981") if done else QColor("#182b44")))
            p.drawEllipse(pt, 8.5 if is_cur else 6.0, 8.5 if is_cur else 6.0)

            p.setPen(QColor("#f8f4ea") if is_cur else QColor("#b8c0ce"))
            p.setFont(QFont(self.ui_font, 9, QFont.Weight.Bold if is_cur else QFont.Weight.Normal))
            lbl_rect = QRectF(pt.x() - 125, pt.y() - 12, 112, 24)
            p.drawText(lbl_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, st["dayLabel"])

        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        for i, pt in enumerate(self._pts):
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 20.0:
                self.stopClicked.emit(i)
                return


# ==============================================================================
# 3. TACTICAL BATTLE SIMULATOR CANVAS (SMOOTH UNIT INTERPOLATION)
# ==============================================================================
def _parse_svg_arrow(d_str: str, mapper) -> QPainterPath:
    path = QPainterPath()
    tokens = re.findall(r"[MLQC]|-?\d+(?:\.\d+)?", d_str or "")
    idx = 0
    cmd = ""
    while idx < len(tokens):
        tk = tokens[idx]
        if tk in ("M", "L", "Q", "C"):
            cmd = tk
            idx += 1
            continue
        if cmd == "M" and idx + 1 < len(tokens):
            pt = mapper(float(tokens[idx]), float(tokens[idx + 1]))
            path.moveTo(pt)
            idx += 2
        elif cmd == "L" and idx + 1 < len(tokens):
            pt = mapper(float(tokens[idx]), float(tokens[idx + 1]))
            path.lineTo(pt)
            idx += 2
        elif cmd == "Q" and idx + 3 < len(tokens):
            c1 = mapper(float(tokens[idx]), float(tokens[idx + 1]))
            ep = mapper(float(tokens[idx + 2]), float(tokens[idx + 3]))
            path.quadTo(c1, ep)
            idx += 4
        elif cmd == "C" and idx + 5 < len(tokens):
            c1 = mapper(float(tokens[idx]), float(tokens[idx + 1]))
            c2 = mapper(float(tokens[idx + 2]), float(tokens[idx + 3]))
            ep = mapper(float(tokens[idx + 4]), float(tokens[idx + 5]))
            path.cubicTo(c1, c2, ep)
            idx += 6
        else:
            idx += 1
    return path


class BattleTacticalCanvas(QWidget):
    def __init__(self, ui_font: str, parent=None):
        super().__init__(parent)
        self.ui_font = ui_font
        self.battle = None
        self.phase_idx = 0
        self._curr_positions = {}  # unit_id -> (x, y)
        self._target_positions = {}
        self.setMinimumSize(420, 340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._step_anim)
        self._anim.start(30)

    def set_battle_phase(self, battle: dict, phase_idx: int, instant: bool = False):
        self.battle = battle
        phases = battle.get("phases", []) if battle else []
        self.phase_idx = max(0, min(phase_idx, max(0, len(phases) - 1)))
        if phases:
            units = phases[self.phase_idx].get("units", [])
            self._target_positions = {u["id"]: (float(u["x"]), float(u["y"])) for u in units}
            if instant or not self._curr_positions:
                self._curr_positions = dict(self._target_positions)
            else:
                for uid, pos in self._target_positions.items():
                    if uid not in self._curr_positions:
                        self._curr_positions[uid] = pos
        self.update()

    def _step_anim(self):
        if not self.isVisible() or not self._target_positions:
            return
        moved = False
        for uid, (tx, ty) in self._target_positions.items():
            cx, cy = self._curr_positions.get(uid, (tx, ty))
            nx = cx + (tx - cx) * 0.22
            ny = cy + (ty - cy) * 0.22
            if abs(nx - tx) > 0.3 or abs(ny - ty) > 0.3:
                moved = True
            self._curr_positions[uid] = (nx, ny)
        if moved:
            self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(6, 6, self.width() - 12, self.height() - 12)

        bg = QRadialGradient(r.center(), max(r.width(), r.height()) * 0.65)
        bg.setColorAt(0.0, QColor("#132338"))
        bg.setColorAt(1.0, QColor("#08101c"))
        p.setPen(QPen(QColor("#d4af37"), 1.5))
        p.setBrush(bg)
        p.drawRoundedRect(r, 16, 16)

        if not self.battle:
            p.end()
            return

        VW, VH = 600.0, 380.0
        mp = lambda x, y: _map_pt(x, y, VW, VH, r.adjusted(14, 14, -14, -14))

        # Topographical grid
        p.setPen(QPen(QColor(212, 175, 55, 22), 1, Qt.PenStyle.DotLine))
        for gx in range(60, 560, 80):
            p.drawLine(mp(gx, 20), mp(gx, 360))
        for gy in range(50, 350, 65):
            p.drawLine(mp(20, gy), mp(580, gy))

        # Battle-specific terrain landmarks
        bid = self.battle.get("id", "")
        p.setFont(QFont(self.ui_font, 9, QFont.Weight.Bold))
        if bid == "uhud":
            mt = QPolygonF([mp(95, 55), mp(510, 48), mp(540, 105), mp(75, 100)])
            p.setPen(QPen(QColor("#9b7b24"), 1.5))
            p.setBrush(QColor(92, 68, 34, 145))
            p.drawPolygon(mt)
            p.setPen(QColor("#f5d77f"))
            p.drawText(QRectF(mp(220, 60), mp(380, 92)), Qt.AlignmentFlag.AlignCenter, "⛰️ جبل أُحد الشامخ")

            archers = mp(245, 195)
            p.setBrush(QColor(212, 175, 55, 90))
            p.drawEllipse(archers, 28, 18)
            p.drawText(QRectF(archers.x() - 60, archers.y() - 12, 120, 24), Qt.AlignmentFlag.AlignCenter, "جبل الرماة")
        elif bid == "khandaq":
            tr = QPainterPath()
            tr.moveTo(mp(110, 195))
            tr.quadTo(mp(300, 145), mp(490, 195))
            p.setPen(QPen(QColor("#2dd4bf"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(tr)
            p.setPen(QColor("#2dd4bf"))
            p.drawText(QRectF(mp(220, 140), mp(380, 168)), Qt.AlignmentFlag.AlignCenter, "🛡️ الخندق النبوي المحفور")
        elif bid == "badr":
            for wx, wy in [(285, 195), (315, 208), (268, 214)]:
                wpt = mp(wx, wy)
                p.setPen(QPen(QColor("#2dd4bf"), 1.5))
                p.setBrush(QColor(45, 212, 191, 95))
                p.drawEllipse(wpt, 8, 8)
            p.setPen(QColor("#2dd4bf"))
            p.drawText(QRectF(mp(225, 215), mp(365, 240)), Qt.AlignmentFlag.AlignCenter, "💧 آبار بدر")

        phases = self.battle.get("phases", [])
        if not phases:
            p.end()
            return
        phase = phases[self.phase_idx]

        # Tactical movement arrows
        for arr in phase.get("arrows", []):
            col = QColor(arr.get("color", "#f5d77f"))
            apath = _parse_svg_arrow(arr.get("d", ""), mp)
            p.setPen(QPen(col, 2.8, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(apath)
            if apath.length() > 12:
                tip = apath.pointAtPercent(1.0)
                prev = apath.pointAtPercent(max(0.0, 1.0 - 12.0 / apath.length()))
                ang = math.atan2(tip.y() - prev.y(), tip.x() - prev.x())
                head = QPolygonF([
                    tip,
                    QPointF(tip.x() - 10 * math.cos(ang - 0.45), tip.y() - 10 * math.sin(ang - 0.45)),
                    QPointF(tip.x() - 10 * math.cos(ang + 0.45), tip.y() - 10 * math.sin(ang + 0.45)),
                ])
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(col)
                p.drawPolygon(head)

        # Units rendering
        type_colors = {
            "command": ("#f5d77f", "#070b12"),
            "muslim": ("#10b981", "#ffffff"),
            "archers": ("#2dd4bf", "#070b12"),
            "cavalry": ("#f59e0b", "#070b12"),
            "enemy": ("#ef4444", "#ffffff"),
        }
        for u in phase.get("units", []):
            uid = u["id"]
            ux, uy = self._curr_positions.get(uid, (float(u["x"]), float(u["y"])))
            pt = mp(ux, uy)
            fill_hex, _fg = type_colors.get(u.get("type", "muslim"), ("#10b981", "#ffffff"))

            p.setPen(QPen(QColor("#ffffff"), 1.6))
            p.setBrush(QColor(fill_hex))
            if u.get("type") == "command":
                p.drawRoundedRect(QRectF(pt.x() - 13, pt.y() - 13, 26, 26), 7, 7)
            elif u.get("type") == "enemy":
                dia = QPolygonF([
                    QPointF(pt.x(), pt.y() - 12),
                    QPointF(pt.x() + 12, pt.y()),
                    QPointF(pt.x(), pt.y() + 12),
                    QPointF(pt.x() - 12, pt.y()),
                ])
                p.drawPolygon(dia)
            else:
                p.drawEllipse(pt, 11, 11)

            lbl_box = QRectF(pt.x() - 75, pt.y() + 13, 150, 22)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(6, 11, 20, 210))
            p.drawRoundedRect(lbl_box, 6, 6)
            p.setPen(QColor("#f8f4ea"))
            p.setFont(QFont(self.ui_font, 8, QFont.Weight.Bold))
            p.drawText(lbl_box, Qt.AlignmentFlag.AlignCenter, u.get("label", ""))

        p.end()


# ==============================================================================
# 4. SACRED SANCTUARIES ARCHITECTURAL BLUEPRINT CANVAS
# ==============================================================================
class SanctuaryBlueprintCanvas(QWidget):
    hotspotClicked = Signal(int)

    def __init__(self, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.serif_font = serif_font
        self.ui_font = ui_font
        self.site_key = "madinah"
        self.hotspots = []
        self.active_idx = 0
        self._pts = []
        self.phase = 0.0
        self.setMinimumSize(400, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        if self.isVisible():
            self.phase = (self.phase + 0.09) % (2.0 * math.pi)
            self.update()

    def set_site(self, site_key: str, hotspots: list, active_idx: int = 0):
        self.site_key = site_key
        self.hotspots = hotspots or []
        self.active_idx = max(0, min(active_idx, max(0, len(self.hotspots) - 1)))
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(6, 6, self.width() - 12, self.height() - 12)
        p.setPen(QPen(QColor("#d4af37"), 1.6))
        p.setBrush(QColor("#081423"))
        p.drawRoundedRect(r, 16, 16)

        VW, VH = 520.0, 420.0
        mp = lambda x, y: _map_pt(x, y, VW, VH, r.adjusted(14, 14, -14, -14))

        if self.site_key == "madinah":
            # Prophetic Mosque outer architectural courtyard
            tl, br = mp(70, 55), mp(450, 375)
            mosque_rect = QRectF(tl, br)
            p.setPen(QPen(QColor("#d4af37"), 2.4))
            p.setBrush(QColor(15, 30, 50, 210))
            p.drawRoundedRect(mosque_rect, 12, 12)

            # Blessed Rawdah emerald carpet zone
            rtl, rbr = mp(175, 255), mp(325, 355)
            p.setPen(QPen(QColor("#10b981"), 1.8, Qt.PenStyle.DashLine))
            p.setBrush(QColor(16, 185, 129, 55))
            p.drawRoundedRect(QRectF(rtl, rbr), 8, 8)

            # Sacred Chamber (Al-Hujrah Ash-Sharifah) on the East
            htl, hbr = mp(332, 262), mp(428, 352)
            p.setPen(QPen(QColor("#f5d77f"), 2.2))
            p.setBrush(QColor(212, 175, 55, 65))
            p.drawRoundedRect(QRectF(htl, hbr), 8, 8)

            # Suffah platform in the North
            stl, sbr = mp(95, 72), mp(265, 128)
            p.setPen(QPen(QColor("#2dd4bf"), 1.4))
            p.setBrush(QColor(45, 212, 191, 35))
            p.drawRoundedRect(QRectF(stl, sbr), 8, 8)

            p.setPen(QColor("#f5d77f"))
            p.setFont(QFont(self.serif_font, 11, QFont.Weight.Bold))
            p.drawText(QRectF(mp(160, 378), mp(360, 405)), Qt.AlignmentFlag.AlignCenter, "⬇️ اتجاه القبلة الشريفة (جنوباً نحو مكة)")
        else:
            # Al-Masjid Al-Haram Mataf concentric rings + Kaaba cube + Hijr Ismail
            center = mp(260, 215)
            unit = abs(mp(360, 215).x() - center.x())
            for mult, alpha in [(1.55, 35), (1.22, 55), (0.88, 75)]:
                p.setPen(QPen(QColor(212, 175, 55, alpha + 40), 1.3))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(center, unit * mult, unit * mult)

            # Hijr Ismail (semi-circular Hatim)
            hijr_rect = QRectF(center.x() - unit * 0.42, center.y() - unit * 0.68, unit * 0.84, unit * 0.65)
            p.setPen(QPen(QColor("#2dd4bf"), 2.4))
            p.drawArc(hijr_rect, 0 * 16, 180 * 16)

            # Holy Kaaba square
            k_half = unit * 0.36
            k_rect = QRectF(center.x() - k_half, center.y() - k_half, k_half * 2, k_half * 2)
            p.setPen(QPen(QColor("#f5d77f"), 2.8))
            p.setBrush(QColor("#0a0c10"))
            p.drawRoundedRect(k_rect, 6, 6)
            # Golden Kiswah belt
            belt = QRectF(k_rect.left() + 4, k_rect.top() + k_rect.height() * 0.24, k_rect.width() - 8, 7)
            p.fillRect(belt, QColor("#d4af37"))

        # Interactive hotspots
        self._pts = []
        for idx, hs in enumerate(self.hotspots):
            pt = mp(float(hs.get("x", 260)), float(hs.get("y", 210)))
            self._pts.append((pt, idx, hs))
            is_cur = idx == self.active_idx
            col = QColor(hs.get("color", "#f5d77f"))

            if is_cur:
                rad = 15 + 5 * math.sin(self.phase * 2.2)
                glow = QRadialGradient(pt, rad * 1.5)
                glow.setColorAt(0.0, QColor(col.red(), col.green(), col.blue(), 190))
                glow.setColorAt(1.0, QColor(col.red(), col.green(), col.blue(), 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(glow)
                p.drawEllipse(pt, rad * 1.5, rad * 1.5)

            p.setPen(QPen(QColor("#ffffff"), 2.0 if is_cur else 1.3))
            p.setBrush(col)
            p.drawEllipse(pt, 9.5 if is_cur else 7.0, 9.5 if is_cur else 7.0)

        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        for pt, idx, _ in self._pts:
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 22.0:
                self.hotspotClicked.emit(idx)
                return

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        for pt, _idx, hs in self._pts:
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 18.0:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                QToolTip.showText(ev.globalPosition().toPoint(), hs.get("name", ""), self)
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ==============================================================================
# 5. COMPANIONS CONSTELLATION 4-ORBIT CANVAS
# ==============================================================================
class ConstellationCanvas(QWidget):
    companionClicked = Signal(str)

    def __init__(self, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.serif_font = serif_font
        self.ui_font = ui_font
        self.companions = []
        self.orbit_filter = 0  # 0 = all, 1..4
        self.active_id = ""
        self.rot_offset = 0.0
        self._nodes = []
        self.setMinimumSize(420, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(55)

    def _tick(self):
        if self.isVisible():
            self.rot_offset = (self.rot_offset + 0.12) % 360.0
            self.update()

    def set_state(self, companions: list, active_id: str, orbit_filter: int = 0):
        self.companions = companions or []
        self.active_id = active_id
        self.orbit_filter = orbit_filter
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(6, 6, self.width() - 12, self.height() - 12)

        bg = QRadialGradient(r.center(), max(r.width(), r.height()) * 0.6)
        bg.setColorAt(0.0, QColor("#132540"))
        bg.setColorAt(1.0, QColor("#060b14"))
        p.setPen(QPen(QColor("#d4af37"), 1.5))
        p.setBrush(bg)
        p.drawRoundedRect(r, 16, 16)

        cx, cy = r.center().x(), r.center().y()
        max_rad = min(r.width(), r.height()) * 0.43

        # 4 Concentric celestial orbits
        for orb in range(1, 5):
            orad = max_rad * (0.28 + orb * 0.175)
            is_dim = self.orbit_filter not in (0, orb)
            p.setPen(QPen(QColor(212, 175, 55, 25 if is_dim else 85), 1.2, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), orad, orad)

        # Central Prophetic Seal
        seal_glow = QRadialGradient(QPointF(cx, cy), 46)
        seal_glow.setColorAt(0.0, QColor(245, 215, 127, 150))
        seal_glow.setColorAt(1.0, QColor(245, 215, 127, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(seal_glow)
        p.drawEllipse(QPointF(cx, cy), 46, 46)

        p.setPen(QPen(QColor("#f5d77f"), 2.4))
        p.setBrush(QColor("#0c1829"))
        p.drawEllipse(QPointF(cx, cy), 28, 28)
        p.setPen(QColor("#f5d77f"))
        p.setFont(QFont(self.serif_font, 11, QFont.Weight.Bold))
        p.drawText(QRectF(cx - 26, cy - 24, 52, 48), Qt.AlignmentFlag.AlignCenter, "محمد\nﷺ")

        self._nodes = []
        for comp in self.companions:
            orb = int(comp.get("orbit", 1))
            if self.orbit_filter not in (0, orb):
                continue
            orad = max_rad * (0.28 + orb * 0.175)
            ang_deg = float(comp.get("angle", 0)) + self.rot_offset * (0.5 / orb)
            ang = math.radians(ang_deg)
            nx = cx + orad * math.cos(ang)
            ny = cy + orad * math.sin(ang)
            pt = QPointF(nx, ny)
            self._nodes.append((pt, comp))

            is_sel = comp.get("id") == self.active_id
            col = QColor(comp.get("color", "#f5d77f"))

            if is_sel:
                p.setPen(QPen(QColor(245, 215, 127, 130), 1.5))
                p.drawLine(QPointF(cx, cy), pt)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(col.red(), col.green(), col.blue(), 95))
                p.drawEllipse(pt, 18, 18)

            p.setPen(QPen(QColor("#ffffff"), 2.0 if is_sel else 1.2))
            p.setBrush(col)
            p.drawEllipse(pt, 9.0 if is_sel else 6.5, 9.0 if is_sel else 6.5)

            short_name = comp.get("name", "").split(" بن ")[0]
            p.setPen(QColor("#f5d77f") if is_sel else QColor("#dce2ec"))
            p.setFont(QFont(self.ui_font, 8, QFont.Weight.Bold if is_sel else QFont.Weight.Normal))
            p.drawText(QRectF(nx - 55, ny + 9, 110, 20), Qt.AlignmentFlag.AlignCenter, short_name)

        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        for pt, comp in self._nodes:
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 20.0:
                self.companionClicked.emit(comp["id"])
                return

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        for pt, comp in self._nodes:
            if math.hypot(pos.x() - pt.x(), pos.y() - pt.y()) < 16.0:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                QToolTip.showText(
                    ev.globalPosition().toPoint(),
                    f"{comp.get('name', '')} — {comp.get('title', '')}",
                    self,
                )
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ==============================================================================
# 6. PROPHETIC LINEAGE GOLDEN TREE CANVAS
# ==============================================================================
class LineageTreeCanvas(QWidget):
    ancestorClicked = Signal(int)

    def __init__(self, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.serif_font = serif_font
        self.ui_font = ui_font
        self.ancestors = []
        self.active_idx = 0
        self._rects = []
        self.setMinimumSize(400, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_ancestors(self, ancestors: list, active_idx: int = 0):
        self.ancestors = ancestors or []
        self.active_idx = max(0, min(active_idx, max(0, len(self.ancestors) - 1)))
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(6, 6, self.width() - 12, self.height() - 12)
        p.setPen(QPen(QColor("#d4af37"), 1.5))
        p.setBrush(QColor("#081322"))
        p.drawRoundedRect(r, 16, 16)

        if not self.ancestors:
            p.end()
            return

        cx = r.center().x()
        top_pad = r.top() + 34
        bot_pad = r.bottom() - 34
        step = (bot_pad - top_pad) / max(1, len(self.ancestors) - 1)

        # Golden spine trunk
        p.setPen(QPen(QColor("#d4af37"), 3.2))
        p.drawLine(QPointF(cx, top_pad), QPointF(cx, bot_pad))

        self._rects = []
        for idx, anc in enumerate(self.ancestors):
            ny = top_pad + idx * step
            is_cur = idx == self.active_idx
            is_prophet = idx == len(self.ancestors) - 1

            w = 230 if is_prophet else 195
            h = 38 if is_prophet else 32
            box = QRectF(cx - w / 2, ny - h / 2, w, h)
            self._rects.append((box, idx))

            if is_prophet:
                p.setPen(QPen(QColor("#f5d77f"), 2.6))
                p.setBrush(QColor("#9c6f12"))
            elif is_cur:
                p.setPen(QPen(QColor("#2dd4bf"), 2.2))
                p.setBrush(QColor("#18364a"))
            else:
                p.setPen(QPen(QColor("#d4af37"), 1.4))
                p.setBrush(QColor("#112238"))

            p.drawRoundedRect(box, 14, 14)
            p.setPen(QColor("#ffffff") if (is_prophet or is_cur) else QColor("#f5d77f"))
            p.setFont(QFont(self.serif_font, 12 if is_prophet else 11, QFont.Weight.Bold))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, anc.get("name", ""))

            # Companion convergence side badge if present
            conv = anc.get("convergence", "")
            if conv:
                side_x = cx + w / 2 + 14
                if side_x + 145 < r.right():
                    p.setPen(QPen(QColor("#2dd4bf"), 1.1, Qt.PenStyle.DotLine))
                    p.drawLine(QPointF(cx + w / 2, ny), QPointF(side_x, ny))
                    cbox = QRectF(side_x, ny - 12, min(185, r.right() - side_x - 8), 24)
                    p.setPen(QColor("#2dd4bf"))
                    p.setFont(QFont(self.ui_font, 8))
                    p.drawText(cbox, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"✦ {conv[:26]}")

        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        for box, idx in self._rects:
            if box.adjusted(-8, -4, 8, 4).contains(pos):
                self.ancestorClicked.emit(idx)
                return
