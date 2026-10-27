from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .canvases import (
    ArabiaMapCanvas,
    BattleTacticalCanvas,
    HijrahRouteCanvas,
    SanctuaryBlueprintCanvas,
)
from .dialogs import ImageExportPreviewDialog
from .export_studio import render_station_poster


def _make_scrollable(inner_widget: QWidget) -> QScrollArea:
    sc = QScrollArea()
    sc.setWidgetResizable(True)
    sc.setFrameShape(QFrame.Shape.NoFrame)
    sc.setWidget(inner_widget)
    return sc


def _repolish(widget: QWidget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# ==============================================================================
# VIEW 1: CHRONO-SPATIAL ATLAS & WAHI SYNCHRONIZER
# ==============================================================================
class AtlasView(QWidget):
    jumpBattle = Signal(str)
    jumpScenario = Signal(str)

    def __init__(self, repo, state, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.state = state
        self.serif_font = serif_font
        self.ui_font = ui_font

        self.era_filter = "all"
        self.search_text = ""
        self.filtered = list(self.repo.events)
        self.current_idx = 0
        self.depth_mode = "story"

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._auto_next)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        # Toolbar: Era filter pills + instant search
        top_bar = QHBoxLayout()
        self.era_btns = {}
        for key, lbl in [
            ("all", "كل المراحل (18)"),
            ("makki", "العهد المكي"),
            ("hijrah", "مسار الهجرة"),
            ("madani", "العهد المدني"),
        ]:
            b = QPushButton(lbl)
            b.setProperty("btn", "pill")
            b.setProperty("active", "true" if key == "all" else "false")
            b.clicked.connect(lambda _=False, k=key: self._set_era(k))
            self.era_btns[key] = b
            top_bar.addWidget(b)

        top_bar.addStretch(1)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("ابحث عن حدث، غزوة، سورة، أو معلم...")
        self.search_box.setMinimumWidth(260)
        self.search_box.textChanged.connect(self._on_search)
        top_bar.addWidget(self.search_box)
        root.addLayout(top_bar)

        # Main Splitter: Left/Right (RTL: Right=Map, Left=Inspector)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Map Stage Panel
        map_panel = QFrame()
        map_panel.setProperty("panel", "glass")
        mp_lay = QVBoxLayout(map_panel)
        mp_lay.setContentsMargins(12, 12, 12, 12)
        mp_lay.setSpacing(8)

        hud = QHBoxLayout()
        self.era_badge = QLabel("العهد المكي")
        self.era_badge.setProperty("role", "badge")
        hud.addWidget(self.era_badge)
        hud.addStretch(1)
        self.play_btn = QPushButton("▶ تشغيل الرحلة تلقائياً")
        self.play_btn.clicked.connect(self.toggle_autoplay)
        hud.addWidget(self.play_btn)
        mp_lay.addLayout(hud)

        self.map_canvas = ArabiaMapCanvas(serif_font, ui_font)
        self.map_canvas.stationClicked.connect(self.select_index)
        mp_lay.addWidget(self.map_canvas, 1)

        scrub_hdr = QHBoxLayout()
        self.year_lbl = QLabel()
        self.year_lbl.setFont(QFont(serif_font, 14, QFont.Weight.Bold))
        scrub_hdr.addWidget(self.year_lbl)
        scrub_hdr.addStretch(1)

        prev_b = QPushButton("◀ السابق")
        prev_b.clicked.connect(lambda: self.select_index(self.current_idx - 1))
        self.counter_lbl = QLabel("1 / 18")
        next_b = QPushButton("التالي ▶")
        next_b.clicked.connect(lambda: self.select_index(self.current_idx + 1))
        scrub_hdr.addWidget(prev_b)
        scrub_hdr.addWidget(self.counter_lbl)
        scrub_hdr.addWidget(next_b)
        mp_lay.addLayout(scrub_hdr)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, len(self.filtered) - 1))
        self.slider.valueChanged.connect(self._on_slider)
        mp_lay.addWidget(self.slider)

        # Inspector Panel (Scrollable)
        insp_frame = QFrame()
        insp_frame.setProperty("panel", "glass")
        insp_outer = QVBoxLayout(insp_frame)
        insp_outer.setContentsMargins(6, 6, 6, 6)

        insp_inner = QWidget()
        self.insp_lay = QVBoxLayout(insp_inner)
        self.insp_lay.setContentsMargins(12, 12, 12, 12)
        self.insp_lay.setSpacing(12)

        top_info = QHBoxLayout()
        titles_col = QVBoxLayout()
        self.st_meta = QLabel()
        self.st_meta.setProperty("role", "subtitle")
        self.st_title = QLabel()
        self.st_title.setProperty("role", "title")
        self.st_title.setWordWrap(True)
        titles_col.addWidget(self.st_meta)
        titles_col.addWidget(self.st_title)
        top_info.addLayout(titles_col, 1)

        act_col = QHBoxLayout()
        self.bm_btn = QPushButton("🔖 حفظ")
        self.bm_btn.clicked.connect(self._toggle_bookmark)
        self.poster_btn = QPushButton("🖼️ بطاقة ذهبية")
        self.poster_btn.setProperty("btn", "gold")
        self.poster_btn.clicked.connect(self._open_poster)
        act_col.addWidget(self.bm_btn)
        act_col.addWidget(self.poster_btn)
        top_info.addLayout(act_col)
        self.insp_lay.addLayout(top_info)

        # 3 Reading Depth Switcher
        depth_row = QHBoxLayout()
        self.depth_btns = {}
        for dkey, dlbl in [
            ("flash", "⚡ ومضة (30 ث)"),
            ("story", "📖 القصة الكاملة"),
            ("scholarly", "🔍 تحقيق ومصادر"),
        ]:
            db = QPushButton(dlbl)
            db.setProperty("btn", "pill")
            db.setProperty("active", "true" if dkey == "story" else "false")
            db.clicked.connect(lambda _=False, k=dkey: self._set_depth(k))
            self.depth_btns[dkey] = db
            depth_row.addWidget(db)
        self.insp_lay.addLayout(depth_row)

        story_card = QFrame()
        story_card.setProperty("panel", "card")
        sc_lay = QVBoxLayout(story_card)
        self.story_lbl = QLabel()
        self.story_lbl.setWordWrap(True)
        self.story_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        sc_lay.addWidget(self.story_lbl)
        self.insp_lay.addWidget(story_card)

        # Linked Battle / Scenario row
        self.links_row = QHBoxLayout()
        self.btn_link_battle = QPushButton("⚔️ افتح المحاكاة التكتيكية لهذه الغزوة")
        self.btn_link_battle.setProperty("btn", "gold")
        self.btn_link_battle.clicked.connect(self._emit_battle)
        self.btn_link_scen = QPushButton("🧭 عِش مجلس الشورى في هذا الموقف")
        self.btn_link_scen.clicked.connect(self._emit_scenario)
        self.links_row.addWidget(self.btn_link_battle)
        self.links_row.addWidget(self.btn_link_scen)
        self.insp_lay.addLayout(self.links_row)

        # Synced Quranic Wahi Box
        wahi_card = QFrame()
        wahi_card.setProperty("panel", "wahi")
        w_lay = QVBoxLayout(wahi_card)
        self.wahi_surah = QLabel()
        self.wahi_surah.setProperty("role", "teal-badge")
        self.wahi_ayah = QLabel()
        self.wahi_ayah.setProperty("role", "ayah")
        self.wahi_ayah.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wahi_ayah.setWordWrap(True)
        self.wahi_ctx = QLabel()
        self.wahi_ctx.setProperty("role", "subtitle")
        self.wahi_ctx.setWordWrap(True)
        w_lay.addWidget(self.wahi_surah, 0, Qt.AlignmentFlag.AlignRight)
        w_lay.addWidget(self.wahi_ayah)
        w_lay.addWidget(self.wahi_ctx)
        self.insp_lay.addWidget(wahi_card)

        # Past vs Today Box
        tn_card = QFrame()
        tn_card.setProperty("panel", "card")
        tn_lay = QVBoxLayout(tn_card)
        tn_hdr = QLabel("🧭 مقارنة المكان: في العهد النبوي × اليوم")
        tn_hdr.setStyleSheet("font-weight: bold;")
        self.tn_lbl = QLabel()
        self.tn_lbl.setWordWrap(True)
        tn_lay.addWidget(tn_hdr)
        tn_lay.addWidget(self.tn_lbl)
        self.insp_lay.addWidget(tn_card)
        self.insp_lay.addStretch(1)

        insp_outer.addWidget(_make_scrollable(insp_inner))

        splitter.addWidget(map_panel)
        splitter.addWidget(insp_frame)
        splitter.setSizes([580, 520])
        root.addWidget(splitter, 1)

        self.map_canvas.set_events(self.filtered, 0)
        self.select_index(0)

    def stop_autoplay(self):
        if self.auto_timer.isActive():
            self.auto_timer.stop()
            self.play_btn.setText("▶ تشغيل الرحلة تلقائياً")

    def toggle_autoplay(self):
        if self.auto_timer.isActive():
            self.stop_autoplay()
        else:
            self.play_btn.setText("⏸ إيقاف الرحلة التلقائية")
            self.auto_timer.start(3800)

    def _auto_next(self):
        if self.filtered:
            self.select_index((self.current_idx + 1) % len(self.filtered))

    def _set_era(self, era_key: str):
        self.era_filter = era_key
        for k, b in self.era_btns.items():
            b.setProperty("active", "true" if k == era_key else "false")
            _repolish(b)
        self._apply_filters()

    def _on_search(self, txt: str):
        self.search_text = txt.strip()
        self._apply_filters()

    def _apply_filters(self):
        res = []
        for ev in self.repo.events:
            if self.era_filter != "all" and ev.get("era") != self.era_filter:
                continue
            if self.search_text:
                blob = f"{ev['title']} {ev['locationName']} {ev['wahi']['ayah']} {ev['depths']['story']}"
                if self.search_text not in blob:
                    continue
            res.append(ev)
        self.filtered = res or list(self.repo.events)
        self.slider.blockSignals(True)
        self.slider.setMaximum(max(0, len(self.filtered) - 1))
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.map_canvas.set_events(self.filtered, 0)
        self.select_index(0)

    def _on_slider(self, val: int):
        self.select_index(val)

    def _set_depth(self, dkey: str):
        self.depth_mode = dkey
        for k, b in self.depth_btns.items():
            b.setProperty("active", "true" if k == dkey else "false")
            _repolish(b)
        self._render_current()

    def jump_to_event_id(self, event_id: str):
        self._set_era("all")
        self.search_box.clear()
        for i, ev in enumerate(self.filtered):
            if ev["id"] == event_id:
                self.select_index(i)
                return

    def select_index(self, idx: int):
        if not self.filtered:
            return
        self.current_idx = max(0, min(idx, len(self.filtered) - 1))
        self.slider.blockSignals(True)
        self.slider.setValue(self.current_idx)
        self.slider.blockSignals(False)
        self.map_canvas.set_active_index(self.current_idx)
        ev = self.filtered[self.current_idx]
        self.state.add_unique("stations", ev["id"])
        self._render_current()

    def _render_current(self):
        ev = self.filtered[self.current_idx]
        self.era_badge.setText(f"{ev.get('eraLabel', '')} — {ev.get('locationName', '')}")
        self.year_lbl.setText(ev.get("yearLabel", ""))
        self.counter_lbl.setText(f"{self.current_idx + 1} / {len(self.filtered)}")

        self.st_meta.setText(f"{ev.get('yearLabel', '')}  •  📍 {ev.get('locationName', '')}  •  المحطة {ev.get('order', 1)} من 18")
        self.st_title.setText(ev.get("title", ""))

        is_bm = ev["id"] in self.state.data.get("bookmarks", [])
        self.bm_btn.setText("🔖 محفوظة" if is_bm else "🔖 حفظ")

        self.story_lbl.setText(ev.get("depths", {}).get(self.depth_mode, ""))

        self.btn_link_battle.setVisible(bool(ev.get("linkedBattle")))
        self.btn_link_scen.setVisible(bool(ev.get("linkedScenario")))

        wahi = ev.get("wahi", {})
        self.wahi_surah.setText(f"✨ نبض الوحي المتزامن • {wahi.get('surah', '')}")
        self.wahi_ayah.setText(wahi.get("ayah", ""))
        self.wahi_ctx.setText(wahi.get("context", ""))

        tn = ev.get("thenNow", {})
        self.tn_lbl.setText(f"• في العهد النبوي: {tn.get('then', '')}\n• في عصرنا اليوم: {tn.get('now', '')}")

    def _toggle_bookmark(self):
        ev = self.filtered[self.current_idx]
        self.state.toggle_in_list("bookmarks", ev["id"])
        self._render_current()

    def _open_poster(self):
        ev = self.filtered[self.current_idx]
        img = render_station_poster(ev, self.serif_font, self.ui_font)
        dlg = ImageExportPreviewDialog(
            f"🖼️ البطاقة الذهبية — {ev['title']}",
            img,
            f"sirag-poster-{ev['id']}.png",
            self,
        )
        dlg.exec()

    def _emit_battle(self):
        ev = self.filtered[self.current_idx]
        if ev.get("linkedBattle"):
            self.jumpBattle.emit(ev["linkedBattle"])

    def _emit_scenario(self):
        ev = self.filtered[self.current_idx]
        if ev.get("linkedScenario"):
            self.jumpScenario.emit(ev["linkedScenario"])


# ==============================================================================
# VIEW 2: HIJRAH DAY-BY-DAY & SEERAH KNIGHTS QUIZ ARENA
# ==============================================================================
class HijrahQuizView(QWidget):
    def __init__(self, repo, state, ui_font: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.state = state
        self.stops = repo.hijrah_data.get("stops", [])
        self.team = repo.hijrah_data.get("team", [])
        self.quiz = repo.hijrah_data.get("quiz", [])
        self.badges = repo.hijrah_data.get("badges", [])

        self.stop_idx = 0
        self.q_idx = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        sub_row = QHBoxLayout()
        self.btn_mode_h = QPushButton("🐪 مسار الهجرة السري (480 كم)")
        self.btn_mode_q = QPushButton("🏆 ميدان فرسان السيرة (12 تحدياً)")
        for b in (self.btn_mode_h, self.btn_mode_q):
            b.setProperty("btn", "pill")
        self.btn_mode_h.setProperty("active", "true")
        self.btn_mode_h.clicked.connect(lambda: self._switch_sub(0))
        self.btn_mode_q.clicked.connect(lambda: self._switch_sub(1))
        sub_row.addWidget(self.btn_mode_h)
        sub_row.addWidget(self.btn_mode_q)
        sub_row.addStretch(1)
        root.addLayout(sub_row)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_hijrah_page(ui_font))
        self.stack.addWidget(self._build_quiz_page())
        root.addWidget(self.stack, 1)

        self._render_stop()
        self._render_quiz()

    def _switch_sub(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.btn_mode_h.setProperty("active", "true" if idx == 0 else "false")
        self.btn_mode_q.setProperty("active", "true" if idx == 1 else "false")
        _repolish(self.btn_mode_h)
        _repolish(self.btn_mode_q)

    def _build_hijrah_page(self, ui_font: str) -> QWidget:
        sp = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left.setProperty("panel", "glass")
        l_lay = QVBoxLayout(left)
        self.h_canvas = HijrahRouteCanvas(ui_font)
        self.h_canvas.stopClicked.connect(self._set_stop)
        l_lay.addWidget(self.h_canvas, 1)

        ctrl = QHBoxLayout()
        b_prev = QPushButton("◀ اليوم السابق")
        b_prev.clicked.connect(lambda: self._set_stop(self.stop_idx - 1))
        self.h_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_slider.setRange(0, max(0, len(self.stops) - 1))
        self.h_slider.valueChanged.connect(self._set_stop)
        b_next = QPushButton("اليوم التالي ▶")
        b_next.clicked.connect(lambda: self._set_stop(self.stop_idx + 1))
        ctrl.addWidget(b_prev)
        ctrl.addWidget(self.h_slider, 1)
        ctrl.addWidget(b_next)
        l_lay.addLayout(ctrl)

        right = QFrame()
        right.setProperty("panel", "glass")
        r_outer = QVBoxLayout(right)
        r_inner = QWidget()
        r_lay = QVBoxLayout(r_inner)
        self.h_meta = QLabel()
        self.h_meta.setProperty("role", "badge")
        self.h_title = QLabel()
        self.h_title.setProperty("role", "title")
        self.h_title.setWordWrap(True)
        self.h_terrain = QLabel()
        self.h_terrain.setProperty("role", "subtitle")
        self.h_story = QLabel()
        self.h_story.setWordWrap(True)
        r_lay.addWidget(self.h_meta, 0, Qt.AlignmentFlag.AlignRight)
        r_lay.addWidget(self.h_title)
        r_lay.addWidget(self.h_terrain)
        r_lay.addWidget(self.h_story)

        team_hdr = QLabel("🕵️‍♂️ خلية التخطيط السرية في الهجرة النبوية:")
        team_hdr.setStyleSheet("font-weight: bold; margin-top: 8px;")
        r_lay.addWidget(team_hdr)

        grid = QGridLayout()
        for i, member in enumerate(self.team):
            mc = QFrame()
            mc.setProperty("panel", "card")
            ml = QVBoxLayout(mc)
            n = QLabel(f"✦ {member['name']} — ({member['role']})")
            n.setStyleSheet("font-weight: bold;")
            d = QLabel(member["detail"])
            d.setProperty("role", "subtitle")
            d.setWordWrap(True)
            ml.addWidget(n)
            ml.addWidget(d)
            grid.addWidget(mc, i // 2, i % 2)
        r_lay.addLayout(grid)
        r_lay.addStretch(1)
        r_outer.addWidget(_make_scrollable(r_inner))

        sp.addWidget(left)
        sp.addWidget(right)
        sp.setSizes([520, 560])
        return sp

    def _set_stop(self, idx: int):
        if not self.stops:
            return
        self.stop_idx = max(0, min(idx, len(self.stops) - 1))
        self.h_slider.blockSignals(True)
        self.h_slider.setValue(self.stop_idx)
        self.h_slider.blockSignals(False)
        self._render_stop()

    def _render_stop(self):
        if not self.stops:
            return
        st = self.stops[self.stop_idx]
        self.h_canvas.set_data(self.stops, self.stop_idx)
        self.h_meta.setText(f"{st['dayLabel']}  •  {st['km']} كم من مكة")
        self.h_title.setText(st["title"])
        self.h_terrain.setText(f"⛰️ التضاريس: {st['terrain']}")
        self.h_story.setText(st["story"])

    def _build_quiz_page(self) -> QWidget:
        sp = QSplitter(Qt.Orientation.Horizontal)

        q_panel = QFrame()
        q_panel.setProperty("panel", "glass")
        ql = QVBoxLayout(q_panel)
        ql.setContentsMargins(18, 18, 18, 18)
        ql.setSpacing(12)

        self.q_lvl = QLabel()
        self.q_lvl.setProperty("role", "badge")
        self.q_text = QLabel()
        self.q_text.setProperty("role", "title")
        self.q_text.setWordWrap(True)
        ql.addWidget(self.q_lvl, 0, Qt.AlignmentFlag.AlignRight)
        ql.addWidget(self.q_text)

        self.opt_btns = []
        for i in range(4):
            ob = QPushButton()
            ob.clicked.connect(lambda _=False, oi=i: self._answer_quiz(oi))
            self.opt_btns.append(ob)
            ql.addWidget(ob)

        self.q_feedback = QLabel()
        self.q_feedback.setWordWrap(True)
        ql.addWidget(self.q_feedback)
        ql.addStretch(1)

        nav = QHBoxLayout()
        bp = QPushButton("◀ السؤال السابق")
        bp.clicked.connect(lambda: self._go_q(self.q_idx - 1))
        bn = QPushButton("السؤال التالي ▶")
        bn.setProperty("btn", "gold")
        bn.clicked.connect(lambda: self._go_q(self.q_idx + 1))
        nav.addWidget(bp)
        nav.addWidget(bn)
        ql.addLayout(nav)

        m_panel = QFrame()
        m_panel.setProperty("panel", "glass")
        ml = QVBoxLayout(m_panel)
        ml.setContentsMargins(18, 18, 18, 18)
        self.m_score_lbl = QLabel()
        self.m_score_lbl.setProperty("role", "title")
        ml.addWidget(self.m_score_lbl)

        self.badge_labels = []
        for b in self.badges:
            bc = QFrame()
            bc.setProperty("panel", "card")
            bl = QVBoxLayout(bc)
            lbl = QLabel()
            lbl.setWordWrap(True)
            self.badge_labels.append((b, lbl))
            bl.addWidget(lbl)
            ml.addWidget(bc)
        ml.addStretch(1)

        sp.addWidget(q_panel)
        sp.addWidget(m_panel)
        sp.setSizes([620, 440])
        return sp

    def _go_q(self, idx: int):
        if not self.quiz:
            return
        self.q_idx = idx % len(self.quiz)
        self.q_feedback.clear()
        self._render_quiz()

    def _render_quiz(self):
        if not self.quiz:
            return
        q = self.quiz[self.q_idx]
        self.q_lvl.setText(f"التحدي {self.q_idx + 1} من {len(self.quiz)}  •  المستوى: {q.get('level', '')}")
        self.q_text.setText(q["question"])
        opts = q.get("options", [])
        for i, btn in enumerate(self.opt_btns):
            if i < len(opts):
                btn.setText(opts[i])
                btn.show()
            else:
                btn.hide()

        solved = len(self.state.data.get("quiz_solved", []))
        self.m_score_lbl.setText(f"🏅 رصيدك: {solved} من {len(self.quiz)} تحدياً")
        for b, lbl in self.badge_labels:
            unlocked = solved >= b["threshold"]
            status = "🔓 وسام مفتوح!" if unlocked else f"🔒 يفتح عند {b['threshold']} إجابات"
            lbl.setText(f"{b['icon']} {b['title']} — {status}\n{b['desc']}")

    def _answer_quiz(self, chosen_idx: int):
        q = self.quiz[self.q_idx]
        correct = chosen_idx == q.get("correctIndex", 0)
        if correct:
            self.state.add_unique("quiz_solved", q["id"])
            self.q_feedback.setText(f"✅ إجابة صحيحة أحسنت!\n📚 {q.get('explanation', '')}")
        else:
            right_txt = q["options"][q["correctIndex"]]
            self.q_feedback.setText(f"💡 الإجابة الأدق هي: «{right_txt}»\n📚 {q.get('explanation', '')}")
        self._render_quiz()


# ==============================================================================
# VIEW 3: TACTICAL BATTLE SIMULATOR
# ==============================================================================
class BattlesView(QWidget):
    def __init__(self, repo, state, ui_font: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.state = state
        self.battles = repo.battles
        self.b_idx = 0
        self.p_idx = 0

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._next_phase_auto)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        bar = QHBoxLayout()
        self.b_btns = []
        for i, b in enumerate(self.battles):
            btn = QPushButton(f"⚔️ {b['title']}")
            btn.setProperty("btn", "pill")
            btn.clicked.connect(lambda _=False, bi=i: self.select_battle_index(bi))
            self.b_btns.append(btn)
            bar.addWidget(btn)
        bar.addStretch(1)
        root.addLayout(bar)

        sp = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left.setProperty("panel", "glass")
        ll = QVBoxLayout(left)
        self.canvas = BattleTacticalCanvas(ui_font)
        ll.addWidget(self.canvas, 1)

        ctrl = QHBoxLayout()
        self.btn_play = QPushButton("▶ تشغيل التحريك التكتيكي")
        self.btn_play.setProperty("btn", "gold")
        self.btn_play.clicked.connect(self._toggle_play)
        bp = QPushButton("◀ المرحلة السابقة")
        bp.clicked.connect(lambda: self.set_phase(self.p_idx - 1))
        bn = QPushButton("المرحلة التالية ▶")
        bn.clicked.connect(lambda: self.set_phase(self.p_idx + 1))
        ctrl.addWidget(self.btn_play)
        ctrl.addWidget(bp)
        ctrl.addWidget(bn)
        ll.addLayout(ctrl)

        right = QFrame()
        right.setProperty("panel", "glass")
        r_out = QVBoxLayout(right)
        r_in = QWidget()
        rl = QVBoxLayout(r_in)
        self.b_date = QLabel()
        self.b_date.setProperty("role", "badge")
        self.b_title = QLabel()
        self.b_title.setProperty("role", "title")
        self.b_title.setWordWrap(True)
        self.b_forces = QLabel()
        self.b_forces.setProperty("role", "subtitle")
        self.b_forces.setWordWrap(True)

        p_card = QFrame()
        p_card.setProperty("panel", "card")
        pl = QVBoxLayout(p_card)
        self.p_head = QLabel()
        self.p_head.setStyleSheet("font-weight: bold;")
        self.p_head.setWordWrap(True)
        self.p_analysis = QLabel()
        self.p_analysis.setWordWrap(True)
        pl.addWidget(self.p_head)
        pl.addWidget(self.p_analysis)

        l_card = QFrame()
        l_card.setProperty("panel", "wahi")
        ll2 = QVBoxLayout(l_card)
        self.p_lesson = QLabel()
        self.p_lesson.setWordWrap(True)
        ll2.addWidget(self.p_lesson)

        rl.addWidget(self.b_date, 0, Qt.AlignmentFlag.AlignRight)
        rl.addWidget(self.b_title)
        rl.addWidget(self.b_forces)
        rl.addWidget(p_card)
        rl.addWidget(l_card)
        rl.addStretch(1)
        r_out.addWidget(_make_scrollable(r_in))

        sp.addWidget(left)
        sp.addWidget(right)
        sp.setSizes([600, 480])
        root.addWidget(sp, 1)

        self.select_battle_index(0)

    def stop_play(self):
        if self.play_timer.isActive():
            self.play_timer.stop()
            self.btn_play.setText("▶ تشغيل التحريك التكتيكي")

    def _toggle_play(self):
        if self.play_timer.isActive():
            self.stop_play()
        else:
            self.btn_play.setText("⏸ إيقاف التحريك")
            self.play_timer.start(3000)

    def _next_phase_auto(self):
        phases = self.battles[self.b_idx].get("phases", [])
        if phases:
            self.set_phase((self.p_idx + 1) % len(phases))

    def select_battle_by_id(self, battle_id: str):
        for i, b in enumerate(self.battles):
            if b["id"] == battle_id:
                self.select_battle_index(i)
                return

    def select_battle_index(self, idx: int):
        self.stop_play()
        self.b_idx = max(0, min(idx, len(self.battles) - 1))
        for i, btn in enumerate(self.b_btns):
            btn.setProperty("active", "true" if i == self.b_idx else "false")
            _repolish(btn)
        b = self.battles[self.b_idx]
        self.state.add_unique("battles", b["id"])
        self.p_idx = 0
        self.canvas.set_battle_phase(b, 0, instant=True)
        self._render_info()

    def set_phase(self, pidx: int):
        b = self.battles[self.b_idx]
        phases = b.get("phases", [])
        if not phases:
            return
        self.p_idx = pidx % len(phases)
        self.canvas.set_battle_phase(b, self.p_idx, instant=False)
        self._render_info()

    def _render_info(self):
        b = self.battles[self.b_idx]
        phases = b.get("phases", [])
        ph = phases[self.p_idx]
        self.b_date.setText(f"{b['date']}  •  المرحلة {self.p_idx + 1} من {len(phases)}: {ph['name']}")
        self.b_title.setText(b["title"])
        self.b_forces.setText(
            f"🛡️ جيش المسلمين: {b['muslimForce']}   |   ⚔️ جيش الخصم: {b['enemyForce']}\n⛰️ الميدان: {b['terrainSummary']}"
        )
        self.p_head.setText(f"📍 {ph['headline']}")
        self.p_analysis.setText(ph["analysis"])
        self.p_lesson.setText(f"💎 الدرس القيادي والنبوي:\n{ph['lesson']}")


# ==============================================================================
# VIEW 4: SACRED SANCTUARIES BLUEPRINTS
# ==============================================================================
class SanctuariesView(QWidget):
    def __init__(self, repo, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.data = repo.sanctuaries
        self.site_key = "madinah"
        self.hs_idx = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.btn_mad = QPushButton("🕌 المسجد النبوي الشريف والروضة")
        self.btn_mak = QPushButton("🕋 الكعبة المشرفة والمسجد الحرام")
        for b in (self.btn_mad, self.btn_mak):
            b.setProperty("btn", "pill")
        self.btn_mad.clicked.connect(lambda: self._set_site("madinah"))
        self.btn_mak.clicked.connect(lambda: self._set_site("makkah"))
        top.addWidget(self.btn_mad)
        top.addWidget(self.btn_mak)
        top.addStretch(1)
        root.addLayout(top)

        sp = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left.setProperty("panel", "glass")
        ll = QVBoxLayout(left)
        self.canvas = SanctuaryBlueprintCanvas(serif_font, ui_font)
        self.canvas.hotspotClicked.connect(self._set_hotspot)
        ll.addWidget(self.canvas, 1)

        self.hs_strip = QHBoxLayout()
        ll.addLayout(self.hs_strip)

        right = QFrame()
        right.setProperty("panel", "glass")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(18, 18, 18, 18)
        rl.setSpacing(12)
        self.s_badge = QLabel()
        self.s_badge.setProperty("role", "badge")
        self.s_name = QLabel()
        self.s_name.setProperty("role", "title")
        self.s_name.setWordWrap(True)
        self.s_dim = QLabel()
        self.s_dim.setProperty("role", "subtitle")
        self.s_dim.setWordWrap(True)

        h_box = QFrame()
        h_box.setProperty("panel", "wahi")
        hl = QVBoxLayout(h_box)
        self.s_hadith = QLabel()
        self.s_hadith.setWordWrap(True)
        hl.addWidget(self.s_hadith)

        self.s_story = QLabel()
        self.s_story.setWordWrap(True)

        rl.addWidget(self.s_badge, 0, Qt.AlignmentFlag.AlignRight)
        rl.addWidget(self.s_name)
        rl.addWidget(self.s_dim)
        rl.addWidget(h_box)
        rl.addWidget(self.s_story)
        rl.addStretch(1)

        sp.addWidget(left)
        sp.addWidget(right)
        sp.setSizes([580, 500])
        root.addWidget(sp, 1)

        self._set_site("madinah")

    def _set_site(self, key: str):
        self.site_key = key
        self.hs_idx = 0
        self.btn_mad.setProperty("active", "true" if key == "madinah" else "false")
        self.btn_mak.setProperty("active", "true" if key == "makkah" else "false")
        _repolish(self.btn_mad)
        _repolish(self.btn_mak)

        while self.hs_strip.count():
            it = self.hs_strip.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        hotspots = self.data[key]["hotspots"]
        for i, hs in enumerate(hotspots):
            b = QPushButton(hs["name"].split(" ")[0] + " " + (hs["name"].split(" ")[1] if len(hs["name"].split(" ")) > 1 else ""))
            b.clicked.connect(lambda _=False, idx=i: self._set_hotspot(idx))
            self.hs_strip.addWidget(b)

        self._set_hotspot(0)

    def _set_hotspot(self, idx: int):
        hotspots = self.data[self.site_key]["hotspots"]
        self.hs_idx = max(0, min(idx, len(hotspots) - 1))
        hs = hotspots[self.hs_idx]
        self.canvas.set_site(self.site_key, hotspots, self.hs_idx)
        self.s_badge.setText(hs.get("badge", ""))
        self.s_name.setText(hs.get("name", ""))
        self.s_dim.setText(f"📐 الأبعاد والمعالم: {hs.get('dimensions', '')}")
        self.s_hadith.setText(f"📜 النص النبوي الموثق:\n{hs.get('hadith', '')}")
        self.s_story.setText(hs.get("story", ""))


# ==============================================================================
# VIEW 5: IF YOU WERE THERE (SHURA SCENARIOS)
# ==============================================================================
class ScenariosView(QWidget):
    def __init__(self, repo, state, parent=None):
        super().__init__(parent)
        self.scenarios = repo.scenarios
        self.state = state
        self.cur_idx = 0

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(14)

        side = QFrame()
        side.setProperty("panel", "glass")
        side.setMaximumWidth(310)
        sl = QVBoxLayout(side)
        sl.addWidget(QLabel("🧭 مواقف الشورى الكبرى:"))
        self.s_btns = []
        for i, sc in enumerate(self.scenarios):
            b = QPushButton(f"{i + 1}. {sc['title']}")
            b.setProperty("btn", "pill")
            b.clicked.connect(lambda _=False, idx=i: self.select_scenario_index(idx))
            self.s_btns.append(b)
            sl.addWidget(b)
        sl.addStretch(1)

        stage = QFrame()
        stage.setProperty("panel", "glass")
        st_out = QVBoxLayout(stage)
        st_in = QWidget()
        stl = QVBoxLayout(st_in)
        stl.setContentsMargins(18, 18, 18, 18)
        stl.setSpacing(12)

        self.sc_era = QLabel()
        self.sc_era.setProperty("role", "badge")
        self.sc_title = QLabel()
        self.sc_title.setProperty("role", "title")
        self.sc_title.setWordWrap(True)
        self.sc_sit = QLabel()
        self.sc_sit.setWordWrap(True)
        self.sc_q = QLabel()
        self.sc_q.setStyleSheet("font-weight: bold;")
        self.sc_q.setWordWrap(True)

        stl.addWidget(self.sc_era, 0, Qt.AlignmentFlag.AlignRight)
        stl.addWidget(self.sc_title)
        stl.addWidget(self.sc_sit)
        stl.addWidget(self.sc_q)

        self.choice_box = QVBoxLayout()
        stl.addLayout(self.choice_box)

        self.outcome_frame = QFrame()
        self.outcome_frame.setProperty("panel", "wahi")
        ol = QVBoxLayout(self.outcome_frame)
        self.out_lbl = QLabel()
        self.out_lbl.setWordWrap(True)
        ol.addWidget(self.out_lbl)
        stl.addWidget(self.outcome_frame)
        stl.addStretch(1)

        st_out.addWidget(_make_scrollable(st_in))

        root.addWidget(side)
        root.addWidget(stage, 1)

        self.select_scenario_index(0)

    def select_scenario_by_id(self, sc_id: str):
        for i, sc in enumerate(self.scenarios):
            if sc["id"] == sc_id:
                self.select_scenario_index(i)
                return

    def select_scenario_index(self, idx: int):
        self.cur_idx = max(0, min(idx, len(self.scenarios) - 1))
        for i, b in enumerate(self.s_btns):
            b.setProperty("active", "true" if i == self.cur_idx else "false")
            _repolish(b)
        sc = self.scenarios[self.cur_idx]
        self.sc_era.setText(sc.get("era", ""))
        self.sc_title.setText(sc.get("title", ""))
        self.sc_sit.setText(sc.get("situation", ""))
        self.sc_q.setText(f"❓ {sc.get('question', '')}")
        self.outcome_frame.hide()

        while self.choice_box.count():
            it = self.choice_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        for ch in sc.get("choices", []):
            cb = QPushButton(f"• {ch['text']}")
            cb.clicked.connect(lambda _=False, c=ch: self._pick_choice(c))
            self.choice_box.addWidget(cb)

    def _pick_choice(self, ch: dict):
        sc = self.scenarios[self.cur_idx]
        self.state.add_unique("scenarios", sc["id"])
        prefix = "🌟 اختيار يوافق البصيرة والشورى النبوية!" if ch.get("isPropheticMatch") else "💡 تأمّل هذا البُعد:"
        self.out_lbl.setText(
            f"{prefix}\n{ch.get('feedback', '')}\n\n"
            f"✨ القرار النبوي التاريخي:\n{sc.get('propheticOutcome', '')}\n\n"
            f"🌱 الأثر القيادي والنفسي في حياتك اليوم:\n{sc.get('lifeLesson', '')}"
        )
        self.outcome_frame.show()
