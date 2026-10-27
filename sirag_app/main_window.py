import os
import sys
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME_AR, APP_VERSION, DEV_URL
from .audio_engine import NativeAudioEngine
from .dialogs import OmniSearchDialog, SettingsAndUpdaterDialog, UpdateCheckWorker, _compare_semver
from .state import DataRepository, UserState, gregorian_to_hijri, open_external_url, resource_path
from .theme import build_stylesheet
from .views_part1 import (
    AtlasView,
    BattlesView,
    HijrahQuizView,
    SanctuariesView,
    ScenariosView,
    _repolish,
)
from .views_part2 import (
    ConstellationView,
    DiwanLexiconView,
    GuidanceView,
    KhatmahCertView,
    LineageShamailView,
    MuseumView,
)


class SiragMainWindow(QMainWindow):
    def __init__(self, ui_font: str, serif_font: str):
        super().__init__()
        self.ui_font = ui_font
        self.serif_font = serif_font

        self.setWindowTitle(f"{APP_NAME_AR} — الإصدار الأصلي المستقل لنظام ويندوز (v{APP_VERSION})")
        self.resize(1380, 880)
        self.setMinimumSize(780, 560)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        ico_candidate = resource_path("windows/sirag-atlas.ico")
        icon_path = ico_candidate if os.path.exists(ico_candidate) else resource_path("assets/icon-512.png")
        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(self.app_icon)

        self.repo = DataRepository()
        self.state = UserState(self.repo)
        self.audio = NativeAudioEngine(self)

        # Optional system tray for native Linux desktop notifications
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.app_icon, self)
            self.tray.show()

        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # 1. Top Royal Header
        header = QFrame()
        header.setProperty("panel", "header")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 10, 16, 10)
        h_lay.setSpacing(12)

        seal_lbl = QLabel()
        seal_pix = QPixmap(resource_path("assets/icon-round.png")).scaled(
            42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        seal_lbl.setPixmap(seal_pix)
        h_lay.addWidget(seal_lbl)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        b_title = QLabel("سراج أطلس السيرة النبوية")
        b_title.setProperty("role", "title")
        b_sub = QLabel("الأطلس الزماني-المكاني لسيرة خير الأنام ﷺ • واجهة سطح مكتب أصلية مستقلة")
        b_sub.setProperty("role", "subtitle")
        brand_col.addWidget(b_title)
        brand_col.addWidget(b_sub)
        h_lay.addLayout(brand_col)
        h_lay.addStretch(1)

        _, hijri_month, _, hijri_text = gregorian_to_hijri()
        hijri_pill = QLabel(f"🌙 {hijri_text}")
        hijri_pill.setProperty("role", "badge")
        h_lay.addWidget(hijri_pill)

        self.score_btn = QPushButton("🏅 0% مستكشف")
        self.score_btn.clicked.connect(self._jump_to_cert)
        h_lay.addWidget(self.score_btn)

        search_btn = QPushButton("🔍 بحث")
        search_btn.setToolTip("البحث الفوري الشامل والمحفوظات (Ctrl+K)")
        search_btn.clicked.connect(self.open_search)
        h_lay.addWidget(search_btn)

        self.settings_btn = QPushButton("⚙️ الإعدادات")
        self.settings_btn.setProperty("btn", "gold")
        self.settings_btn.clicked.connect(self.open_settings)
        h_lay.addWidget(self.settings_btn)

        main_lay.addWidget(header)

        # 2. Horizontal All-Sections Navigation Strip
        nav_frame = QFrame()
        nav_frame.setProperty("panel", "navstrip")
        nf_lay = QVBoxLayout(nav_frame)
        nf_lay.setContentsMargins(10, 6, 10, 6)

        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        nav_scroll.setMaximumHeight(50)

        nav_bar_w = QWidget()
        nav_lay = QHBoxLayout(nav_bar_w)
        nav_lay.setContentsMargins(2, 2, 2, 2)
        nav_lay.setSpacing(6)

        self.section_defs = [
            ("atlas", "🗺️ الأطلس الحي"),
            ("hijrah", "🐪 الهجرة والفرسان"),
            ("battles", "⚔️ محاكي الغزوات"),
            ("sanctuaries", "🕌 معالم الحرمين"),
            ("scenarios", "🧭 لو كنتَ يومئذٍ"),
            ("constellation", "✨ مجرّة الصحابة"),
            ("lineage", "🌿 النسب والشمائل"),
            ("diwan", "🎙️ الديوان والمعجم"),
            ("guidance", "💎 الهدي التطبيقي"),
            ("museum", "📜 المتحف النبوي"),
            ("khatmah", "🏅 الختمة والشهادة"),
        ]
        self.nav_btns = {}
        for idx, (key, label) in enumerate(self.section_defs):
            b = QPushButton(label)
            b.setProperty("btn", "nav")
            b.clicked.connect(lambda _=False, i=idx: self.switch_section_index(i))
            self.nav_btns[key] = (idx, b)
            nav_lay.addWidget(b)
        nav_lay.addStretch(1)
        nav_scroll.setWidget(nav_bar_w)
        nf_lay.addWidget(nav_scroll)
        main_lay.addWidget(nav_frame)

        # 3. Hijri Memory & Live Update Notification Banner
        mem_wrap = QWidget()
        mw_lay = QVBoxLayout(mem_wrap)
        mw_lay.setContentsMargins(14, 8, 14, 2)
        mw_lay.setSpacing(6)

        self.update_banner = QFrame()
        self.update_banner.setProperty("panel", "wahi")
        ub_lay = QHBoxLayout(self.update_banner)
        ub_lay.setContentsMargins(12, 6, 12, 6)
        self.update_banner_lbl = QLabel()
        self.update_banner_lbl.setWordWrap(True)
        ub_btn = QPushButton("⬇️ فتح الإعدادات للتنزيل")
        ub_btn.setProperty("btn", "gold")
        ub_btn.clicked.connect(self.open_settings)
        ub_close = QPushButton("✕")
        ub_close.clicked.connect(self.update_banner.hide)
        ub_lay.addWidget(self.update_banner_lbl, 1)
        ub_lay.addWidget(ub_btn)
        ub_lay.addWidget(ub_close)
        self.update_banner.hide()
        mw_lay.addWidget(self.update_banner)

        mem_card = QFrame()
        mem_card.setProperty("panel", "memory")
        mc_lay = QHBoxLayout(mem_card)
        mc_lay.setContentsMargins(12, 7, 12, 7)
        matched_ev = next(
            (e for e in self.repo.events if e.get("hijriMonth") == hijri_month),
            self.repo.events[0],
        )
        self._mem_event_id = matched_ev["id"]
        mem_tag = QLabel("في مثل هذا الشهر الهجري")
        mem_tag.setProperty("role", "badge")
        mem_txt = QLabel(
            f"تزامن شهري: «{matched_ev['title']}» ({matched_ev['yearLabel']}) — في {matched_ev['locationName']}"
        )
        mem_btn = QPushButton("انتقل للمحطة ←")
        mem_btn.clicked.connect(self._jump_memory_station)
        mc_lay.addWidget(mem_tag)
        mc_lay.addWidget(mem_txt, 1)
        mc_lay.addWidget(mem_btn)
        mw_lay.addWidget(mem_card)
        main_lay.addWidget(mem_wrap)

        # 4. Main Views Stack
        self.stack = QStackedWidget()
        self.v_atlas = AtlasView(self.repo, self.state, serif_font, ui_font)
        self.v_hijrah = HijrahQuizView(self.repo, self.state, ui_font)
        self.v_battles = BattlesView(self.repo, self.state, ui_font)
        self.v_sanctuaries = SanctuariesView(self.repo, serif_font, ui_font)
        self.v_scenarios = ScenariosView(self.repo, self.state)
        self.v_constellation = ConstellationView(self.repo, self.state, serif_font, ui_font)
        self.v_lineage = LineageShamailView(self.repo, serif_font, ui_font)
        self.v_diwan = DiwanLexiconView(self.repo, self.audio, serif_font)
        self.v_guidance = GuidanceView(self.repo, self.state, serif_font)
        self.v_museum = MuseumView(self.repo, self.state, serif_font)
        self.v_khatmah = KhatmahCertView(self.repo, self.state, serif_font, ui_font)

        for vw in [
            self.v_atlas,
            self.v_hijrah,
            self.v_battles,
            self.v_sanctuaries,
            self.v_scenarios,
            self.v_constellation,
            self.v_lineage,
            self.v_diwan,
            self.v_guidance,
            self.v_museum,
            self.v_khatmah,
        ]:
            self.stack.addWidget(vw)

        main_lay.addWidget(self.stack, 1)

        # Cross-view signals
        self.v_atlas.jumpBattle.connect(self._on_jump_battle)
        self.v_atlas.jumpScenario.connect(self._on_jump_scenario)
        self.v_constellation.jumpEvent.connect(self._on_jump_event)
        self.v_diwan.jumpEvent.connect(self._on_jump_event)

        # 5. Official Developer Attribution Footer Bar ("عن المطور" + Button underneath)
        footer = QFrame()
        footer.setProperty("panel", "footer")
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(16, 6, 16, 8)
        f_lay.setSpacing(4)
        about_lbl = QLabel("عن المطور")
        about_lbl.setProperty("role", "subtitle")
        about_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_lay.addWidget(about_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        dev_btn = QPushButton("محمد صلاح عبد الخالق")
        dev_btn.setProperty("btn", "dev")
        dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dev_btn.setToolTip(DEV_URL)
        dev_btn.clicked.connect(lambda: open_external_url(DEV_URL))
        btn_row.addWidget(dev_btn)
        btn_row.addStretch(1)
        f_lay.addLayout(btn_row)
        main_lay.addWidget(footer)

        # Keyboard Shortcuts
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_search)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)
        for n in range(1, 10):
            QShortcut(QKeySequence(f"Alt+{n}"), self, activated=lambda idx=n - 1: self.switch_section_index(idx))

        self.state.on_change(self._refresh_score)
        self._refresh_score()
        self.apply_theme()
        self.switch_section_index(0)

        # Silent startup repository update check
        if self.state.data.get("auto_update_notify", True):
            QTimer.singleShot(2800, self._silent_startup_update_check)

    def apply_theme(self):
        theme_key = self.state.data.get("theme", "night")
        qss = build_stylesheet(
            theme_key,
            self.state.data.get("font_scale", "normal"),
            self.ui_font,
            self.serif_font,
        )
        QApplication.instance().setStyleSheet(qss)
        self._apply_win11_titlebar_theme(theme_key == "night")

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_win11_titlebar_theme(self.state.data.get("theme", "night") == "night")

    def _apply_win11_titlebar_theme(self, dark: bool):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            val = ctypes.c_int(1 if dark else 0)
            for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (Win11 / Win10 20H1+)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_int(attr),
                    ctypes.byref(val),
                    ctypes.sizeof(val),
                )
        except Exception:
            pass

    def _refresh_score(self):
        pct, done, total = self.state.mastery_stats()
        self.score_btn.setText(f"🏅 {pct}% مستكشف ({done}/{total})")

    def switch_section_by_key(self, key: str):
        if key in self.nav_btns:
            self.switch_section_index(self.nav_btns[key][0])

    def switch_section_index(self, idx: int):
        if idx != 0:
            self.v_atlas.stop_autoplay()
        if idx != 2:
            self.v_battles.stop_play()
        if idx != 7:
            self.audio.stop_poem()

        self.stack.setCurrentIndex(idx)
        for _k, (b_idx, btn) in self.nav_btns.items():
            btn.setProperty("active", "true" if b_idx == idx else "false")
            _repolish(btn)

    def _jump_memory_station(self):
        self.switch_section_by_key("atlas")
        self.v_atlas.jump_to_event_id(self._mem_event_id)

    def _jump_to_cert(self):
        self.switch_section_by_key("khatmah")
        self.v_khatmah.open_cert_tab()

    def _on_jump_battle(self, bid: str):
        self.switch_section_by_key("battles")
        self.v_battles.select_battle_by_id(bid)

    def _on_jump_scenario(self, scid: str):
        self.switch_section_by_key("scenarios")
        self.v_scenarios.select_scenario_by_id(scid)

    def _on_jump_event(self, eid: str):
        self.switch_section_by_key("atlas")
        self.v_atlas.jump_to_event_id(eid)

    def open_search(self):
        dlg = OmniSearchDialog(self.repo, self.state, self)
        dlg.jumpRequested.connect(self._handle_omni_jump)
        dlg.exec()

    def _handle_omni_jump(self, t_type: str, t_id: str):
        if t_type == "event":
            self._on_jump_event(t_id)
        elif t_type == "battle":
            self._on_jump_battle(t_id)
        elif t_type == "companion":
            self.switch_section_by_key("constellation")
            self.v_constellation.select_companion(t_id)
        elif t_type == "poem":
            self.switch_section_by_key("diwan")
            self.v_diwan.select_poem_by_id(t_id)
        elif t_type == "lexicon":
            self.switch_section_by_key("diwan")
            self.v_diwan.open_lexicon_term(t_id)
        elif t_type == "relic":
            self.switch_section_by_key("museum")
            self.v_museum.open_relic_by_id(t_id)

    def open_settings(self):
        dlg = SettingsAndUpdaterDialog(self.state, self.audio, self._push_desktop_notification, self)
        dlg.appearanceChanged.connect(self.apply_theme)
        dlg.exec()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _push_desktop_notification(self, title: str, message: str):
        self.update_banner_lbl.setText(f"🔔 {title} — {message}")
        self.update_banner.show()
        self.settings_btn.setText("⚙️ الإعدادات • تحديث!")
        if self.tray:
            try:
                self.tray.showMessage(title, message, self.app_icon, 6000)
            except Exception:
                pass

    def _silent_startup_update_check(self):
        self._bg_checker = UpdateCheckWorker(self)
        self._bg_checker.finishedCheck.connect(self._on_silent_check)
        self._bg_checker.start()

    def _on_silent_check(self, ok: bool, remote_ver: str, changelog: str, _exe_url: str, _msix_url: str):
        if ok and _compare_semver(remote_ver, APP_VERSION) > 0:
            self._push_desktop_notification(f"تحديث جديد متاح (v{remote_ver})", changelog)

    def closeEvent(self, event):
        if self.tray:
            self.tray.hide()
        bg = getattr(self, "_bg_checker", None)
        if bg is not None and bg.isRunning():
            bg.quit()
            bg.wait(1000)
        super().closeEvent(event)
