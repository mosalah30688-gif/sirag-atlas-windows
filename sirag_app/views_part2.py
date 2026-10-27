from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .canvases import ConstellationCanvas, LineageTreeCanvas
from .dialogs import ImageExportPreviewDialog, RelicManuscriptDialog
from .export_studio import render_khatmah_certificate
from .state import gregorian_to_hijri
from .views_part1 import _make_scrollable, _repolish


# ==============================================================================
# VIEW 6: COMPANIONS CONSTELLATION
# ==============================================================================
class ConstellationView(QWidget):
    jumpEvent = Signal(str)

    def __init__(self, repo, state, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.state = state
        self.companions = repo.companions
        self.orbit_filter = 0
        self.active_id = self.companions[0]["id"] if self.companions else ""

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        bar = QHBoxLayout()
        self.orb_btns = {}
        for okey, olbl in [
            (0, "كل المدارات (16)"),
            (1, "السابقون والخلفاء"),
            (2, "القادة والفرسان"),
            (3, "السفراء والعلماء"),
            (4, "أمهات المؤمنين والصحابيات"),
        ]:
            b = QPushButton(olbl)
            b.setProperty("btn", "pill")
            b.clicked.connect(lambda _=False, k=okey: self._set_orbit(k))
            self.orb_btns[okey] = b
            bar.addWidget(b)
        bar.addStretch(1)
        root.addLayout(bar)

        sp = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left.setProperty("panel", "glass")
        ll = QVBoxLayout(left)
        self.canvas = ConstellationCanvas(serif_font, ui_font)
        self.canvas.companionClicked.connect(self.select_companion)
        ll.addWidget(self.canvas, 1)

        right = QFrame()
        right.setProperty("panel", "glass")
        r_out = QVBoxLayout(right)
        r_in = QWidget()
        rl = QVBoxLayout(r_in)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        self.c_role = QLabel()
        self.c_role.setProperty("role", "badge")
        self.c_name = QLabel()
        self.c_name.setProperty("role", "title")
        self.c_name.setWordWrap(True)
        self.c_title = QLabel()
        self.c_title.setProperty("role", "subtitle")
        self.c_bio = QLabel()
        self.c_bio.setWordWrap(True)

        q_card = QFrame()
        q_card.setProperty("panel", "wahi")
        ql = QVBoxLayout(q_card)
        self.c_quote = QLabel()
        self.c_quote.setFont(QFont(serif_font, 15))
        self.c_quote.setWordWrap(True)
        ql.addWidget(self.c_quote)

        rl.addWidget(self.c_role, 0, Qt.AlignmentFlag.AlignRight)
        rl.addWidget(self.c_name)
        rl.addWidget(self.c_title)
        rl.addWidget(self.c_bio)
        rl.addWidget(q_card)
        rl.addWidget(QLabel("🗺️ المحطات المرتبطة في الأطلس:"))
        self.st_box = QVBoxLayout()
        rl.addLayout(self.st_box)
        rl.addStretch(1)

        r_out.addWidget(_make_scrollable(r_in))
        sp.addWidget(left)
        sp.addWidget(right)
        sp.setSizes([580, 500])
        root.addWidget(sp, 1)

        self._set_orbit(0)

    def _set_orbit(self, orb: int):
        self.orbit_filter = orb
        for k, b in self.orb_btns.items():
            b.setProperty("active", "true" if k == orb else "false")
            _repolish(b)
        visible = [c for c in self.companions if orb == 0 or c.get("orbit") == orb]
        if visible and all(c["id"] != self.active_id for c in visible):
            self.active_id = visible[0]["id"]
        self.select_companion(self.active_id)

    def select_companion(self, comp_id: str):
        comp = next((c for c in self.companions if c["id"] == comp_id), None)
        if not comp:
            return
        self.active_id = comp_id
        self.state.add_unique("companions", comp_id)
        self.canvas.set_state(self.companions, self.active_id, self.orbit_filter)

        self.c_role.setText(f"🌟 {comp.get('signatureRole', '')}  •  إسلامه/ها: {comp.get('ageAtIslam', '')}")
        self.c_name.setText(comp.get("name", ""))
        self.c_title.setText(f"اللقب النبوي: {comp.get('title', '')}")
        self.c_bio.setText(comp.get("bio", ""))
        self.c_quote.setText(f"«{comp.get('quote', '')}»")

        while self.st_box.count():
            it = self.st_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        ev_map = {e["id"]: e["title"] for e in self.repo.events}
        for sid in comp.get("stations", []):
            if sid in ev_map:
                b = QPushButton(f"📍 انتقل إلى: {ev_map[sid]}")
                b.clicked.connect(lambda _=False, eid=sid: self.jumpEvent.emit(eid))
                self.st_box.addWidget(b)


# ==============================================================================
# VIEW 7: PROPHETIC LINEAGE, HOUSEHOLD & DAILY SHAMA'IL
# ==============================================================================
class LineageShamailView(QWidget):
    def __init__(self, repo, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.data = repo.lineage
        self.ancestors = self.data.get("ancestors", [])
        self.anc_idx = len(self.ancestors) - 1

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        tabs = QHBoxLayout()
        self.t_btns = []
        for i, lbl in enumerate([
            "🌿 عمود النسب المطهّر",
            "🏡 أبناء وبنات النبي ﷺ",
            "🕰️ يوم في حياته ﷺ (الشمائل)",
        ]):
            b = QPushButton(lbl)
            b.setProperty("btn", "pill")
            b.clicked.connect(lambda _=False, idx=i: self._set_tab(idx))
            self.t_btns.append(b)
            tabs.addWidget(b)
        tabs.addStretch(1)
        root.addLayout(tabs)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_tree_tab(serif_font, ui_font))
        self.stack.addWidget(self._build_children_tab())
        self.stack.addWidget(self._build_shamail_tab())
        root.addWidget(self.stack, 1)

        self._set_tab(0)

    def _set_tab(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.t_btns):
            b.setProperty("active", "true" if i == idx else "false")
            _repolish(b)

    def _build_tree_tab(self, serif_font: str, ui_font: str) -> QWidget:
        sp = QSplitter(Qt.Orientation.Horizontal)
        left = QFrame()
        left.setProperty("panel", "glass")
        ll = QVBoxLayout(left)
        self.tree_canvas = LineageTreeCanvas(serif_font, ui_font)
        self.tree_canvas.ancestorClicked.connect(self._select_anc)
        ll.addWidget(_make_scrollable(self.tree_canvas))

        right = QFrame()
        right.setProperty("panel", "glass")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(18, 18, 18, 18)
        rl.setSpacing(12)
        self.a_era = QLabel()
        self.a_era.setProperty("role", "badge")
        self.a_name = QLabel()
        self.a_name.setProperty("role", "title")
        self.a_conv = QLabel()
        self.a_conv.setProperty("role", "teal-badge")
        self.a_conv.setWordWrap(True)
        self.a_story = QLabel()
        self.a_story.setWordWrap(True)
        rl.addWidget(self.a_era, 0, Qt.AlignmentFlag.AlignRight)
        rl.addWidget(self.a_name)
        rl.addWidget(self.a_conv)
        rl.addWidget(self.a_story)
        rl.addStretch(1)

        sp.addWidget(left)
        sp.addWidget(right)
        sp.setSizes([580, 480])
        self._select_anc(self.anc_idx)
        return sp

    def _select_anc(self, idx: int):
        if not self.ancestors:
            return
        self.anc_idx = max(0, min(idx, len(self.ancestors) - 1))
        self.tree_canvas.set_ancestors(self.ancestors, self.anc_idx)
        anc = self.ancestors[self.anc_idx]
        self.a_era.setText(anc.get("era", ""))
        self.a_name.setText(anc.get("name", ""))
        conv = anc.get("convergence", "")
        self.a_conv.setText(f"🤝 التقاء النسب: {conv}" if conv else "🌟 عمود النسب النبوي الشريف")
        self.a_story.setText(anc.get("story", ""))

    def _build_children_tab(self) -> QWidget:
        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setSpacing(12)
        for i, ch in enumerate(self.data.get("children", [])):
            card = QFrame()
            card.setProperty("panel", "glass")
            cl = QVBoxLayout(card)
            nm = QLabel(f"🌿 {ch['name']}")
            nm.setProperty("role", "title")
            mo = QLabel(f"الأم الكريمة: {ch['mother']}")
            mo.setProperty("role", "teal-badge")
            nt = QLabel(ch["note"])
            nt.setWordWrap(True)
            cl.addWidget(nm)
            cl.addWidget(mo, 0, Qt.AlignmentFlag.AlignRight)
            cl.addWidget(nt)
            grid.addWidget(card, i // 2, i % 2)
        return _make_scrollable(inner)

    def _build_shamail_tab(self) -> QWidget:
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(12)
        for hr in self.data.get("dailyHours", []):
            card = QFrame()
            card.setProperty("panel", "glass")
            cl = QVBoxLayout(card)
            top = QLabel(f"{hr.get('icon', '🕰️')} {hr['period']} ({hr['timeLabel']}) — {hr['title']}")
            top.setProperty("role", "title")
            top.setWordWrap(True)
            sm = QLabel(hr["summary"])
            sm.setWordWrap(True)
            cl.addWidget(top)
            cl.addWidget(sm)
            lay.addWidget(card)
        lay.addStretch(1)
        return _make_scrollable(inner)


# ==============================================================================
# VIEW 8: SPOKEN SAHABA DIWAN (OFFLINE MP3) & SEERAH LEXICON
# ==============================================================================
class DiwanLexiconView(QWidget):
    jumpEvent = Signal(str)

    def __init__(self, repo, audio_engine, serif_font: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.audio = audio_engine
        self.serif_font = serif_font
        self.poems = repo.diwan_lexicon.get("poems", [])
        self.lexicon = repo.diwan_lexicon.get("lexicon", [])
        self.p_idx = 0
        self.speed = 1.0
        self.verse_frames = []

        self.audio.poem_progress.connect(self._on_audio_progress)
        self.audio.poem_state.connect(self._on_audio_state)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        tabs = QHBoxLayout()
        self.b_diwan = QPushButton("🎙️ ديوان القصائد الصحابية المسموع (بدون موسيقى)")
        self.b_lex = QPushButton("📖 معجم الأماكن وغريب السيرة (18)")
        for b in (self.b_diwan, self.b_lex):
            b.setProperty("btn", "pill")
        self.b_diwan.clicked.connect(lambda: self._set_sub(0))
        self.b_lex.clicked.connect(lambda: self._set_sub(1))
        tabs.addWidget(self.b_diwan)
        tabs.addWidget(self.b_lex)
        tabs.addStretch(1)
        root.addLayout(tabs)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_diwan_page())
        self.stack.addWidget(self._build_lexicon_page())
        root.addWidget(self.stack, 1)

        self._set_sub(0)
        self.select_poem_index(0)

    def _set_sub(self, idx: int):
        if idx != 0:
            self.audio.stop_poem()
        self.stack.setCurrentIndex(idx)
        self.b_diwan.setProperty("active", "true" if idx == 0 else "false")
        self.b_lex.setProperty("active", "true" if idx == 1 else "false")
        _repolish(self.b_diwan)
        _repolish(self.b_lex)

    def select_poem_by_id(self, poem_id: str):
        self._set_sub(0)
        for i, p in enumerate(self.poems):
            if p["id"] == poem_id:
                self.select_poem_index(i)
                return

    def open_lexicon_term(self, term: str):
        self._set_sub(1)
        self.lex_search.setText(term)

    def _build_diwan_page(self) -> QWidget:
        sp = QSplitter(Qt.Orientation.Horizontal)

        side = QFrame()
        side.setProperty("panel", "glass")
        side.setMaximumWidth(310)
        sl = QVBoxLayout(side)
        sl.addWidget(QLabel("🎙️ القصائد النبوية الموثقة:"))
        self.p_btns = []
        for i, pm in enumerate(self.poems):
            b = QPushButton(f"🎙️ {pm['title']}\n({pm['poet']})")
            b.setProperty("btn", "pill")
            b.clicked.connect(lambda _=False, idx=i: self.select_poem_index(idx))
            self.p_btns.append(b)
            sl.addWidget(b)
        sl.addStretch(1)

        stage = QFrame()
        stage.setProperty("panel", "glass")
        st_out = QVBoxLayout(stage)
        st_in = QWidget()
        stl = QVBoxLayout(st_in)
        stl.setContentsMargins(18, 16, 18, 16)
        stl.setSpacing(12)

        self.pm_poet = QLabel()
        self.pm_poet.setProperty("role", "badge")
        self.pm_title = QLabel()
        self.pm_title.setProperty("role", "title")
        stl.addWidget(self.pm_poet, 0, Qt.AlignmentFlag.AlignRight)
        stl.addWidget(self.pm_title)

        # Native Audio Player Controls
        player_box = QFrame()
        player_box.setProperty("panel", "card")
        pl = QVBoxLayout(player_box)
        prow = QHBoxLayout()
        self.play_btn = QPushButton("▶ استمع للإلقاء العربي الفصيح")
        self.play_btn.setProperty("btn", "gold")
        self.play_btn.clicked.connect(self._toggle_play)
        self.time_lbl = QLabel("00:00 / 00:00")
        self.speed_btn = QPushButton("السرعة: 1.0x")
        self.speed_btn.clicked.connect(self._cycle_speed)
        prow.addWidget(self.play_btn)
        prow.addStretch(1)
        prow.addWidget(self.time_lbl)
        prow.addWidget(self.speed_btn)
        pl.addLayout(prow)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(lambda v: self.audio.seek_poem_ratio(v / 1000.0))
        pl.addWidget(self.seek_slider)
        stl.addWidget(player_box)

        self.verses_lay = QVBoxLayout()
        stl.addLayout(self.verses_lay)

        occ_card = QFrame()
        occ_card.setProperty("panel", "wahi")
        ol = QVBoxLayout(occ_card)
        self.pm_occ = QLabel()
        self.pm_occ.setWordWrap(True)
        ol.addWidget(self.pm_occ)
        stl.addWidget(occ_card)

        self.pm_vocab = QLabel()
        self.pm_vocab.setProperty("role", "subtitle")
        self.pm_vocab.setWordWrap(True)
        stl.addWidget(self.pm_vocab)
        stl.addStretch(1)

        st_out.addWidget(_make_scrollable(st_in))
        sp.addWidget(side)
        sp.addWidget(stage)
        sp.setSizes([300, 760])
        return sp

    def select_poem_index(self, idx: int):
        self.audio.stop_poem()
        self.p_idx = max(0, min(idx, len(self.poems) - 1))
        for i, b in enumerate(self.p_btns):
            b.setProperty("active", "true" if i == self.p_idx else "false")
            _repolish(b)
        pm = self.poems[self.p_idx]
        self.pm_poet.setText(pm.get("poet", ""))
        self.pm_title.setText(pm.get("title", ""))
        self.pm_occ.setText(f"📚 المناسبة: {pm.get('occasion', '')}\nالمصدر: {pm.get('source', '')}")
        self.pm_vocab.setText(f"💡 إضاءة بلاغية ولغوية: {pm.get('vocabNote', '')}")
        self.seek_slider.setValue(0)
        self.time_lbl.setText("00:00 / 00:00")

        while self.verses_lay.count():
            it = self.verses_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.verse_frames = []

        for v in pm.get("verses", []):
            vf = QFrame()
            vf.setProperty("panel", "card")
            vl = QHBoxLayout(vf)
            sadr = QLabel(v["sadr"])
            sadr.setFont(QFont(self.serif_font, 16))
            sadr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            star = QLabel("✦")
            ajuz = QLabel(v["ajuz"])
            ajuz.setFont(QFont(self.serif_font, 16))
            ajuz.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl.addWidget(sadr, 1)
            vl.addWidget(star)
            vl.addWidget(ajuz, 1)
            self.verses_lay.addWidget(vf)
            self.verse_frames.append(vf)

    def _toggle_play(self):
        pm = self.poems[self.p_idx]
        self.audio.toggle_poem(pm.get("audioSrc", ""), self.speed)

    def _cycle_speed(self):
        speeds = [0.85, 1.0, 1.15]
        self.speed = speeds[(speeds.index(self.speed) + 1) % len(speeds)] if self.speed in speeds else 1.0
        self.speed_btn.setText(f"السرعة: {self.speed}x")
        self.audio.set_poem_speed(self.speed)

    def _on_audio_state(self, playing: bool):
        self.play_btn.setText("⏸ إيقاف مؤقت للإلقاء" if playing else "▶ استمع للإلقاء العربي الفصيح")

    def _on_audio_progress(self, pos_ms: int, dur_ms: int):
        if dur_ms > 0:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int(pos_ms * 1000 / dur_ms))
            self.seek_slider.blockSignals(False)
            ps, ds = pos_ms // 1000, dur_ms // 1000
            self.time_lbl.setText(f"{ps // 60:02d}:{ps % 60:02d} / {ds // 60:02d}:{ds % 60:02d}")
            if self.verse_frames:
                active_v = min(len(self.verse_frames) - 1, int((pos_ms / dur_ms) * len(self.verse_frames)))
                for i, vf in enumerate(self.verse_frames):
                    vf.setProperty("panel", "wahi" if i == active_v else "card")
                    _repolish(vf)

    def _build_lexicon_page(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        self.lex_search = QLineEdit()
        self.lex_search.setPlaceholderText("ابحث في معجم المواضع والألفاظ النبوية...")
        self.lex_search.textChanged.connect(self._render_lex)
        lay.addWidget(self.lex_search)

        inner = QWidget()
        self.lex_grid = QGridLayout(inner)
        self.lex_grid.setSpacing(10)
        lay.addWidget(_make_scrollable(inner), 1)
        self._render_lex("")
        return wrap

    def _render_lex(self, q: str):
        q = q.strip()
        while self.lex_grid.count():
            it = self.lex_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        items = [x for x in self.lexicon if not q or q in f"{x['term']} {x['vocalized']} {x['meaning']}"]
        for i, lx in enumerate(items):
            c = QFrame()
            c.setProperty("panel", "glass")
            cl = QVBoxLayout(c)
            t = QLabel(f"📖 {lx['vocalized']}")
            t.setProperty("role", "title")
            m = QLabel(lx["meaning"])
            m.setWordWrap(True)
            cl.addWidget(t)
            cl.addWidget(m)
            if lx.get("linkedEvent"):
                jb = QPushButton("🗺️ شاهد الموضع في الأطلس ←")
                jb.clicked.connect(lambda _=False, eid=lx["linkedEvent"]: self.jumpEvent.emit(eid))
                cl.addWidget(jb)
            self.lex_grid.addWidget(c, i // 2, i % 2)


# ==============================================================================
# VIEW 9: PRACTICAL PROPHETIC GUIDANCE
# ==============================================================================
class GuidanceView(QWidget):
    def __init__(self, repo, state, serif_font: str, parent=None):
        super().__init__(parent)
        self.items = repo.guidance
        self.state = state
        self.serif_font = serif_font
        self.cat = "all"

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.cat_btns = {}
        for k, lbl in [
            ("all", "الكل (10)"),
            ("psych", "🌱 السكينة النفسية"),
            ("social", "🤝 بناء القلوب"),
            ("leadership", "⚖️ القيادة والإتقان"),
            ("health", "🍯 العافية البدنية"),
        ]:
            b = QPushButton(lbl)
            b.setProperty("btn", "pill")
            b.clicked.connect(lambda _=False, ck=k: self._set_cat(ck))
            self.cat_btns[k] = b
            top.addWidget(b)
        top.addStretch(1)
        self.counter_lbl = QLabel()
        self.counter_lbl.setProperty("role", "teal-badge")
        top.addWidget(self.counter_lbl)
        root.addLayout(top)

        inner = QWidget()
        self.grid = QGridLayout(inner)
        self.grid.setSpacing(12)
        root.addWidget(_make_scrollable(inner), 1)

        self._set_cat("all")

    def _set_cat(self, ck: str):
        self.cat = ck
        for k, b in self.cat_btns.items():
            b.setProperty("active", "true" if k == ck else "false")
            _repolish(b)
        self._render()

    def _render(self):
        done_ids = set(self.state.data.get("sunnah_done", []))
        self.counter_lbl.setText(f"🌟 سنن مطبّقة اليوم: {len(done_ids)} من {len(self.items)}")

        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        vis = [g for g in self.items if self.cat == "all" or g["category"] == self.cat]
        for i, g in enumerate(vis):
            done = g["id"] in done_ids
            c = QFrame()
            c.setProperty("panel", "wahi" if done else "glass")
            cl = QVBoxLayout(c)
            cl.setSpacing(8)
            cat_l = QLabel(g["categoryLabel"])
            cat_l.setProperty("role", "badge")
            tit = QLabel(g["title"])
            tit.setProperty("role", "title")
            tit.setWordWrap(True)
            had = QLabel(g["hadith"])
            had.setFont(QFont(self.serif_font, 15))
            had.setWordWrap(True)
            ins = QLabel(g["insight"])
            ins.setWordWrap(True)
            act = QLabel(f"🎯 خطوتك العملية اليوم: {g['actionToday']}")
            act.setStyleSheet("font-weight: bold;")
            act.setWordWrap(True)

            btn = QPushButton("✅ طبّقتُ هذه السنة اليوم" if done else "☐ علّمها كمطبّقة اليوم")
            if done:
                btn.setProperty("btn", "gold")
            btn.clicked.connect(lambda _=False, gid=g["id"]: self._toggle_sunnah(gid))

            cl.addWidget(cat_l, 0, Qt.AlignmentFlag.AlignRight)
            cl.addWidget(tit)
            cl.addWidget(had)
            cl.addWidget(ins)
            cl.addWidget(act)
            cl.addWidget(btn)
            self.grid.addWidget(c, i // 2, i % 2)

    def _toggle_sunnah(self, gid: str):
        self.state.toggle_in_list("sunnah_done", gid)
        self._render()


# ==============================================================================
# VIEW 10: PROPHETIC MUSEUM & ETERNAL MANUSCRIPTS
# ==============================================================================
class MuseumView(QWidget):
    def __init__(self, repo, state, serif_font: str, parent=None):
        super().__init__(parent)
        self.relics = repo.relics
        self.state = state
        self.serif_font = serif_font

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setSpacing(14)

        for i, rl in enumerate(self.relics):
            c = QFrame()
            c.setProperty("panel", "glass")
            cl = QVBoxLayout(c)
            cl.setContentsMargins(18, 18, 18, 18)
            cl.setSpacing(10)

            meta = QLabel(f"{rl.get('icon', '📜')} {rl['category']}  •  {rl['year']}")
            meta.setProperty("role", "badge")
            tit = QLabel(rl["title"])
            tit.setProperty("role", "title")
            tit.setWordWrap(True)

            ex_box = QFrame()
            ex_box.setProperty("panel", "card")
            el = QVBoxLayout(ex_box)
            ex = QLabel(rl["excerpt"])
            ex.setFont(QFont(serif_font, 15))
            ex.setWordWrap(True)
            el.addWidget(ex)

            note = QLabel(rl["historicalNote"])
            note.setProperty("role", "subtitle")
            note.setWordWrap(True)

            open_b = QPushButton("🔍 استعراض نص الوثيقة الكامل وتحقيقها")
            open_b.setProperty("btn", "gold")
            open_b.clicked.connect(lambda _=False, item=rl: self.open_relic(item))

            cl.addWidget(meta, 0, Qt.AlignmentFlag.AlignRight)
            cl.addWidget(tit)
            cl.addWidget(ex_box)
            cl.addWidget(note)
            cl.addWidget(open_b)
            grid.addWidget(c, i // 2, i % 2)

        root.addWidget(_make_scrollable(inner))

    def open_relic_by_id(self, relic_id: str):
        rl = next((x for x in self.relics if x["id"] == relic_id), None)
        if rl:
            self.open_relic(rl)

    def open_relic(self, rl: dict):
        self.state.add_unique("relics", rl["id"])
        dlg = RelicManuscriptDialog(rl, self.serif_font, self)
        dlg.exec()


# ==============================================================================
# VIEW 11: 30-DAY SEERAH KHATMAH & PERSONALIZED GOLDEN CERTIFICATE
# ==============================================================================
class KhatmahCertView(QWidget):
    def __init__(self, repo, state, serif_font: str, ui_font: str, parent=None):
        super().__init__(parent)
        self.days = repo.khatmah_days
        self.state = state
        self.serif_font = serif_font
        self.ui_font = ui_font

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.b_plan = QPushButton("📅 خطة الـ 30 مجلساً")
        self.b_cert = QPushButton("🎓 إصدار شهادة الإتمام الذهبية باسمك")
        for b in (self.b_plan, self.b_cert):
            b.setProperty("btn", "pill")
        self.b_plan.clicked.connect(lambda: self._set_mode(0))
        self.b_cert.clicked.connect(lambda: self._set_mode(1))
        top.addWidget(self.b_plan)
        top.addWidget(self.b_cert)
        top.addStretch(1)
        self.prog_bar = QProgressBar()
        self.prog_bar.setMinimumWidth(260)
        top.addWidget(self.prog_bar)
        root.addLayout(top)

        self.stack = QStackedWidget()
        self.plan_inner = QWidget()
        self.plan_grid = QGridLayout(self.plan_inner)
        self.plan_grid.setSpacing(10)
        self.stack.addWidget(_make_scrollable(self.plan_inner))
        self.stack.addWidget(self._build_cert_studio())
        root.addWidget(self.stack, 1)

        self._set_mode(0)
        self._render_plan()

    def open_cert_tab(self):
        self._set_mode(1)

    def _set_mode(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.b_plan.setProperty("active", "true" if idx == 0 else "false")
        self.b_cert.setProperty("active", "true" if idx == 1 else "false")
        _repolish(self.b_plan)
        _repolish(self.b_cert)

    def _render_plan(self):
        done = set(self.state.data.get("khatmah_done", []))
        pct = round(len(done) * 100 / max(1, len(self.days)))
        self.prog_bar.setValue(pct)
        self.prog_bar.setFormat(f"إنجاز الختمة: {len(done)} / {len(self.days)} ({pct}%)")

        while self.plan_grid.count():
            it = self.plan_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        for i, d in enumerate(self.days):
            day_num = d["day"]
            is_done = day_num in done
            c = QFrame()
            c.setProperty("panel", "wahi" if is_done else "glass")
            cl = QVBoxLayout(c)
            hdr = QLabel(f"المجلس {day_num}: {d['title']}")
            hdr.setStyleSheet("font-weight: bold;")
            hdr.setWordWrap(True)
            sm = QLabel(d["summary"])
            sm.setProperty("role", "subtitle")
            sm.setWordWrap(True)
            btn = QPushButton("✅ تمّ المجلس بحمد الله" if is_done else "☐ علّمه كمجلس مُنجز")
            if is_done:
                btn.setProperty("btn", "gold")
            btn.clicked.connect(lambda _=False, dn=day_num: self._toggle_day(dn))
            cl.addWidget(hdr)
            cl.addWidget(sm)
            cl.addWidget(btn)
            self.plan_grid.addWidget(c, i // 3, i % 3)

    def _toggle_day(self, day_num: int):
        self.state.toggle_in_list("khatmah_done", day_num)
        self._render_plan()

    def _build_cert_studio(self) -> QWidget:
        card = QFrame()
        card.setProperty("panel", "glass")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(14)

        t = QLabel("🎓 استوديو إصدار وثيقة ختمة السيرة المذهّبة عالية الدقة (1600×1120 PNG)")
        t.setProperty("role", "title")
        t.setWordWrap(True)
        lay.addWidget(t)

        lay.addWidget(QLabel("اكتب اسمك الكريم كما تحب أن يُنقش على الإجازة الذهبية:"))
        self.name_input = QLineEdit(self.state.data.get("reader_name", ""))
        self.name_input.setPlaceholderText("مثال: محمد صلاح عبد الخالق")
        lay.addWidget(self.name_input)

        gen_btn = QPushButton("🏅 توليد ومعاينة وحفظ الشهادة الذهبية الآن")
        gen_btn.setProperty("btn", "gold")
        gen_btn.clicked.connect(self._generate_cert)
        lay.addWidget(gen_btn)
        lay.addStretch(1)
        return card

    def _generate_cert(self):
        name = self.name_input.text().strip()
        self.state.data["reader_name"] = name
        self.state.save()
        done_councils = len(self.state.data.get("khatmah_done", []))
        mastery_pct, _, _ = self.state.mastery_stats()
        _, _, _, hijri_str = gregorian_to_hijri()
        img = render_khatmah_certificate(
            name, done_councils, mastery_pct, hijri_str, self.serif_font, self.ui_font
        )
        dlg = ImageExportPreviewDialog(
            "🎓 شهادة إتمام ومدارسة السيرة النبوية الشريفة",
            img,
            "sirag-seerah-certificate.png",
            self,
        )
        dlg.exec()
