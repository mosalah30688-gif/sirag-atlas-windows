import json
import os
import stat
import urllib.request
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import APP_VERSION, DEV_URL, REPO_SLUG
from .state import open_external_url, resource_path


def _compare_semver(a: str, b: str) -> int:
    pa = [int(x) if x.isdigit() else 0 for x in str(a).lstrip("vV").split(".")[:3]]
    pb = [int(x) if x.isdigit() else 0 for x in str(b).lstrip("vV").split(".")[:3]]
    while len(pa) < 3:
        pa.append(0)
    while len(pb) < 3:
        pb.append(0)
    return (pa > pb) - (pa < pb)


class UpdateCheckWorker(QThread):
    finishedCheck = Signal(bool, str, str, str, str)  # ok, remote_ver, changelog, exe_url, msix_url

    def run(self):
        remote_ver = APP_VERSION
        changelog = "تحديثات وتحسينات جديدة من المستودع الرسمي لنسخة ويندوز."
        exe_url = f"https://github.com/{REPO_SLUG}/releases/latest/download/Sirag-Atlas-Seerah-Portable-x64.exe"
        msix_url = f"https://github.com/{REPO_SLUG}/releases/latest/download/Sirag-Atlas-Seerah-Win11-Store-x64.msix"
        try:
            req = urllib.request.Request(
                f"https://raw.githubusercontent.com/{REPO_SLUG}/main/version.json",
                headers={"User-Agent": "SiragAtlasNativeWindows/2.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                vdata = json.loads(resp.read().decode("utf-8"))
                remote_ver = vdata.get("version", remote_ver)
                changelog = vdata.get("changelog", changelog)
                exe_url = vdata.get("portableExeUrl", exe_url)
                msix_url = vdata.get("msixUrl", msix_url)

            rel_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO_SLUG}/releases/latest",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "SiragAtlasNativeWindows/2.0"},
            )
            with urllib.request.urlopen(rel_req, timeout=10) as rresp:
                rdata = json.loads(rresp.read().decode("utf-8"))
                tag_v = rdata.get("tag_name", "").lstrip("vV")
                if tag_v and _compare_semver(tag_v, remote_ver) > 0:
                    remote_ver = tag_v
                for asset in rdata.get("assets", []):
                    nm = asset.get("name", "")
                    if nm.endswith(".exe"):
                        exe_url = asset.get("browser_download_url", exe_url)
                    elif nm.endswith(".msix"):
                        msix_url = asset.get("browser_download_url", msix_url)

            self.finishedCheck.emit(True, remote_ver, changelog, exe_url, msix_url)
        except Exception:
            self.finishedCheck.emit(False, remote_ver, changelog, exe_url, msix_url)


class BinaryDownloadWorker(QThread):
    progress = Signal(int)
    completed = Signal(bool, str)

    def __init__(self, url: str, target_path: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.target_path = target_path

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "SiragAtlasNativeWindows/2.0"})
            tmp_path = self.target_path + ".part"
            with urllib.request.urlopen(req, timeout=90) as resp:
                total = int(resp.headers.get("Content-Length", 0) or 0)
                downloaded = 0
                with open(tmp_path, "wb") as out:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(min(100, int(downloaded * 100 / total)))
            os.replace(tmp_path, self.target_path)
            self.completed.emit(True, self.target_path)
        except Exception as e:
            self.completed.emit(False, str(e))


class OmniSearchDialog(QDialog):
    jumpRequested = Signal(str, str)  # target_type, target_id

    def __init__(self, repo, state, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.state = state
        self.setWindowTitle("🔍 البحث الفوري الشامل والمحفوظات")
        self.resize(660, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        hdr = QLabel("🔍 الكشّاف الشامل عبر محطات السيرة، الغزوات، الصحابة، القصائد والمعجم")
        hdr.setProperty("role", "title")
        hdr.setWordWrap(True)
        lay.addWidget(hdr)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("اكتب اسم غزوة، صحابي، موضع، قصيدة، أو آية...")
        self.search_input.textChanged.connect(self._populate)
        lay.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.itemActivated.connect(self._on_pick)
        self.list_widget.itemClicked.connect(self._on_pick)
        lay.addWidget(self.list_widget, 1)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

        self._populate("")
        self.search_input.setFocus()

    def _populate(self, query: str):
        q = query.strip()
        self.list_widget.clear()
        hits = []

        if not q:
            bms = set(self.state.data.get("bookmarks", []))
            for ev in self.repo.events:
                if ev["id"] in bms:
                    hits.append(("event", ev["id"], f"🔖 [محفوظة] {ev['title']} — {ev['yearLabel']}"))
            for ev in self.repo.events[:8]:
                hits.append(("event", ev["id"], f"🗺️ {ev['title']} ({ev['locationName']})"))
        else:
            for ev in self.repo.events:
                blob = f"{ev['title']} {ev['locationName']} {ev['wahi']['ayah']} {ev['depths']['flash']}"
                if q in blob:
                    hits.append(("event", ev["id"], f"🗺️ محطة: {ev['title']} — {ev['yearLabel']}"))
            for b in self.repo.battles:
                if q in f"{b['title']} {b['terrainSummary']}":
                    hits.append(("battle", b["id"], f"⚔️ غزوة: {b['title']} ({b['date']})"))
            for c in self.repo.companions:
                if q in f"{c['name']} {c['title']} {c['bio']}":
                    hits.append(("companion", c["id"], f"✨ صحابي: {c['name']} — {c['title']}"))
            for p in self.repo.diwan_lexicon.get("poems", []):
                if q in f"{p['title']} {p['poet']}":
                    hits.append(("poem", p["id"], f"🎙️ قصيدة: {p['title']} — {p['poet']}"))
            for lx in self.repo.diwan_lexicon.get("lexicon", []):
                if q in f"{lx['term']} {lx['meaning']}":
                    hits.append(("lexicon", lx["term"], f"📖 معجم: {lx['vocalized']} — {lx['meaning'][:65]}..."))
            for rl in self.repo.relics:
                if q in f"{rl['title']} {rl['fullText']}":
                    hits.append(("relic", rl["id"], f"📜 وثيقة: {rl['title']}"))

        for t_type, t_id, label in hits[:30]:
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, (t_type, t_id))
            self.list_widget.addItem(it)

    def _on_pick(self, item: QListWidgetItem):
        payload = item.data(Qt.ItemDataRole.UserRole)
        if payload:
            self.jumpRequested.emit(payload[0], payload[1])
            self.accept()


class ImageExportPreviewDialog(QDialog):
    def __init__(self, title: str, qimage, default_filename: str, parent=None):
        super().__init__(parent)
        self.qimage = qimage
        self.default_filename = default_filename
        self.setWindowTitle(title)
        self.resize(720, 660)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "title")
        lay.addWidget(lbl_title)

        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap.fromImage(qimage).scaled(
            660, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        preview.setPixmap(pix)
        lay.addWidget(preview, 1)

        row = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ الصورة بدقة كاملة (PNG) على جهازك")
        save_btn.setProperty("btn", "gold")
        save_btn.clicked.connect(self._save_png)
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        row.addWidget(save_btn, 2)
        row.addWidget(close_btn, 1)
        lay.addLayout(row)

    def _save_png(self):
        downloads = str(Path.home() / "Downloads" / self.default_filename)
        out_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ اللوحة الذهبية", downloads, "PNG Images (*.png)"
        )
        if out_path:
            if not out_path.lower().endswith(".png"):
                out_path += ".png"
            self.qimage.save(out_path, "PNG")
            QMessageBox.information(self, "تم الحفظ بنجاح", f"تم حفظ اللوحة عالية الدقة في:\n{out_path}")


class RelicManuscriptDialog(QDialog):
    def __init__(self, relic: dict, serif_font: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(relic.get("title", ""))
        self.resize(640, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        meta = QLabel(f"{relic.get('icon', '📜')} {relic.get('category', '')} • {relic.get('year', '')}")
        meta.setProperty("role", "badge")
        lay.addWidget(meta, 0, Qt.AlignmentFlag.AlignRight)

        title = QLabel(relic.get("title", ""))
        title.setProperty("role", "title")
        title.setWordWrap(True)
        lay.addWidget(title)

        card = QFrame()
        card.setProperty("panel", "wahi")
        c_lay = QVBoxLayout(card)
        txt = QLabel(relic.get("fullText", ""))
        txt.setFont(QFont(serif_font, 16))
        txt.setWordWrap(True)
        c_lay.addWidget(txt)
        lay.addWidget(card)

        note = QLabel(f"📚 التوثيق التاريخي: {relic.get('historicalNote', '')}")
        note.setProperty("role", "subtitle")
        note.setWordWrap(True)
        lay.addWidget(note)

        btn = QPushButton("إغلاق")
        btn.setProperty("btn", "gold")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


class SettingsAndUpdaterDialog(QDialog):
    appearanceChanged = Signal()

    def __init__(self, state, audio_engine, notify_callback, parent=None):
        super().__init__(parent)
        self.state = state
        self.audio = audio_engine
        self.notify_callback = notify_callback
        self._worker = None
        self._dl_worker = None
        self._latest_exe_url = f"https://github.com/{REPO_SLUG}/releases/latest/download/Sirag-Atlas-Seerah-Portable-x64.exe"
        self._latest_msix_url = f"https://github.com/{REPO_SLUG}/releases/latest/download/Sirag-Atlas-Seerah-Win11-Store-x64.msix"

        self.setWindowTitle(f"⚙️ إعدادات التطبيق والتحديثات • v{APP_VERSION}")
        self.resize(620, 640)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(14)

        hdr = QLabel(f"⚙️ إعدادات «سراج أطلس السيرة النبوية» (الإصدار الأصلي v{APP_VERSION})")
        hdr.setProperty("role", "title")
        hdr.setWordWrap(True)
        lay.addWidget(hdr)

        # 1. Live GitHub Windows Updater (Portable EXE + Win11 MSIX)
        upd_box = QFrame()
        upd_box.setProperty("panel", "glass")
        u_lay = QVBoxLayout(upd_box)
        u_title = QLabel("🔄 التحديث المباشر من المستودع لنظام ويندوز (Portable EXE + متجر ويندوز 11 MSIX)")
        u_title.setStyleSheet("font-weight: bold;")
        u_lay.addWidget(u_title)

        self.check_btn = QPushButton("🔄 فحص وجود تحديثات جديدة في المستودع الآن")
        self.check_btn.setProperty("btn", "gold")
        self.check_btn.clicked.connect(self._start_check)
        u_lay.addWidget(self.check_btn)

        self.auto_chk = QCheckBox("🔔 تفعيل فحص التحديثات التلقائي والإشعارات عند تشغيل التطبيق")
        self.auto_chk.setChecked(bool(self.state.data.get("auto_update_notify", True)))
        self.auto_chk.toggled.connect(self._toggle_auto_notify)
        u_lay.addWidget(self.auto_chk)

        self.upd_status = QLabel(f"متصل بالمستودع الرسمي: {REPO_SLUG}")
        self.upd_status.setProperty("role", "subtitle")
        self.upd_status.setWordWrap(True)
        u_lay.addWidget(self.upd_status)

        self.dl_bar = QProgressBar()
        self.dl_bar.hide()
        u_lay.addWidget(self.dl_bar)

        dl_row = QHBoxLayout()
        self.dl_btn = QPushButton("⚡ تنزيل النسخة المحمولة (Portable .exe)")
        self.dl_btn.clicked.connect(lambda: self._download_pkg("exe"))
        self.dl_msix_btn = QPushButton("🛍️ تنزيل حزمة متجر ويندوز 11 (.msix)")
        self.dl_msix_btn.clicked.connect(lambda: self._download_pkg("msix"))
        dl_row.addWidget(self.dl_btn)
        dl_row.addWidget(self.dl_msix_btn)
        u_lay.addLayout(dl_row)
        lay.addWidget(upd_box)

        # 2. Theme & Font Scaling
        th_box = QFrame()
        th_box.setProperty("panel", "glass")
        t_lay = QVBoxLayout(th_box)
        t_lay.addWidget(QLabel("🎨 المظهر وحجم الخط العربي:"))

        theme_row = QHBoxLayout()
        for key, label in [("night", "🌙 الوضع الليلي الفلكي"), ("parchment", "📜 الرقّ النهاري العاجي")]:
            b = QPushButton(label)
            b.setProperty("btn", "pill")
            b.setProperty("active", "true" if self.state.data.get("theme") == key else "false")
            b.clicked.connect(lambda _=False, k=key: self._set_theme(k))
            theme_row.addWidget(b)
        t_lay.addLayout(theme_row)

        scale_row = QHBoxLayout()
        for key, label in [("small", "صغير"), ("normal", "متوسط"), ("large", "كبير"), ("xlarge", "كبير جداً")]:
            b = QPushButton(label)
            b.setProperty("btn", "pill")
            b.setProperty("active", "true" if self.state.data.get("font_scale") == key else "false")
            b.clicked.connect(lambda _=False, k=key: self._set_font_scale(k))
            scale_row.addWidget(b)
        t_lay.addLayout(scale_row)
        lay.addWidget(th_box)

        # 3. Natural Ambiance (Music-Free)
        amb_box = QFrame()
        amb_box.setProperty("panel", "glass")
        a_lay = QVBoxLayout(amb_box)
        a_lay.addWidget(QLabel("🌬️ الأجواء الصوتية الطبيعية الهادئة (بدون موسيقى):"))

        self.amb_btn = QPushButton()
        self._refresh_amb_btn()
        self.amb_btn.clicked.connect(self._toggle_amb)
        a_lay.addWidget(self.amb_btn)

        amb_modes = QHBoxLayout()
        for mkey, mlabel in [("desert", "🌙 نسيم الليل"), ("rain", "🌧️ مطر بدر"), ("wind", "🍃 رياح الجبال")]:
            mb = QPushButton(mlabel)
            mb.clicked.connect(lambda _=False, mk=mkey: self._pick_amb_mode(mk))
            amb_modes.addWidget(mb)
        a_lay.addLayout(amb_modes)
        lay.addWidget(amb_box)

        # 4. Official Developer Attribution Card (Clean: "عن المطور" + Button underneath)
        dev_box = QFrame()
        dev_box.setProperty("panel", "glass")
        d_lay = QVBoxLayout(dev_box)
        d_lay.setSpacing(8)
        d_hdr = QLabel("عن المطور")
        d_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_hdr.setStyleSheet("font-weight: bold;")
        d_lay.addWidget(d_hdr)

        dev_btn = QPushButton("محمد صلاح عبد الخالق")
        dev_btn.setProperty("btn", "gold")
        dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dev_btn.setToolTip(DEV_URL)
        dev_btn.clicked.connect(lambda: open_external_url(DEV_URL))
        d_lay.addWidget(dev_btn)
        lay.addWidget(dev_box)

        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        close_b = QPushButton("إغلاق النافذة")
        close_b.clicked.connect(self.accept)
        outer.addWidget(close_b)

    def _toggle_auto_notify(self, checked: bool):
        self.state.data["auto_update_notify"] = checked
        self.state.save()

    def _set_theme(self, theme_key: str):
        self.state.data["theme"] = theme_key
        self.state.save()
        self.appearanceChanged.emit()
        self.accept()

    def _set_font_scale(self, scale_key: str):
        self.state.data["font_scale"] = scale_key
        self.state.save()
        self.appearanceChanged.emit()
        self.accept()

    def _refresh_amb_btn(self):
        on = self.audio.ambiance_enabled
        self.amb_btn.setText("🔊 الأجواء الطبيعية مفعّلة (اضغط للإيقاف)" if on else "🔇 تشغيل الأجواء الطبيعية الهادئة")

    def _toggle_amb(self):
        self.audio.toggle_ambiance(self.state.data.get("ambiance_type", "desert"))
        self._refresh_amb_btn()

    def _pick_amb_mode(self, mode: str):
        self.state.data["ambiance_type"] = mode
        self.state.save()
        self.audio.set_ambiance_mode(mode)
        if not self.audio.ambiance_enabled:
            self.audio.toggle_ambiance(mode)
        self._refresh_amb_btn()

    def _start_check(self):
        self.check_btn.setEnabled(False)
        self.upd_status.setText("⏳ جاري الاتصال بمستودع GitHub للتحقق من آخر إصدار...")
        self._worker = UpdateCheckWorker(self)
        self._worker.finishedCheck.connect(self._on_check_done)
        self._worker.start()

    def _on_check_done(self, ok: bool, remote_ver: str, changelog: str, exe_url: str, msix_url: str):
        self.check_btn.setEnabled(True)
        self._latest_exe_url = exe_url
        self._latest_msix_url = msix_url
        if not ok:
            self.upd_status.setText("⚠️ تعذر الاتصال بالمستودع حالياً — التطبيق يعمل بالكامل أوفلاين.")
            return
        if _compare_semver(remote_ver, APP_VERSION) > 0:
            msg = f"🔔 يتوفر إصدار جديد (v{remote_ver}): {changelog}"
            self.upd_status.setText(msg)
            self.dl_btn.setText(f"⚡ تنزيل التحديث المحمول (.exe v{remote_ver})")
            self.dl_btn.setProperty("btn", "gold")
            if self.notify_callback:
                self.notify_callback(f"تحديث جديد متاح v{remote_ver}", changelog)
        else:
            self.upd_status.setText(f"✅ أنت على أحدث إصدار متاح على المستودع (v{APP_VERSION}).")

    def _download_pkg(self, kind: str):
        if kind == "msix":
            url = self._latest_msix_url
            fname = "Sirag-Atlas-Seerah-Win11-Store-x64.msix"
            flt = "Windows 11 MSIX Package (*.msix)"
        else:
            url = self._latest_exe_url
            fname = "Sirag-Atlas-Seerah-Portable-x64.exe"
            flt = "Windows Executable (*.exe)"

        default_target = str(Path.home() / "Downloads" / fname)
        out_path, _ = QFileDialog.getSaveFileName(self, "حفظ حزمة ويندوز", default_target, flt)
        if not out_path:
            return
        self._pending_fallback_url = url
        self.dl_bar.setValue(0)
        self.dl_bar.show()
        self.dl_btn.setEnabled(False)
        self.dl_msix_btn.setEnabled(False)
        self._dl_worker = BinaryDownloadWorker(url, out_path, self)
        self._dl_worker.progress.connect(self.dl_bar.setValue)
        self._dl_worker.completed.connect(self._on_dl_done)
        self._dl_worker.start()

    def _on_dl_done(self, ok: bool, info: str):
        self.dl_btn.setEnabled(True)
        self.dl_msix_btn.setEnabled(True)
        if ok:
            self.upd_status.setText(f"✅ اكتمل التنزيل بنجاح:\n{info}")
            QMessageBox.information(self, "اكتمل التنزيل", f"تم حفظ النسخة المحدثة بنجاح في:\n{info}")
        else:
            self.upd_status.setText(f"⚠️ تعذر التنزيل المباشر ({info}) — سيتم فتح الرابط في المتصفح.")
            open_external_url(getattr(self, "_pending_fallback_url", self._latest_exe_url))
