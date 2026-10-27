# 🪟 سراج أطلس السيرة النبوية ﷺ — نسخة ويندوز 10 / 11 الأصلية المستقلة (Portable `.exe` + Windows 11 Store `.msix`)

<p align="center">
  <img src="assets/icon-192.png" width="128" alt="سراج أطلس السيرة النبوية" />
</p>

<p align="center">
  <strong>الأطلس الزماني-المكاني التفاعلي لسيرة خير الأنام محمد ﷺ — تطبيق سطح مكتب ويندوز أصلي مستقل 100% (`Pure Native Qt 6 GUI`) بدون أي اعتماد على متصفح أو Electron!</strong>
</p>

<p align="center">
  <a href="https://github.com/mosalah30688-gif/sirag-atlas-windows/releases/latest/download/Sirag-Atlas-Seerah-Portable-x64.exe">
    <img src="https://img.shields.io/badge/⚡_Download_Portable_.EXE-Windows_10%2F11_(No_Install)-d4a853?style=for-the-badge&logo=windows&logoColor=070f1c" alt="Download Portable EXE" />
  </a>
  <a href="https://github.com/mosalah30688-gif/sirag-atlas-windows/releases/latest/download/Sirag-Atlas-Seerah-Win11-Store-x64.msix">
    <img src="https://img.shields.io/badge/🛍️_Download_Win11_Store_.MSIX-Microsoft_Store_Package-0078D4?style=for-the-badge&logo=windows11&logoColor=white" alt="Download Windows 11 MSIX" />
  </a>
</p>

---

## 📦 النسختان الرسميتان الجاهزتان للتحميل الفوري

### 1️⃣ النسخة البورتابل المحمولة (`Sirag-Atlas-Seerah-Portable-x64.exe`)
- **ملف `.exe` واحد فقط مستقل بذاته** — لا يحتاج أي تثبيت ولا صلاحيات مسؤول ولا اتصال بالإنترنت.
- **طريقة التشغيل:** حمّل الملف واضغط عليه مرتين (**Double-Click**) من سطح المكتب أو من الفلاشة مباشرة!
- 🔗 **التحميل المباشر:** [`Sirag-Atlas-Seerah-Portable-x64.exe`](https://github.com/mosalah30688-gif/sirag-atlas-windows/releases/latest/download/Sirag-Atlas-Seerah-Portable-x64.exe)

---

### 2️⃣ حزمة متجر ويندوز 11 الرسمية (`Sirag-Atlas-Seerah-Win11-Store-x64.msix`)
- مبنية رسمياً عبر أدوات **Windows 11 SDK (`makeappx.exe` + `signtool.exe`)** بملف بيان `AppxManifest.xml` كامل وبلاطات قائمة ابدأ عالية الدقة لـ Windows 11 (`Assets\Square44x44Logo`, `Square150x150Logo`, `Wide310x150Logo`, `Square310x310Logo`, `StoreLogo`, `SplashScreen`).
- جاهزة لرفعها إلى **Microsoft Partner Center (متجر ويندوز 11)** أو لتثبيتها محلياً عبر **Windows App Installer**:
  - *للتثبيت المحلي خارج المتجر:* حمّل ملف الشهادة المرفق في الإصدار [`Sirag-Atlas-Win11-Store.cer`](https://github.com/mosalah30688-gif/sirag-atlas-windows/releases/latest/download/Sirag-Atlas-Win11-Store.cer) ⬅️ افتحه واختر **Install Certificate** ⬅️ **Local Machine** ⬅️ **Place all certificates in the following store: Trusted Root Certification Authorities**، ثم افتح ملف `Sirag-Atlas-Seerah-Win11-Store-x64.msix` واضغط **Install**.
- 🔗 **التحميل المباشر:** [`Sirag-Atlas-Seerah-Win11-Store-x64.msix`](https://github.com/mosalah30688-gif/sirag-atlas-windows/releases/latest/download/Sirag-Atlas-Seerah-Win11-Store-x64.msix)

---

## ✨ أبرز المزايا الهندسية في إصدار ويندوز الأصلي (`v2.0.1`)

- 🖥️ **واجهة `Qt 6` أصلية 100% بدون متصفح**: مرسومة مباشرة بمحرك `QPainter` مع تسريع عتادي، وتكامل أصيل مع شريط العنوان الداكن في **Windows 11 (`DWM Immersive Dark Mode`)**.
- 🗺️ **الأقسام الـ 11 الكاملة أوفلاين**: الأطلس الجغرافي التفاعلي (`QWidget` مخصص بالتحريك والتكبير والمسارات المتحركة)، الخط الزمني، الراوي الصوتي الأصلي (`QtMultimedia`) لـ 6 فصول كاملة مضمّنة، المختبر التكتيكي للغزوات، أطلس الوفود، شجرة النسب الشريف والبيت النبوي، الوثائق النبوية، متحف الآثار، الفهرس الشامل، الإنجازات والمفضلة، واستوديو التصدير الطباعي (`PNG` فائق الدقة).
- 🔄 **محدّث تلقائي متصل بالمستودع**: يفحص التحديثات الجديدة من GitHub Releases ويتيح تنزيل أحدث نسخة `.exe` أو `.msix` مباشرة من داخل نافذة الإعدادات مع إشعارات سطح مكتب ويندوز.
- 🔤 **خطوط عربية مدمجة بالكامل**: يعمل بخطّي `Amiri` و `Readex Pro` المدمجين داخل الحزمة دون الحاجة لتثبيت أي خطوط إضافية على نظام ويندوز.

---

## 👨‍💻 عن المطور

**[محمد صلاح عبد الخالق](https://elkatebmohamadsalah.blogspot.com/?m=1#google_vignette)**

---

## 🔗 باقي منصات المشروع الشقيقة
- 🌐 **تطبيق الويب التقدمي (PWA) وحزمة أندرويد (APK):** [`mosalah30688-gif/sirag-atlas`](https://github.com/mosalah30688-gif/sirag-atlas)
- 🐧 **تطبيق سطح مكتب لينكس الأصلي (AppImage):** [`mosalah30688-gif/sirag-atlas-linux`](https://github.com/mosalah30688-gif/sirag-atlas-linux)
