#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    W I N T E R N E T   B R O W S E R                         ║
# ║              Liquid Glass · Safari-Inspired · Python + PyQt6                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import sys
import os
import json
import math
import time
import hashlib
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# ── Windows crash prevention — MUST happen before any Qt import ──────────────
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu-sandbox")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

# ── Qt imports ───────────────────────────────────────────────────────────────
from PyQt6.QtCore import (
    Qt, QUrl, QSize, QTimer, QThread, QObject, QPoint, QRect, QRectF,
    QPropertyAnimation, QEasingCurve, QAbstractAnimation, pyqtSignal,
    QParallelAnimationGroup, QSequentialAnimationGroup, QSettings,
    QMimeData, QByteArray, QRunnable, QThreadPool, QPointF, QSizeF,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTabBar, QSizePolicy,
    QFrame, QScrollArea, QListWidget, QListWidgetItem, QTextEdit,
    QDialog, QDialogButtonBox, QMenu, QMenuBar, QToolBar, QStatusBar,
    QSplitter, QStackedWidget, QCheckBox, QSlider, QSpinBox, QComboBox,
    QGroupBox, QProgressBar, QFileDialog, QInputDialog, QMessageBox,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QTreeWidget,
    QTreeWidgetItem, QAbstractItemView, QStyleOption, QStyle,
    QColorDialog, QFontDialog,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QBrush, QPen, QLinearGradient,
    QRadialGradient, QConicalGradient, QFont, QFontMetrics, QIcon,
    QPixmap, QImage, QAction, QKeySequence, QCursor, QPalette,
    QFontDatabase, QMovie, QRegion, QPolygonF, QTransform,
    QGradient,
)

# WebEngine — import BEFORE QApplication on Windows
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
    QWebEngineScript, QWebEngineUrlRequestInterceptor,
    QWebEngineDownloadRequest,
)

# ═════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & PATHS
# ═════════════════════════════════════════════════════════════════════════════

APP_NAME    = "Winternet"
APP_VERSION = "2.0.0"
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / ".winternet"
CACHE_DIR   = DATA_DIR / "cache"
HISTORY_FILE    = DATA_DIR / "history.json"
BOOKMARKS_FILE  = DATA_DIR / "bookmarks.json"
SETTINGS_FILE   = DATA_DIR / "settings.json"
DOWNLOADS_FILE  = DATA_DIR / "downloads.json"

for _d in [DATA_DIR, CACHE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

DEFAULT_HOME = "https://www.google.com"
DEFAULT_SEARCH = "https://www.google.com/search?q={}"

# ═════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  — liquid glass, deep ocean night
# ═════════════════════════════════════════════════════════════════════════════

class Palette:
    # Base layers
    VOID          = QColor(6,   8,  18)
    DEEP          = QColor(10,  14, 35)
    SURFACE       = QColor(15,  20, 50)
    RAISED        = QColor(22,  28, 65)

    # Glass
    GLASS_FILL    = QColor(255, 255, 255, 18)
    GLASS_FILL_HO = QColor(255, 255, 255, 30)
    GLASS_FILL_PR = QColor(255, 255, 255, 42)
    GLASS_BORDER  = QColor(255, 255, 255, 40)
    GLASS_BORDER_HO = QColor(255, 255, 255, 70)
    GLASS_SHINE   = QColor(255, 255, 255, 80)

    # Accents
    BLUE          = QColor(100, 160, 255)
    BLUE_SOFT     = QColor( 80, 140, 220, 180)
    PURPLE        = QColor(140, 100, 255)
    CYAN          = QColor( 60, 200, 220)
    ROSE          = QColor(255, 100, 140)
    AMBER         = QColor(255, 180,  60)
    GREEN         = QColor( 80, 220, 140)

    # Text
    TEXT_PRIMARY  = QColor(235, 240, 255)
    TEXT_SECONDARY= QColor(160, 175, 210)
    TEXT_DIM      = QColor( 90, 105, 145)
    TEXT_DISABLED = QColor( 55,  68, 100)

    # Semantic
    SUCCESS       = QColor( 80, 220, 140)
    WARNING       = QColor(255, 180,  60)
    ERROR         = QColor(255, 100, 120)
    INFO          = QColor(100, 160, 255)

    @staticmethod
    def with_alpha(color: QColor, alpha: int) -> QColor:
        c = QColor(color)
        c.setAlpha(alpha)
        return c


# ═════════════════════════════════════════════════════════════════════════════
#  SETTINGS MANAGER
# ═════════════════════════════════════════════════════════════════════════════

class SettingsManager:
    DEFAULTS = {
        "home_page":        DEFAULT_HOME,
        "search_engine":    DEFAULT_SEARCH,
        "new_tab_page":     "speed_dial",   # speed_dial | home | blank | game
        "theme":            "void",
        "font_size":        15,
        "zoom":             100,
        "javascript":       True,
        "images":           True,
        "adblock":          True,
        "dark_mode_force":  False,
        "reader_font":      "Georgia",
        "download_path":    str(Path.home() / "Downloads"),
        "show_bookmarks":   True,
        "hardware_accel":   True,
        "smooth_scroll":    True,
        "tab_preview":      True,
        "restore_tabs":     True,
        "user_agent":       "",
        "custom_css":       "",
        "sidebar_open":     False,
        "privacy_mode":     False,
        "open_tabs":        [],
    }

    def __init__(self):
        self._data: Dict = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._data.update(saved)
            except Exception:
                pass

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, fallback=None):
        return self._data.get(key, self.DEFAULTS.get(key, fallback))

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def toggle(self, key: str) -> bool:
        val = not self.get(key)
        self.set(key, val)
        return val


# ═════════════════════════════════════════════════════════════════════════════
#  HISTORY MANAGER
# ═════════════════════════════════════════════════════════════════════════════

class HistoryManager:
    MAX_ENTRIES = 2000

    def __init__(self):
        self._entries: List[Dict] = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = []

    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._entries[-self.MAX_ENTRIES:], f, indent=2)
        except Exception:
            pass

    def add(self, url: str, title: str):
        if not url or url == "about:blank":
            return
        entry = {
            "url":   url,
            "title": title or url,
            "time":  datetime.datetime.now().isoformat(),
            "ts":    time.time(),
        }
        self._entries.append(entry)
        self._save()

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [
            e for e in reversed(self._entries)
            if q in e.get("url", "").lower() or q in e.get("title", "").lower()
        ][:50]

    def recent(self, n: int = 20) -> List[Dict]:
        return list(reversed(self._entries[-n:]))

    def clear(self):
        self._entries = []
        self._save()

    def all(self) -> List[Dict]:
        return list(reversed(self._entries))


# ═════════════════════════════════════════════════════════════════════════════
#  BOOKMARKS MANAGER
# ═════════════════════════════════════════════════════════════════════════════

class BookmarksManager:
    def __init__(self):
        self._bookmarks: List[Dict] = []
        self._load()

    def _load(self):
        if BOOKMARKS_FILE.exists():
            try:
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    self._bookmarks = json.load(f)
            except Exception:
                self._bookmarks = []

    def _save(self):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._bookmarks, f, indent=2)
        except Exception:
            pass

    def add(self, url: str, title: str, folder: str = "") -> Dict:
        bm = {
            "id":     hashlib.md5(url.encode()).hexdigest()[:8],
            "url":    url,
            "title":  title or url,
            "folder": folder,
            "time":   datetime.datetime.now().isoformat(),
        }
        self._bookmarks.append(bm)
        self._save()
        return bm

    def remove(self, url: str):
        self._bookmarks = [b for b in self._bookmarks if b["url"] != url]
        self._save()

    def is_bookmarked(self, url: str) -> bool:
        return any(b["url"] == url for b in self._bookmarks)

    def get_all(self) -> List[Dict]:
        return list(self._bookmarks)

    def get_folders(self) -> List[str]:
        return sorted(set(b.get("folder", "") for b in self._bookmarks))

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [b for b in self._bookmarks
                if q in b.get("title","").lower() or q in b.get("url","").lower()]


# ═════════════════════════════════════════════════════════════════════════════
#  AD BLOCK INTERCEPTOR
# ═════════════════════════════════════════════════════════════════════════════

BLOCKED_DOMAINS = [
    "doubleclick.net", "googlesyndication.com", "adservice.google.com",
    "amazon-adsystem.com", "scorecardresearch.com", "taboola.com",
    "outbrain.com", "revcontent.com", "media.net", "bidvertiser.com",
    "adroll.com", "adsrvr.org", "criteo.com", "pubmatic.com",
    "openx.net", "rubiconproject.com", "contextweb.com", "adnxs.com",
    "advertising.com", "casalemedia.com", "quantserve.com",
    "chartbeat.com", "moatads.com", "adsafeprotected.com",
    "doubleverify.com", "2mdn.net", "googletagservices.com",
    "googletagmanager.com", "hotjar.com", "fullstory.com",
    "mouseflow.com", "luckyorange.com", "optimizely.com",
    "omtrdc.net", "demdex.net", "bluekai.com", "krxd.net",
    "exelator.com", "addthis.com", "sharethis.com",
]

BLOCKED_URL_PATTERNS = [
    "/ads/", "/ad/", "/advert", "/banner-ad", "/popup",
    "googleads", "adchoices", "/sponsored-", "/tracking/",
    "analytics.js", "/pixel.", "facebook.com/tr",
]

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._blocked_count = 0
        self.custom_domains: List[str] = []
        self.custom_patterns: List[str] = []

    @property
    def blocked_count(self) -> int:
        return self._blocked_count

    def interceptRequest(self, info):
        if not self._settings.get("adblock"):
            return
        url = info.requestUrl()
        host = url.host().lower()
        url_str = url.toString().lower()

        all_domains  = BLOCKED_DOMAINS  + self.custom_domains
        all_patterns = BLOCKED_URL_PATTERNS + self.custom_patterns

        for domain in all_domains:
            if domain and host.endswith(domain):
                info.block(True)
                self._blocked_count += 1
                return

        for pattern in all_patterns:
            if pattern and pattern in url_str:
                info.block(True)
                self._blocked_count += 1
                return


# ═════════════════════════════════════════════════════════════════════════════
#  ANIMATED LIQUID GLASS BACKGROUND
# ═════════════════════════════════════════════════════════════════════════════

class LiquidGlassBackground(QWidget):
    """
    Full-window animated background: deep ocean blues with slowly drifting
    luminous blobs and a fine grain overlay — the 'liquid' in liquid glass.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(33)   # ~30 fps for background
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # Pre-compute blob parameters so they're stable
        import random
        rng = random.Random(42)
        self._blobs = []
        configs = [
            (QColor( 60, 100, 220), 0.38, 0.008, 0.24, 0.20),
            (QColor(100,  60, 200), 0.32, 0.006, 0.65, 0.60),
            (QColor( 40, 130, 200), 0.28, 0.011, 0.50, 0.45),
            (QColor( 80,  40, 180), 0.24, 0.007, 0.15, 0.75),
            (QColor( 30, 160, 180), 0.20, 0.013, 0.80, 0.30),
            (QColor(120,  80, 220), 0.18, 0.009, 0.35, 0.80),
        ]
        for color, rad, speed, bx, by in configs:
            color.setAlpha(rng.randint(35, 60))
            self._blobs.append({
                "color": color,
                "rad":   rad,
                "speed": speed,
                "ox":    bx,
                "oy":    by,
                "px":    rng.uniform(0, math.pi * 2),
                "py":    rng.uniform(0, math.pi * 2),
                "mx":    rng.uniform(0.08, 0.18),
                "my":    rng.uniform(0.08, 0.16),
            })

    def _tick(self):
        self._t += 0.016
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        t = self._t

        # ── Solid base ──────────────────────────────────────────────────────
        p.fillRect(0, 0, w, h, Palette.VOID)

        # ── Gradient overlay ────────────────────────────────────────────────
        grad = QLinearGradient(0, 0, w * 0.6, h)
        grad.setColorAt(0.0, QColor(12, 16, 40, 180))
        grad.setColorAt(0.5, QColor( 8, 12, 28,  80))
        grad.setColorAt(1.0, QColor(14, 10, 35, 120))
        p.fillRect(0, 0, w, h, QBrush(grad))

        # ── Animated blobs ──────────────────────────────────────────────────
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for blob in self._blobs:
            cx = int((blob["ox"] + blob["mx"] * math.sin(t * blob["speed"] + blob["px"])) * w)
            cy = int((blob["oy"] + blob["my"] * math.cos(t * blob["speed"] * 0.7 + blob["py"])) * h)
            r  = int(blob["rad"] * max(w, h))
            rg = QRadialGradient(cx, cy, r)
            rg.setColorAt(0.0, blob["color"])
            edge = QColor(blob["color"])
            edge.setAlpha(0)
            rg.setColorAt(1.0, edge)
            p.fillRect(max(0, cx - r), max(0, cy - r),
                       min(w, cx + r) - max(0, cx - r),
                       min(h, cy + r) - max(0, cy - r),
                       QBrush(rg))

        # ── Scanline grain ──────────────────────────────────────────────────
        p.setPen(QPen(QColor(255, 255, 255, 3)))
        for y in range(0, h, 2):
            p.drawLine(0, y, w, y)

        # ── Subtle vignette ──────────────────────────────────────────────────
        vg = QRadialGradient(w // 2, h // 2, max(w, h) * 0.7)
        vg.setColorAt(0.0, QColor(0, 0, 0, 0))
        vg.setColorAt(1.0, QColor(0, 0, 0, 90))
        p.fillRect(0, 0, w, h, QBrush(vg))


# ═════════════════════════════════════════════════════════════════════════════
#  GLASS WIDGET — base for all frosted-glass UI elements
# ═════════════════════════════════════════════════════════════════════════════

class GlassWidget(QWidget):
    """
    Base widget that paints a frosted-glass rounded rectangle behind its content.
    Subclass and set _glass_radius, _glass_opacity, _glass_border.
    """
    _glass_radius:  int   = 14
    _glass_opacity: float = 1.0   # multiplier on fill alpha
    _glass_border:  bool  = True
    _glass_shine:   bool  = True

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_glass(p, self.rect())
        super().paintEvent(event)

    def _paint_glass(self, p: QPainter, rect: QRect, radius: int = None):
        r = radius if radius is not None else self._glass_radius
        rf = QRectF(rect)

        # Fill
        fill = QColor(255, 255, 255, int(18 * self._glass_opacity))
        p.setBrush(QBrush(fill))
        if self._glass_border:
            p.setPen(QPen(Palette.GLASS_BORDER, 1.0))
        else:
            p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rf.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

        # Shine highlight at top
        if self._glass_shine:
            shine = QLinearGradient(rf.left(), rf.top(), rf.left(), rf.top() + rf.height() * 0.4)
            shine.setColorAt(0.0, QColor(255, 255, 255, 30))
            shine.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(shine))
            p.setPen(Qt.PenStyle.NoPen)
            shine_rect = QRectF(rf.left(), rf.top(), rf.width(), rf.height() * 0.4)
            p.drawRoundedRect(shine_rect, r, r)


# ═════════════════════════════════════════════════════════════════════════════
#  GLASS BUTTON
# ═════════════════════════════════════════════════════════════════════════════

class GlassButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text: str = "", icon_text: str = "",
                 size: int = 36, radius: int = 18,
                 accent: QColor = None, parent=None):
        super().__init__(parent)
        self._text      = text
        self._icon_text = icon_text
        self._size      = size
        self._radius    = radius
        self._accent    = accent or Palette.BLUE
        self._hovered   = False
        self._pressed   = False
        self._enabled   = True
        self._checkable = False
        self._checked   = False
        self._tooltip   = ""
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def setToolTip(self, tip: str):
        self._tooltip = tip
        super().setToolTip(tip)

    def setText(self, text: str):
        self._text = text
        self.update()

    def text(self) -> str:
        return self._text

    def setCheckable(self, v: bool):
        self._checkable = v

    def setChecked(self, v: bool):
        self._checked = v
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def setEnabled(self, v: bool):
        self._enabled = v
        self.update()

    def isEnabled(self) -> bool:
        return self._enabled

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._enabled:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._enabled:
            was_pressed = self._pressed
            self._pressed = False
            if was_pressed and self.rect().contains(event.pos()):
                if self._checkable:
                    self._checked = not self._checked
                self.clicked.emit()
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r   = min(self._radius, self.width() // 2, self.height() // 2)
        rct = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

        # Background fill
        if self._pressed:
            alpha = 52
        elif self._hovered:
            alpha = 34
        elif self._checked:
            alpha = 44
        else:
            alpha = 16 if self._enabled else 8

        # Accent glow for checked/active state
        if (self._checked or self._pressed) and self._enabled:
            glow = QColor(self._accent)
            glow.setAlpha(60 if self._pressed else 45)
            p.setBrush(QBrush(glow))
            p.setPen(QPen(QColor(self._accent.red(), self._accent.green(),
                                 self._accent.blue(), 120), 1.0))
        else:
            p.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            border_alpha = 70 if self._hovered else 40
            if not self._enabled:
                border_alpha = 15
            p.setPen(QPen(QColor(255, 255, 255, border_alpha), 1.0))

        p.drawRoundedRect(rct, r, r)

        # Shine
        if self._hovered and self._enabled:
            shine = QLinearGradient(0, 0, 0, self.height() * 0.5)
            shine.setColorAt(0, QColor(255, 255, 255, 40))
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(shine))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(0.5, 0.5, self.width()-1, self.height()*0.5), r, r)

        # Label
        display = self._icon_text or self._text
        if display:
            alpha_text = 220 if self._enabled else 60
            if self._checked and self._enabled:
                p.setPen(QPen(QColor(self._accent.red(), self._accent.green(),
                                     self._accent.blue(), 255)))
            else:
                p.setPen(QPen(QColor(255, 255, 255, alpha_text)))
            font = QFont()
            font.setPixelSize(16 if len(display) == 1 else 13)
            p.setFont(font)
            p.drawText(rct, Qt.AlignmentFlag.AlignCenter, display)


# ═════════════════════════════════════════════════════════════════════════════
#  GLASS URL BAR
# ═════════════════════════════════════════════════════════════════════════════

class GlassUrlBar(QWidget):
    navigateRequested = pyqtSignal(str)
    searchRequested   = pyqtSignal(str)

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings  = settings
        self._hovered   = False
        self._focused   = False
        self._lock_icon = "🔒"
        self._is_secure = False
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        # Inner layout
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 4, 10, 4)
        lay.setSpacing(6)

        self._secure_label = QLabel()
        self._secure_label.setFixedWidth(18)
        self._secure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._secure_label)

        self._edit = QLineEdit()
        self._edit.setFrame(False)
        self._edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: rgba(235,240,255,220);
                font-size: 13px;
                selection-background-color: rgba(100,160,255,80);
            }
            QLineEdit::placeholder {
                color: rgba(140,155,195,140);
            }
        """)
        self._edit.setPlaceholderText("Search or enter address…")
        self._edit.returnPressed.connect(self._on_return)
        self._edit.focusInEvent  = self._on_focus_in
        self._edit.focusOutEvent = self._on_focus_out
        lay.addWidget(self._edit)

        self._reload_btn = GlassButton("↻", size=28, radius=14)
        self._reload_btn.setToolTip("Reload page")
        lay.addWidget(self._reload_btn)

        self.setUrl("")
        self.setSecure(False)

    def _on_focus_in(self, event):
        self._focused = True
        self._edit.selectAll()
        self.update()
        QLineEdit.focusInEvent(self._edit, event)

    def _on_focus_out(self, event):
        self._focused = False
        self.update()
        QLineEdit.focusOutEvent(self._edit, event)

    def _on_return(self):
        text = self._edit.text().strip()
        if not text:
            return
        if " " in text or ("." not in text and not text.startswith("localhost")):
            engine = self._settings.get("search_engine", DEFAULT_SEARCH)
            url = engine.format(text.replace(" ", "+"))
        elif "://" not in text:
            url = "https://" + text
        else:
            url = text
        self.navigateRequested.emit(url)

    def setUrl(self, url: str):
        if not self._focused:
            display = url if url not in ("about:blank", "") else ""
            self._edit.setText(display)
            self._edit.setCursorPosition(0)
        self.setSecure(url.startswith("https://"))

    def setSecure(self, secure: bool):
        self._is_secure = secure
        if secure:
            self._secure_label.setText("🔒")
            self._secure_label.setStyleSheet("color: rgba(80,220,140,200); font-size: 11px;")
        else:
            self._secure_label.setText("ⓘ")
            self._secure_label.setStyleSheet("color: rgba(140,155,195,140); font-size: 11px;")

    @property
    def reload_btn(self) -> GlassButton:
        return self._reload_btn

    def text(self) -> str:
        return self._edit.text()

    def setText(self, text: str):
        self._edit.setText(text)

    def focusEdit(self):
        self._edit.setFocus()
        self._edit.selectAll()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rct = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        r = 19.0

        if self._focused:
            fill_alpha  = 32
            border_col  = QColor(255, 255, 255, 90)
        elif self._hovered:
            fill_alpha  = 24
            border_col  = QColor(255, 255, 255, 60)
        else:
            fill_alpha  = 16
            border_col  = QColor(255, 255, 255, 38)

        p.setBrush(QBrush(QColor(255, 255, 255, fill_alpha)))
        p.setPen(QPen(border_col, 1.0))
        p.drawRoundedRect(rct, r, r)

        # Inner top shine
        shine = QLinearGradient(0, 0, 0, self.height() * 0.5)
        shine.setColorAt(0, QColor(255, 255, 255, 22))
        shine.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(shine))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width()-1, self.height()*0.5), r, r)

        # Focus ring
        if self._focused:
            p.setPen(QPen(QColor(100, 160, 255, 80), 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rct.adjusted(-1, -1, 1, 1), r + 1, r + 1)


# ═════════════════════════════════════════════════════════════════════════════
#  GLASS TAB BAR
# ═════════════════════════════════════════════════════════════════════════════

class GlassTabBar(QWidget):
    """Completely custom tab bar for the liquid-glass look."""
    tabSelected    = pyqtSignal(int)
    tabCloseReq    = pyqtSignal(int)
    newTabRequested= pyqtSignal()

    _TAB_MIN_W = 100
    _TAB_MAX_W = 220
    _TAB_H     = 38

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: List[Dict] = []   # [{title, url, loading, favicon_char}]
        self._current = -1
        self._hovered_tab  = -1
        self._hovered_close= -1
        self._drag_tab     = -1
        self._drag_start   = QPoint()
        self.setFixedHeight(self._TAB_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    # ── Public API ────────────────────────────────────────────────────────────
    def addTab(self, title: str = "New Tab") -> int:
        self._tabs.append({"title": title, "url": "", "loading": False, "favicon": "🌐"})
        idx = len(self._tabs) - 1
        self._current = idx
        self.update()
        return idx

    def removeTab(self, idx: int):
        if 0 <= idx < len(self._tabs):
            self._tabs.pop(idx)
            if self._current >= len(self._tabs):
                self._current = len(self._tabs) - 1
            self.update()

    def setTabTitle(self, idx: int, title: str):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]["title"] = title or "New Tab"
            self.update()

    def setTabUrl(self, idx: int, url: str):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]["url"] = url

    def setTabLoading(self, idx: int, loading: bool):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]["loading"] = loading
            self.update()

    def setCurrentIndex(self, idx: int):
        if 0 <= idx < len(self._tabs):
            self._current = idx
            self.update()
            self.tabSelected.emit(idx)

    def currentIndex(self) -> int:
        return self._current

    def count(self) -> int:
        return len(self._tabs)

    # ── Geometry helpers ──────────────────────────────────────────────────────
    def _tab_width(self) -> int:
        n = max(1, len(self._tabs))
        avail = self.width() - 36   # space for + button
        w = avail // n
        return max(self._TAB_MIN_W, min(self._TAB_MAX_W, w))

    def _tab_rect(self, idx: int) -> QRect:
        tw = self._tab_width()
        x  = idx * (tw + 2)
        return QRect(x, 2, tw, self._TAB_H - 4)

    def _close_rect(self, tab_rect: QRect) -> QRect:
        return QRect(tab_rect.right() - 20, tab_rect.top() + 10, 16, 16)

    def _new_tab_rect(self) -> QRect:
        n  = len(self._tabs)
        tw = self._tab_width()
        x  = n * (tw + 2) + 4
        return QRect(x, 6, 26, 26)

    # ── Events ────────────────────────────────────────────────────────────────
    def mouseMoveEvent(self, event):
        pos = event.pos()
        prev_ht  = self._hovered_tab
        prev_hc  = self._hovered_close
        self._hovered_tab   = -1
        self._hovered_close = -1

        for i in range(len(self._tabs)):
            tr = self._tab_rect(i)
            if tr.contains(pos):
                self._hovered_tab = i
                cr = self._close_rect(tr)
                if cr.contains(pos):
                    self._hovered_close = i
                break

        if prev_ht != self._hovered_tab or prev_hc != self._hovered_close:
            self.update()

    def mousePressEvent(self, event):
        pos = event.pos()
        if event.button() == Qt.MouseButton.LeftButton:
            ntr = self._new_tab_rect()
            if ntr.contains(pos):
                self.newTabRequested.emit()
                return
            for i in range(len(self._tabs)):
                tr = self._tab_rect(i)
                if tr.contains(pos):
                    cr = self._close_rect(tr)
                    if cr.contains(pos):
                        self.tabCloseReq.emit(i)
                    else:
                        self.setCurrentIndex(i)
                    return

    def leaveEvent(self, event):
        self._hovered_tab   = -1
        self._hovered_close = -1
        self.update()

    # ── Painting ──────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = time.time()

        for i, tab in enumerate(self._tabs):
            self._paint_tab(p, i, tab, t)

        # + New tab button
        ntr = self._new_tab_rect()
        is_nt_hov = self._new_tab_rect().contains(
            self.mapFromGlobal(QCursor.pos()))
        fill_a = 28 if is_nt_hov else 14
        p.setBrush(QBrush(QColor(255, 255, 255, fill_a)))
        p.setPen(QPen(QColor(255, 255, 255, 38), 1))
        p.drawRoundedRect(QRectF(ntr).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        p.setPen(QPen(QColor(255, 255, 255, 160 if is_nt_hov else 100)))
        f = QFont(); f.setPixelSize(17); f.setWeight(QFont.Weight.Light)
        p.setFont(f)
        p.drawText(QRectF(ntr), Qt.AlignmentFlag.AlignCenter, "+")

    def _paint_tab(self, p: QPainter, idx: int, tab: Dict, t: float):
        tr  = self._tab_rect(idx)
        rct = QRectF(tr).adjusted(0.5, 0.5, -0.5, -0.5)
        r   = 10.0
        is_current = (idx == self._current)
        is_hovered = (idx == self._hovered_tab)

        # Fill
        if is_current:
            fill_alpha = 30
            border_col = QColor(255, 255, 255, 60)
        elif is_hovered:
            fill_alpha = 20
            border_col = QColor(255, 255, 255, 45)
        else:
            fill_alpha = 10
            border_col = QColor(255, 255, 255, 22)

        p.setBrush(QBrush(QColor(255, 255, 255, fill_alpha)))
        p.setPen(QPen(border_col, 1.0))
        p.drawRoundedRect(rct, r, r)

        # Shine
        if is_current or is_hovered:
            shine = QLinearGradient(rct.left(), rct.top(), rct.left(), rct.top() + rct.height()*0.45)
            shine.setColorAt(0, QColor(255, 255, 255, 24))
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(shine))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(rct.left(), rct.top(), rct.width(), rct.height()*0.45), r, r)

        # Active underline
        if is_current:
            accent = QColor(100, 160, 255)
            ug = QLinearGradient(rct.left(), 0, rct.right(), 0)
            ug.setColorAt(0.0, QColor(100, 160, 255, 0))
            ug.setColorAt(0.5, accent)
            ug.setColorAt(1.0, QColor(100, 160, 255, 0))
            p.setBrush(QBrush(ug))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(rct.left() + 10, rct.bottom() - 3, rct.width() - 20, 3), 1.5, 1.5)

        # Favicon / spinner
        p.setPen(QPen(QColor(255, 255, 255, 160)))
        fav_f = QFont(); fav_f.setPixelSize(12)
        p.setFont(fav_f)
        if tab.get("loading"):
            # Simple spinning arc
            spinner_angle = int((t * 360) % 360)
            p.save()
            p.translate(tr.left() + 14, tr.top() + tr.height() // 2)
            arc_pen = QPen(Palette.BLUE, 2.0)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRect(-6, -6, 12, 12), spinner_angle * 16, 120 * 16)
            p.restore()
        else:
            fav = tab.get("favicon", "🌐")
            p.drawText(QRect(tr.left() + 6, tr.top(), 22, tr.height()), Qt.AlignmentFlag.AlignCenter, fav)

        # Title
        text_col = QColor(235, 240, 255, 220 if is_current else 160)
        p.setPen(QPen(text_col))
        title_f = QFont()
        title_f.setPixelSize(12)
        if is_current:
            title_f.setWeight(QFont.Weight.Medium)
        p.setFont(title_f)
        title_rect = QRect(tr.left() + 28, tr.top(), tr.width() - 50, tr.height())
        elided = QFontMetrics(title_f).elidedText(
            tab.get("title", "New Tab"), Qt.TextElideMode.ElideRight, title_rect.width())
        p.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

        # Close button
        show_close = is_current or is_hovered
        if show_close:
            cr   = self._close_rect(tr)
            hc   = (idx == self._hovered_close)
            if hc:
                p.setBrush(QBrush(QColor(255, 80, 100, 80)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(cr)
            close_col = QColor(255, 255, 255, 200 if hc else 120)
            p.setPen(QPen(close_col, 1.5))
            m = 4
            p.drawLine(cr.left()+m, cr.top()+m, cr.right()-m, cr.bottom()-m)
            p.drawLine(cr.right()-m, cr.top()+m, cr.left()+m, cr.bottom()-m)


# ═════════════════════════════════════════════════════════════════════════════
#  TOOLBAR
# ═════════════════════════════════════════════════════════════════════════════

class BrowserToolbar(GlassWidget):
    _glass_radius  = 0
    _glass_shine   = False
    _glass_border  = False
    _glass_opacity = 0.5

    backRequested    = pyqtSignal()
    forwardRequested = pyqtSignal()
    reloadRequested  = pyqtSignal()
    stopRequested    = pyqtSignal()
    homeRequested    = pyqtSignal()
    newTabRequested  = pyqtSignal()
    gameRequested    = pyqtSignal()
    sidebarToggled   = pyqtSignal()
    settingsRequested= pyqtSignal()
    bookmarkToggled  = pyqtSignal()
    navigateRequested= pyqtSignal(str)

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings  = settings
        self._is_loading = False
        self.setFixedHeight(56)
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 9, 12, 7)
        lay.setSpacing(6)

        # Traffic-light style spacer (macOS feel)
        tl_spacer = QWidget()
        tl_spacer.setFixedWidth(4)
        lay.addWidget(tl_spacer)

        # Navigation buttons
        self.btn_back    = GlassButton("‹",  size=36, radius=18)
        self.btn_forward = GlassButton("›",  size=36, radius=18)
        self.btn_reload  = GlassButton("↻",  size=36, radius=18)

        self.btn_back.setToolTip("Go back  (Alt+Left)")
        self.btn_forward.setToolTip("Go forward  (Alt+Right)")
        self.btn_reload.setToolTip("Reload page  (Ctrl+R)")

        self.btn_back.clicked.connect(self.backRequested)
        self.btn_forward.clicked.connect(self.forwardRequested)
        self.btn_reload.clicked.connect(self._on_reload_click)

        lay.addWidget(self.btn_back)
        lay.addWidget(self.btn_forward)
        lay.addWidget(self.btn_reload)
        lay.addSpacing(4)

        # URL bar
        self.url_bar = GlassUrlBar(self._settings, self)
        self.url_bar.navigateRequested.connect(self.navigateRequested)
        lay.addWidget(self.url_bar)
        lay.addSpacing(4)

        # Right side buttons
        self.btn_bookmark = GlassButton("★", size=36, radius=18, accent=Palette.AMBER)
        self.btn_bookmark.setCheckable(True)
        self.btn_bookmark.setToolTip("Bookmark this page  (Ctrl+D)")
        self.btn_bookmark.clicked.connect(self.bookmarkToggled)

        self.btn_game = GlassButton("🎮", size=36, radius=18, accent=Palette.PURPLE)
        self.btn_game.setToolTip("Open game")
        self.btn_game.clicked.connect(self.gameRequested)

        self.btn_settings = GlassButton("⚙", size=36, radius=18)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.settingsRequested)

        self.btn_sidebar = GlassButton("☰", size=36, radius=18)
        self.btn_sidebar.setCheckable(True)
        self.btn_sidebar.setToolTip("Sidebar  (Ctrl+B)")
        self.btn_sidebar.clicked.connect(self.sidebarToggled)

        for b in [self.btn_bookmark, self.btn_game, self.btn_settings, self.btn_sidebar]:
            lay.addWidget(b)

    def _on_reload_click(self):
        if self._is_loading:
            self.stopRequested.emit()
        else:
            self.reloadRequested.emit()

    def set_loading(self, loading: bool):
        self._is_loading = loading
        self.btn_reload.setText("✕" if loading else "↻")
        self.btn_reload.setToolTip("Stop loading" if loading else "Reload page  (Ctrl+R)")

    def set_can_go_back(self, v: bool):
        self.btn_back.setEnabled(v)

    def set_can_go_forward(self, v: bool):
        self.btn_forward.setEnabled(v)

    def set_bookmarked(self, v: bool):
        self.btn_bookmark.setChecked(v)

    def paintEvent(self, event):
        p = QPainter(self)
        # Bottom glass toolbar fill
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(255, 255, 255, 14))
        grad.setColorAt(1.0, QColor(255, 255, 255, 6))
        p.fillRect(self.rect(), QBrush(grad))
        # Bottom border
        p.setPen(QPen(QColor(255, 255, 255, 22)))
        p.drawLine(0, self.height()-1, self.width(), self.height()-1)


# ═════════════════════════════════════════════════════════════════════════════
#  LOAD PROGRESS BAR
# ═════════════════════════════════════════════════════════════════════════════

class GlassProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self._value = 0
        self._visible_val = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._animate)
        self.hide()

    def setValue(self, v: int):
        self._value = v
        if not self._anim_timer.isActive():
            self._anim_timer.start()
        if v >= 100:
            QTimer.singleShot(400, self._finish)

    def _animate(self):
        target = float(self._value)
        self._visible_val += (target - self._visible_val) * 0.15
        if abs(self._visible_val - target) < 0.5:
            self._visible_val = target
        self.update()

    def _finish(self):
        self._anim_timer.stop()
        self.hide()
        self._visible_val = 0
        self._value = 0

    def start(self):
        self._value = 10
        self._visible_val = 0.0
        self.show()
        self._anim_timer.start()

    def paintEvent(self, event):
        p = QPainter(self)
        w = self.width()
        filled = int(w * self._visible_val / 100.0)

        # Track
        p.fillRect(0, 0, w, self.height(), QColor(255, 255, 255, 15))

        # Fill gradient
        if filled > 0:
            grad = QLinearGradient(0, 0, filled, 0)
            grad.setColorAt(0.0, QColor( 60, 140, 255))
            grad.setColorAt(0.6, QColor(100, 180, 255))
            grad.setColorAt(1.0, QColor(180, 220, 255))
            p.fillRect(0, 0, filled, self.height(), QBrush(grad))

            # Shine dot at leading edge
            if filled > 4:
                glow = QRadialGradient(filled, 1, 8)
                glow.setColorAt(0, QColor(220, 240, 255, 200))
                glow.setColorAt(1, QColor(220, 240, 255, 0))
                p.fillRect(filled-8, 0, 16, self.height(), QBrush(glow))


# ═════════════════════════════════════════════════════════════════════════════
#  SPEED DIAL (new tab page)
# ═════════════════════════════════════════════════════════════════════════════

SPEED_DIAL_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>New Tab</title>
<style>
:root {
  --glass: rgba(255,255,255,0.08);
  --glass-border: rgba(255,255,255,0.14);
  --glass-hover: rgba(255,255,255,0.14);
  --text: rgba(220,230,255,0.90);
  --text-dim: rgba(140,155,200,0.70);
  --accent: rgba(100,160,255,1);
  --bg: #08090f;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: radial-gradient(ellipse 80% 80% at 30% 30%, #0a1228 0%, #060810 60%, #040609 100%);
  min-height:100vh; display:flex; flex-direction:column;
  align-items:center; justify-content:center; overflow:hidden;
  font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', sans-serif;
  color: var(--text);
}
.blobs { position:fixed; inset:0; pointer-events:none; overflow:hidden; }
.blob {
  position:absolute; border-radius:50%; filter:blur(80px);
  animation: drift 20s ease-in-out infinite alternate;
}
.blob1 { width:500px;height:500px; background:rgba(60,100,220,0.18);
          top:-100px;left:-100px; animation-delay:0s; }
.blob2 { width:400px;height:400px; background:rgba(100,60,200,0.14);
          bottom:-80px;right:-80px; animation-delay:-7s; }
.blob3 { width:300px;height:300px; background:rgba(40,130,200,0.12);
          top:40%;left:60%; animation-delay:-14s; }
@keyframes drift {
  from { transform: translate(0,0) scale(1); }
  to   { transform: translate(40px,30px) scale(1.1); }
}
.center { position:relative; z-index:10; width:100%; max-width:760px;
          display:flex; flex-direction:column; align-items:center; gap:40px;
          padding: 40px 20px; }
.greeting { text-align:center; }
.greeting h1 {
  font-size: 2.2em; font-weight:300; letter-spacing:0.04em;
  background: linear-gradient(135deg, rgba(200,220,255,0.95) 0%, rgba(140,170,255,0.80) 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
}
.greeting .sub { color:var(--text-dim); font-size:0.85em; margin-top:6px; font-weight:300; }

.search-wrap {
  width:100%; max-width:560px;
  background:var(--glass); border:1px solid var(--glass-border);
  border-radius:28px; padding:14px 22px;
  backdrop-filter:blur(20px); display:flex; align-items:center; gap:10px;
  transition: all 0.2s ease;
}
.search-wrap:focus-within {
  background:rgba(255,255,255,0.12); border-color:rgba(255,255,255,0.28);
  box-shadow: 0 0 0 3px rgba(100,160,255,0.12);
}
.search-wrap input {
  flex:1; background:transparent; border:none; outline:none;
  color:var(--text); font-size:15px; font-weight:300;
}
.search-wrap input::placeholder { color:var(--text-dim); }
.search-icon { color:var(--text-dim); font-size:16px; }

.sites { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; width:100%; }
.site-card {
  background:var(--glass); border:1px solid var(--glass-border);
  border-radius:16px; padding:20px 12px; text-align:center; cursor:pointer;
  transition: all 0.18s ease; text-decoration:none; color:var(--text);
  backdrop-filter:blur(12px); display:flex; flex-direction:column;
  align-items:center; gap:8px;
}
.site-card:hover {
  background:var(--glass-hover); border-color:rgba(255,255,255,0.24);
  transform:translateY(-3px);
  box-shadow:0 12px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.10);
}
.site-card .icon { font-size:26px; line-height:1; }
.site-card .name { font-size:12px; font-weight:400; color:var(--text-dim); }

.clock { font-size:4.5em; font-weight:200; letter-spacing:-0.02em;
         color:rgba(210,225,255,0.85); text-shadow:0 0 60px rgba(100,160,255,0.15); }
.date-str { color:var(--text-dim); font-size:0.88em; font-weight:300; letter-spacing:0.06em; }
</style>
</head>
<body>
<div class="blobs">
  <div class="blob blob1"></div>
  <div class="blob blob2"></div>
  <div class="blob blob3"></div>
</div>
<div class="center">
  <div id="clock" class="clock">00:00</div>
  <div id="datestr" class="date-str">LOADING...</div>
  <div class="greeting">
    <h1 id="greet">Good morning</h1>
    <div class="sub">Where would you like to go today?</div>
  </div>
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="searchInput" placeholder="Search the web or enter a URL…" autocomplete="off">
  </div>
  <div class="sites">
    <a class="site-card" href="https://www.google.com">
      <div class="icon">🌐</div><div class="name">Google</div></a>
    <a class="site-card" href="https://www.youtube.com">
      <div class="icon">▶️</div><div class="name">YouTube</div></a>
    <a class="site-card" href="https://github.com">
      <div class="icon">🐙</div><div class="name">GitHub</div></a>
    <a class="site-card" href="https://www.reddit.com">
      <div class="icon">🟠</div><div class="name">Reddit</div></a>
    <a class="site-card" href="https://twitter.com">
      <div class="icon">𝕏</div><div class="name">X / Twitter</div></a>
    <a class="site-card" href="https://www.wikipedia.org">
      <div class="icon">📖</div><div class="name">Wikipedia</div></a>
    <a class="site-card" href="https://www.twitch.tv">
      <div class="icon">💜</div><div class="name">Twitch</div></a>
    <a class="site-card" href="https://news.ycombinator.com">
      <div class="icon">🔶</div><div class="name">Hacker News</div></a>
  </div>
</div>
<script>
function tick() {
  const now = new Date();
  const h = now.getHours(), m = now.getMinutes();
  document.getElementById('clock').textContent =
    String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0');
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  document.getElementById('datestr').textContent =
    days[now.getDay()].toUpperCase() + ', ' +
    months[now.getMonth()].toUpperCase() + ' ' + now.getDate();
  const greets = [
    [5, 'Good morning'],  [12, 'Good afternoon'],
    [17, 'Good evening'], [21, 'Good night'],
  ];
  let g = 'Good evening';
  for (const [hour, text] of greets) { if (h >= hour) g = text; }
  document.getElementById('greet').textContent = g;
}
tick(); setInterval(tick, 10000);

document.getElementById('searchInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const val = e.target.value.trim();
    if (!val) return;
    const isUrl = val.startsWith('http://') || val.startsWith('https://') || (val.includes('.') && !val.includes(' '));
    window.location.href = isUrl
      ? (val.startsWith('http') ? val : 'https://' + val)
      : 'https://www.google.com/search?q=' + encodeURIComponent(val);
  }
});
document.getElementById('searchInput').focus();
</script>
</body></html>"""


# ═════════════════════════════════════════════════════════════════════════════
#  GAME HTML — built-in Asteroids
# ═════════════════════════════════════════════════════════════════════════════

GAME_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Winternet Arcade</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background:#050810; display:flex; flex-direction:column;
  align-items:center; justify-content:center; height:100vh; overflow:hidden;
  font-family:'SF Mono','Courier New',monospace; color:rgba(200,220,255,0.85);
  user-select:none;
}
h1 { font-size:1.4em; font-weight:300; letter-spacing:0.35em; margin-bottom:4px;
     color:rgba(180,210,255,0.90); text-shadow:0 0 30px rgba(100,160,255,0.50); }
.sub { font-size:0.68em; letter-spacing:0.18em; color:rgba(100,130,180,0.70); margin-bottom:16px; }
canvas {
  border-radius:14px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.08),
              0 20px 80px rgba(0,0,0,0.6),
              0 0 60px rgba(60,120,255,0.12);
}
.hud {
  margin-top:14px; display:flex; gap:36px; font-size:0.78em;
  color:rgba(100,130,180,0.80); letter-spacing:0.12em;
}
.hud span { color:rgba(180,210,255,0.90); font-size:1.1em; }
.ctrl { margin-top:10px; font-size:0.66em; color:rgba(80,100,150,0.70);
        letter-spacing:0.08em; }
</style>
</head>
<body>
<h1>A·S·T·E·R·O·I·D·S</h1>
<div class="sub">WINTERNET ARCADE  ·  v2.0</div>
<canvas id="c" width="720" height="460"></canvas>
<div class="hud">
  SCORE <span id="sc">0</span> &nbsp; LIVES <span id="li">3</span> &nbsp; LEVEL <span id="lv">1</span>
</div>
<div class="ctrl">ARROWS / WASD · move &nbsp;|&nbsp; SPACE · shoot &nbsp;|&nbsp; R · restart</div>
<script>
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
let W=720,H=460, ship,bullets,asteroids,particles,score,lives,level,running,keys={},raf,lastT=0;

function rng(a,b){return a+Math.random()*(b-a);}

function init(keepLevel){
  if(!keepLevel){score=0;lives=3;level=1;}
  ship={x:W/2,y:H/2,angle:-Math.PI/2,vx:0,vy:0,r:13,inv:180,thrusting:false,dead:false};
  bullets=[];asteroids=[];particles=[];running=true;
  const n=3+level;
  for(let i=0;i<n;i++) spawnAsteroid(46);
  sync();
}

function sync(){
  document.getElementById('sc').textContent=score;
  document.getElementById('li').textContent=lives;
  document.getElementById('lv').textContent=level;
}

function spawnAsteroid(r,x,y){
  const a=rng(0,Math.PI*2), spd=rng(0.6,1.5+level*0.12);
  const pts=Math.floor(rng(6,11));
  const shape=[];
  for(let i=0;i<pts;i++) shape.push(rng(0.65,1.0));
  asteroids.push({
    x:x??( Math.random()<0.5 ? rng(-50,150) : rng(W-150,W+50)),
    y:y??( Math.random()<0.5 ? rng(-50,100) : rng(H-100,H+50)),
    vx:Math.cos(a)*spd, vy:Math.sin(a)*spd,
    r, rot:0, rotSpd:rng(-0.025,0.025), pts, shape
  });
}

function spawnParticles(x,y,col,n,fast){
  for(let i=0;i<n;i++){
    const a=rng(0,Math.PI*2), s=rng(fast?2:0.8, fast?5:3);
    particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s,
      life:rng(20,50), maxLife:50, col, r:rng(1,3)});
  }
}

function wrap(v,max){return(v%max+max)%max;}

function update(dt){
  if(!running)return;
  const s=ship;
  if(keys['ArrowLeft']||keys['a'])s.angle-=0.065;
  if(keys['ArrowRight']||keys['d'])s.angle+=0.065;
  s.thrusting=!!(keys['ArrowUp']||keys['w']);
  if(s.thrusting){s.vx+=Math.cos(s.angle)*0.20;s.vy+=Math.sin(s.angle)*0.20;}
  s.vx*=0.986; s.vy*=0.986;
  s.x=wrap(s.x+s.vx,W); s.y=wrap(s.y+s.vy,H);
  if(s.inv>0) s.inv-=dt*60;

  bullets=bullets.filter(b=>{
    b.x+=b.vx; b.y+=b.vy; b.life-=dt*60;
    return b.life>0&&b.x>-10&&b.x<W+10&&b.y>-10&&b.y<H+10;
  });

  asteroids.forEach(a=>{
    a.x=wrap(a.x+a.vx,W); a.y=wrap(a.y+a.vy,H); a.rot+=a.rotSpd;
  });

  // Bullet vs asteroid
  for(let bi=bullets.length-1;bi>=0;bi--){
    const b=bullets[bi];
    for(let ai=asteroids.length-1;ai>=0;ai--){
      const a=asteroids[ai];
      if(Math.hypot(b.x-a.x,b.y-a.y)<a.r){
        score+=Math.round(400/a.r); sync();
        spawnParticles(a.x,a.y,'rgba(120,190,255,0.9)',8,false);
        bullets.splice(bi,1);
        if(a.r>18){spawnAsteroid(a.r*0.52,a.x+rng(-10,10),a.y+rng(-10,10));
                   spawnAsteroid(a.r*0.52,a.x+rng(-10,10),a.y+rng(-10,10));}
        asteroids.splice(ai,1);
        break;
      }
    }
  }

  // Ship vs asteroid
  if(s.inv<=0&&!s.dead){
    for(const a of asteroids){
      if(Math.hypot(s.x-a.x,s.y-a.y)<a.r+s.r-3){
        lives--; sync();
        spawnParticles(s.x,s.y,'rgba(255,160,80,0.95)',20,true);
        spawnParticles(s.x,s.y,'rgba(255,220,100,0.80)',10,false);
        s.x=W/2; s.y=H/2; s.vx=0; s.vy=0; s.inv=200;
        if(lives<=0){running=false;}
        break;
      }
    }
  }

  particles=particles.filter(p=>{
    p.x+=p.vx; p.y+=p.vy; p.vx*=0.92; p.vy*=0.92; p.life--;
    return p.life>0;
  });

  if(asteroids.length===0){
    level++; sync();
    for(let i=0;i<3+level;i++) spawnAsteroid(46);
  }
}

function draw(t){
  ctx.fillStyle='rgba(4,6,16,0.88)';
  ctx.fillRect(0,0,W,H);

  // Stars
  for(let i=0;i<90;i++){
    const x=(i*137.508)%W, y=(i*97.31)%H;
    const b=0.1+((i*31)%10)*0.06;
    ctx.globalAlpha=b*(0.8+0.2*Math.sin(t*0.001+i));
    ctx.fillStyle='#fff';
    ctx.fillRect(x,y,1,1);
  }
  ctx.globalAlpha=1;

  // Particles
  particles.forEach(p=>{
    ctx.globalAlpha=p.life/p.maxLife;
    ctx.fillStyle=p.col;
    ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();
  });
  ctx.globalAlpha=1;

  // Asteroids
  asteroids.forEach(a=>{
    ctx.save();ctx.translate(a.x,a.y);ctx.rotate(a.rot);
    ctx.strokeStyle='rgba(160,200,255,0.65)'; ctx.lineWidth=1.5;
    ctx.shadowBlur=10; ctx.shadowColor='rgba(80,150,255,0.35)';
    ctx.beginPath();
    for(let i=0;i<=a.pts;i++){
      const ang=(i/a.pts)*Math.PI*2;
      const r=a.r*a.shape[i%a.pts];
      i===0?ctx.moveTo(Math.cos(ang)*r,Math.sin(ang)*r)
           :ctx.lineTo(Math.cos(ang)*r,Math.sin(ang)*r);
    }
    ctx.closePath();ctx.stroke();
    ctx.shadowBlur=0; ctx.restore();
  });

  // Ship
  const s=ship;
  if(running||(s.inv>0&&Math.floor(t/80)%2===0)){
    ctx.save();ctx.translate(s.x,s.y);ctx.rotate(s.angle);
    ctx.shadowBlur=18; ctx.shadowColor='rgba(100,180,255,0.7)';
    ctx.strokeStyle='rgba(190,220,255,0.92)'; ctx.lineWidth=1.8;
    ctx.beginPath();ctx.moveTo(18,0);ctx.lineTo(-11,-9);ctx.lineTo(-7,0);ctx.lineTo(-11,9);ctx.closePath();ctx.stroke();
    if(s.thrusting&&Math.random()>0.3){
      const fl=12+Math.random()*10;
      ctx.strokeStyle='rgba(255,160,60,0.85)'; ctx.lineWidth=2;
      ctx.beginPath();ctx.moveTo(-7,0);ctx.lineTo(-7-fl,0);ctx.stroke();
      ctx.strokeStyle='rgba(255,220,80,0.50)'; ctx.lineWidth=1;
      ctx.beginPath();ctx.moveTo(-7,-3);ctx.lineTo(-7-fl*0.7+Math.random()*4,0);ctx.stroke();
      ctx.beginPath();ctx.moveTo(-7, 3);ctx.lineTo(-7-fl*0.7+Math.random()*4,0);ctx.stroke();
    }
    ctx.shadowBlur=0; ctx.restore();
  }

  // Bullets
  bullets.forEach(b=>{
    ctx.save();
    ctx.shadowBlur=12; ctx.shadowColor='rgba(180,230,255,0.9)';
    ctx.fillStyle='rgba(210,235,255,0.95)';
    ctx.beginPath();ctx.arc(b.x,b.y,2.8,0,Math.PI*2);ctx.fill();
    ctx.shadowBlur=0; ctx.restore();
  });

  // Game over
  if(!running){
    ctx.fillStyle='rgba(0,0,0,0.55)'; ctx.fillRect(0,0,W,H);
    ctx.save(); ctx.translate(W/2,H/2);
    ctx.shadowBlur=30; ctx.shadowColor='rgba(100,160,255,0.5)';
    ctx.fillStyle='rgba(220,235,255,0.95)';
    ctx.font='300 34px "Helvetica Neue",sans-serif';
    ctx.textAlign='center'; ctx.fillText('GAME OVER',0,-24);
    ctx.font='300 14px "SF Mono","Courier New",monospace';
    ctx.fillStyle='rgba(130,155,200,0.80)'; ctx.shadowBlur=0;
    ctx.fillText('SCORE   '+score,0,16);
    ctx.fillText('PRESS  R  TO RESTART',0,44);
    ctx.textAlign='left'; ctx.restore();
  }
}

function loop(t){
  const dt=Math.min((t-lastT)/1000,0.05); lastT=t;
  update(dt); draw(t);
  raf=requestAnimationFrame(loop);
}

document.addEventListener('keydown',e=>{
  keys[e.key]=true;
  if(e.key===' '&&running&&bullets.length<7){
    const s=ship;
    bullets.push({
      x:s.x+Math.cos(s.angle)*19, y:s.y+Math.sin(s.angle)*19,
      vx:Math.cos(s.angle)*11+s.vx, vy:Math.sin(s.angle)*11+s.vy, life:70
    });
    e.preventDefault();
  }
  if(e.key==='r'||e.key==='R'){cancelAnimationFrame(raf);init(false);requestAnimationFrame(loop);}
});
document.addEventListener('keyup',e=>{keys[e.key]=false;});
init(false); requestAnimationFrame(loop);
</script>
</body></html>"""


# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

class Sidebar(GlassWidget):
    _glass_radius  = 0
    _glass_opacity = 0.6
    _glass_border  = False
    _glass_shine   = False

    pageRequested  = pyqtSignal(str)
    closed         = pyqtSignal()

    _PAGES = ["History", "Bookmarks", "Downloads", "Settings"]

    def __init__(self, settings: SettingsManager,
                 history: HistoryManager,
                 bookmarks: BookmarksManager,
                 parent=None):
        super().__init__(parent)
        self._settings  = settings
        self._history   = history
        self._bookmarks = bookmarks
        self.setFixedWidth(310)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(52)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 12, 0)
        title = QLabel("Winternet")
        title.setStyleSheet("color: rgba(200,220,255,0.90); font-size:15px; font-weight:500;")
        hl.addWidget(title)
        hl.addStretch()
        close_btn = GlassButton("✕", size=28, radius=14)
        close_btn.clicked.connect(self.closed)
        hl.addWidget(close_btn)
        lay.addWidget(header)

        # Page switcher
        tabs_row = QWidget()
        tabs_row.setFixedHeight(38)
        tr_lay = QHBoxLayout(tabs_row)
        tr_lay.setContentsMargins(12, 4, 12, 4)
        tr_lay.setSpacing(4)
        self._tab_btns = []
        for page in self._PAGES:
            btn = GlassButton(page[:4] if page != "Downloads" else "DL",
                              size=32, radius=8)
            btn.setFixedSize(58, 28)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, p=page: self._show_page(p))
            self._tab_btns.append((page, btn))
            tr_lay.addWidget(btn)
        tr_lay.addStretch()
        lay.addWidget(tabs_row)

        # Stack
        self._stack = QStackedWidget()
        self._pages: Dict[str, QWidget] = {}

        self._pages["History"]   = self._build_history_page()
        self._pages["Bookmarks"] = self._build_bookmarks_page()
        self._pages["Downloads"] = self._build_downloads_page()
        self._pages["Settings"]  = self._build_settings_page()

        for w in self._pages.values():
            self._stack.addWidget(w)

        lay.addWidget(self._stack)
        self._show_page("History")

    def _show_page(self, name: str):
        if name in self._pages:
            self._stack.setCurrentWidget(self._pages[name])
        for pname, btn in self._tab_btns:
            btn.setChecked(pname == name)
        if name == "History":
            self._refresh_history()
        elif name == "Bookmarks":
            self._refresh_bookmarks()

    # ── History page ──────────────────────────────────────────────────────────
    def _build_history_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(8)

        search = QLineEdit()
        search.setPlaceholderText("Search history…")
        search.setStyleSheet(self._input_style())
        search.textChanged.connect(self._filter_history)
        lay.addWidget(search)
        self._history_search = search

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }"
                             "QScrollBar:vertical { background:transparent; width:5px; }"
                             "QScrollBar::handle:vertical { background:rgba(255,255,255,0.20); border-radius:2px; }")
        self._history_container = QWidget()
        self._history_container.setStyleSheet("background:transparent;")
        self._history_layout = QVBoxLayout(self._history_container)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(3)
        self._history_layout.addStretch()
        scroll.setWidget(self._history_container)
        lay.addWidget(scroll)

        clear_btn = self._make_action_btn("🗑  Clear History", danger=True)
        clear_btn.clicked.connect(self._clear_history)
        lay.addWidget(clear_btn)
        return w

    def _refresh_history(self, query: str = ""):
        lay = self._history_layout
        # Remove old items (keep stretch)
        while lay.count() > 1:
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._history.search(query) if query else self._history.recent(60)
        for e in entries:
            row = self._make_list_row(e.get("title", e["url"])[:42], e["url"],
                                      e.get("time", "")[:16].replace("T", "  "))
            row.clicked.connect(lambda _, u=e["url"]: self.pageRequested.emit(u))
            lay.insertWidget(lay.count() - 1, row)

    def _filter_history(self, text: str):
        self._refresh_history(text)

    def _clear_history(self):
        self._history.clear()
        self._refresh_history()

    # ── Bookmarks page ────────────────────────────────────────────────────────
    def _build_bookmarks_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(8)

        search = QLineEdit()
        search.setPlaceholderText("Search bookmarks…")
        search.setStyleSheet(self._input_style())
        search.textChanged.connect(self._filter_bookmarks)
        lay.addWidget(search)
        self._bm_search = search

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }"
                             "QScrollBar:vertical { background:transparent; width:5px; }"
                             "QScrollBar::handle:vertical { background:rgba(255,255,255,0.20); border-radius:2px; }")
        self._bm_container = QWidget()
        self._bm_container.setStyleSheet("background:transparent;")
        self._bm_layout = QVBoxLayout(self._bm_container)
        self._bm_layout.setContentsMargins(0, 0, 0, 0)
        self._bm_layout.setSpacing(3)
        self._bm_layout.addStretch()
        scroll.setWidget(self._bm_container)
        lay.addWidget(scroll)
        return w

    def _refresh_bookmarks(self, query: str = ""):
        lay = self._bm_layout
        while lay.count() > 1:
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._bookmarks.search(query) if query else self._bookmarks.get_all()
        for b in entries:
            row = self._make_list_row(b.get("title", b["url"])[:42], b["url"])
            row.clicked.connect(lambda _, u=b["url"]: self.pageRequested.emit(u))
            lay.insertWidget(lay.count() - 1, row)

    def _filter_bookmarks(self, text: str):
        self._refresh_bookmarks(text)

    # ── Downloads page ────────────────────────────────────────────────────────
    def _build_downloads_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(8)
        lbl = QLabel("Downloads")
        lbl.setStyleSheet("color:rgba(200,220,255,0.60); font-size:13px;")
        lay.addWidget(lbl)
        info = QLabel("Downloaded files will appear here.")
        info.setStyleSheet("color:rgba(130,150,190,0.60); font-size:12px;")
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addStretch()
        return w

    # ── Settings page ─────────────────────────────────────────────────────────
    def _build_settings_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(12)

        def section(title: str) -> QLabel:
            lbl = QLabel(title)
            lbl.setStyleSheet("color:rgba(100,160,255,0.90); font-size:11px; "
                              "font-weight:600; letter-spacing:0.08em; margin-top:6px;")
            return lbl

        def toggle_row(label: str, key: str) -> QWidget:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label)
            lbl.setStyleSheet("color:rgba(200,220,255,0.80); font-size:12px;")
            cb = QCheckBox()
            cb.setChecked(self._settings.get(key, True))
            cb.setStyleSheet("""
                QCheckBox::indicator { width:18px; height:18px; border-radius:9px;
                    background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25); }
                QCheckBox::indicator:checked { background:rgba(100,160,255,0.80);
                    border-color:rgba(100,160,255,0.90); }
            """)
            cb.stateChanged.connect(lambda v, k=key: self._settings.set(k, bool(v)))
            rl.addWidget(lbl); rl.addStretch(); rl.addWidget(cb)
            row.setStyleSheet("background:rgba(255,255,255,0.05); border-radius:8px; padding:6px 10px;")
            return row

        lay.addWidget(section("BROWSING"))
        lay.addWidget(toggle_row("JavaScript",   "javascript"))
        lay.addWidget(toggle_row("Load Images",  "images"))
        lay.addWidget(toggle_row("Ad Blocker",   "adblock"))
        lay.addWidget(toggle_row("Smooth Scroll","smooth_scroll"))

        lay.addWidget(section("APPEARANCE"))
        lay.addWidget(toggle_row("Bookmarks Bar","show_bookmarks"))

        lay.addWidget(section("PRIVACY"))
        lay.addWidget(toggle_row("Private Mode", "privacy_mode"))

        lay.addStretch()

        version_lbl = QLabel(f"Winternet {APP_VERSION}")
        version_lbl.setStyleSheet("color:rgba(80,100,150,0.60); font-size:10px; margin-top:4px;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(version_lbl)
        return w

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _input_style(self) -> str:
        return """
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
                padding: 7px 12px;
                color: rgba(210,225,255,0.90);
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: rgba(100,160,255,0.50);
                background: rgba(255,255,255,0.12);
            }
        """

    def _make_list_row(self, title: str, subtitle: str, meta: str = "") -> QPushButton:
        btn = QPushButton()
        btn.setFixedHeight(52 if meta else 44)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                text-align: left;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.10);
                border-color: rgba(255,255,255,0.16);
            }
        """)
        inner = QVBoxLayout(btn)
        inner.setContentsMargins(6, 4, 6, 4)
        inner.setSpacing(1)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color:rgba(210,225,255,0.88); font-size:12px; background:transparent; border:none;")
        inner.addWidget(title_lbl)
        sub_lbl = QLabel(subtitle[:50])
        sub_lbl.setStyleSheet("color:rgba(110,135,180,0.70); font-size:10px; background:transparent; border:none;")
        inner.addWidget(sub_lbl)
        if meta:
            meta_lbl = QLabel(meta)
            meta_lbl.setStyleSheet("color:rgba(80,105,150,0.60); font-size:10px; background:transparent; border:none;")
            inner.addWidget(meta_lbl)
        return btn

    def _make_action_btn(self, label: str, danger: bool = False) -> QPushButton:
        btn = QPushButton(label)
        col = "rgba(255,80,100,0.25)" if danger else "rgba(100,160,255,0.18)"
        brd = "rgba(255,80,100,0.40)" if danger else "rgba(100,160,255,0.35)"
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{col}; border:1px solid {brd}; border-radius:10px;
                padding:8px 14px; color:rgba(220,235,255,0.90); font-size:12px;
            }}
            QPushButton:hover {{
                background:{col.replace('0.25','0.40').replace('0.18','0.30')};
            }}
        """)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return btn

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(255, 255, 255, 16))
        grad.setColorAt(1.0, QColor(255, 255, 255,  8))
        p.fillRect(self.rect(), QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 22)))
        p.drawLine(self.width()-1, 0, self.width()-1, self.height())


# ═════════════════════════════════════════════════════════════════════════════
#  BROWSER TAB CONTENT
# ═════════════════════════════════════════════════════════════════════════════

class BrowserTab(QWidget):
    urlChanged    = pyqtSignal(str)
    titleChanged  = pyqtSignal(str)
    loadStarted   = pyqtSignal()
    loadProgress  = pyqtSignal(int)
    loadFinished  = pyqtSignal(bool)
    iconChanged   = pyqtSignal(str)   # emoji favicon char

    def __init__(self, profile: QWebEngineProfile,
                 settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.view = QWebEngineView(self)
        page = QWebEnginePage(profile, self.view)
        self.view.setPage(page)
        lay.addWidget(self.view)

        # Apply settings
        self._apply_web_settings()

        # Connect signals
        self.view.urlChanged.connect(lambda u: self.urlChanged.emit(u.toString()))
        self.view.titleChanged.connect(self.titleChanged)
        self.view.loadStarted.connect(self.loadStarted)
        self.view.loadProgress.connect(self.loadProgress)
        self.view.loadFinished.connect(self._on_load_finished)

    def _apply_web_settings(self):
        s = self.view.page().settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                       self._settings.get("javascript", True))
        s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages,
                       self._settings.get("images", True))
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled,
                       self._settings.get("smooth_scroll", True))
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

    def _on_load_finished(self, ok: bool):
        self.loadFinished.emit(ok)
        # Inject custom CSS if any
        css = self._settings.get("custom_css", "")
        if css:
            escaped = css.replace("\\", "\\\\").replace("`", "\\`")
            self.run_js(f"""
            (function(){{
                if(document.__winternetCSS)return;
                document.__winternetCSS=true;
                var s=document.createElement('style');
                s.textContent=`{escaped}`;
                (document.head||document.documentElement).appendChild(s);
            }})();
            """)

    def navigate(self, url: str):
        if not url.strip():
            return
        if "://" not in url:
            url = "https://" + url
        self.view.load(QUrl(url))

    def load_html(self, html: str, base_url: QUrl = QUrl("about:blank")):
        self.view.setHtml(html, base_url)

    def load_file(self, path: Path):
        self.view.load(QUrl.fromLocalFile(str(path)))

    def current_url(self) -> str:
        return self.view.url().toString()

    def current_title(self) -> str:
        return self.view.title()

    def back(self):
        self.view.back()

    def forward(self):
        self.view.forward()

    def reload(self):
        self.view.reload()

    def stop(self):
        self.view.stop()

    def can_go_back(self) -> bool:
        return self.view.history().canGoBack()

    def can_go_forward(self) -> bool:
        return self.view.history().canGoForward()

    def run_js(self, code: str):
        self.view.page().runJavaScript(code)

    def set_zoom(self, percent: int):
        self.view.setZoomFactor(percent / 100.0)


# ═════════════════════════════════════════════════════════════════════════════
#  STATUS BAR
# ═════════════════════════════════════════════════════════════════════════════

class GlassStatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self._text = ""
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(16)
        self._url_label = QLabel("")
        self._url_label.setStyleSheet("color:rgba(130,155,195,0.70); font-size:10px;")
        lay.addWidget(self._url_label)
        lay.addStretch()
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color:rgba(100,130,175,0.60); font-size:10px;")
        lay.addWidget(self._info_label)

    def set_url(self, url: str):
        self._url_label.setText(url[:80] if url else "")

    def set_info(self, text: str):
        self._info_label.setText(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(255, 255, 255, 8))
        p.setPen(QPen(QColor(255, 255, 255, 16)))
        p.drawLine(0, 0, self.width(), 0)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN BROWSER WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class Winternet(QMainWindow):
    """
    Main browser window. Orchestrates all components: tabs, toolbar,
    sidebar, background, status bar, settings, history, bookmarks.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Winternet")
        self.resize(1400, 900)
        self.setMinimumSize(800, 600)

        # ── Core state ────────────────────────────────────────────────────────
        self._tabs: List[BrowserTab] = []
        self._current_tab_idx: int = -1

        # ── Managers ──────────────────────────────────────────────────────────
        self._settings  = SettingsManager()
        self._history   = HistoryManager()
        self._bookmarks = BookmarksManager()

        # ── Web profile ───────────────────────────────────────────────────────
        self._profile = self._make_profile()

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()
        self._build_menu()
        self._apply_shortcuts()

        # ── Refresh timer (for tab bar spinner) ───────────────────────────────
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(50)
        self._refresh_timer.timeout.connect(self._tab_bar.update)
        self._refresh_timer.start()

        # ── Open initial tab ──────────────────────────────────────────────────
        self._open_new_tab()

        # ── Restore sidebar state ─────────────────────────────────────────────
        if self._settings.get("sidebar_open"):
            self._sidebar.show()
            self._toolbar.btn_sidebar.setChecked(True)
        else:
            self._sidebar.hide()

    # ══════════════════════════════════════════════════════════════════════════
    #  PROFILE
    # ══════════════════════════════════════════════════════════════════════════

    def _make_profile(self) -> QWebEngineProfile:
        profile = QWebEngineProfile("Winternet2", self)
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setCachePath(str(CACHE_DIR))

        ua = self._settings.get("user_agent", "")
        if ua:
            profile.setHttpUserAgent(ua)

        # Interceptor
        self._interceptor = AdBlockInterceptor(self._settings, self)
        profile.setUrlRequestInterceptor(self._interceptor)

        # Downloads
        profile.downloadRequested.connect(self._on_download_requested)

        return profile

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Background (fills the whole central widget)
        self._bg = LiquidGlassBackground(central)
        self._bg.lower()
        central.resizeEvent = self._on_resize

        # Tab bar
        self._tab_bar = GlassTabBar(self)
        self._tab_bar.tabSelected.connect(self._on_tab_selected)
        self._tab_bar.tabCloseReq.connect(self._close_tab)
        self._tab_bar.newTabRequested.connect(self._open_new_tab)
        main_lay.addWidget(self._tab_bar)

        # Toolbar
        self._toolbar = BrowserToolbar(self._settings, self)
        self._toolbar.backRequested.connect(self._go_back)
        self._toolbar.forwardRequested.connect(self._go_forward)
        self._toolbar.reloadRequested.connect(self._reload)
        self._toolbar.stopRequested.connect(self._stop)
        self._toolbar.homeRequested.connect(self._go_home)
        self._toolbar.newTabRequested.connect(self._open_new_tab)
        self._toolbar.gameRequested.connect(self._open_game_tab)
        self._toolbar.sidebarToggled.connect(self._toggle_sidebar)
        self._toolbar.settingsRequested.connect(self._show_settings)
        self._toolbar.bookmarkToggled.connect(self._toggle_bookmark)
        self._toolbar.navigateRequested.connect(self._navigate)
        main_lay.addWidget(self._toolbar)

        # Progress bar
        self._progress = GlassProgressBar(self)
        main_lay.addWidget(self._progress)

        # Content area: sidebar + web view stack
        content_area = QWidget()
        content_lay = QHBoxLayout(content_area)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self._settings, self._history, self._bookmarks, self)
        self._sidebar.pageRequested.connect(self._navigate)
        self._sidebar.closed.connect(self._close_sidebar)
        content_lay.addWidget(self._sidebar)

        # Web view stack
        self._web_stack = QStackedWidget()
        content_lay.addWidget(self._web_stack)

        main_lay.addWidget(content_area, stretch=1)

        # Status bar
        self._status_bar = GlassStatusBar(self)
        main_lay.addWidget(self._status_bar)

        # Update status bar periodically
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(2000)
        self._status_timer.timeout.connect(self._update_status_info)
        self._status_timer.start()

    def _on_resize(self, event):
        self._bg.resize(self.centralWidget().size())
        type(self.centralWidget()).resizeEvent(self.centralWidget(), event)

    # ══════════════════════════════════════════════════════════════════════════
    #  MENU BAR
    # ══════════════════════════════════════════════════════════════════════════

    def _build_menu(self):
        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar {
                background: rgba(10,14,35,0.90);
                color: rgba(200,220,255,0.85);
                border-bottom: 1px solid rgba(255,255,255,0.10);
                padding: 2px 8px;
                font-size: 13px;
            }
            QMenuBar::item:selected {
                background: rgba(255,255,255,0.12);
                border-radius: 5px;
            }
            QMenu {
                background: rgba(12,16,40,0.96);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
                padding: 5px 0;
                color: rgba(200,220,255,0.85);
                font-size: 13px;
            }
            QMenu::item { padding: 7px 24px; border-radius: 5px; margin: 1px 5px; }
            QMenu::item:selected { background: rgba(100,160,255,0.22); }
            QMenu::separator { height:1px; background:rgba(255,255,255,0.10); margin: 5px 12px; }
        """)

        # ── File ──────────────────────────────────────────────────────────────
        file_m = mb.addMenu("File")
        self._add_action(file_m, "New Tab",      self._open_new_tab,     "Ctrl+T")
        self._add_action(file_m, "New Window",   self._open_new_window,  "Ctrl+N")
        self._add_action(file_m, "Open Game",    self._open_game_tab)
        file_m.addSeparator()
        self._add_action(file_m, "Close Tab",    self._close_current_tab,"Ctrl+W")
        file_m.addSeparator()
        self._add_action(file_m, "Quit",         self.close,             "Ctrl+Q")

        # ── Edit ──────────────────────────────────────────────────────────────
        edit_m = mb.addMenu("Edit")
        self._add_action(edit_m, "Find in Page", self._find_in_page,     "Ctrl+F")
        edit_m.addSeparator()
        self._add_action(edit_m, "Zoom In",      self._zoom_in,          "Ctrl+=")
        self._add_action(edit_m, "Zoom Out",     self._zoom_out,         "Ctrl+-")
        self._add_action(edit_m, "Actual Size",  self._zoom_reset,       "Ctrl+0")

        # ── View ──────────────────────────────────────────────────────────────
        view_m = mb.addMenu("View")
        self._add_action(view_m, "Sidebar",         self._toggle_sidebar, "Ctrl+B")
        self._add_action(view_m, "Developer Tools", self._open_devtools,  "F12")
        self._add_action(view_m, "View Source",     self._view_source,    "Ctrl+U")
        view_m.addSeparator()
        self._add_action(view_m, "Enter Full Screen", self._toggle_fullscreen, "F11")

        # ── History ───────────────────────────────────────────────────────────
        hist_m = mb.addMenu("History")
        self._add_action(hist_m, "Back",     self._go_back,    "Alt+Left")
        self._add_action(hist_m, "Forward",  self._go_forward, "Alt+Right")
        hist_m.addSeparator()
        self._add_action(hist_m, "Show History",  lambda: self._show_sidebar_page("History"))
        hist_m.addSeparator()
        self._add_action(hist_m, "Clear History", self._history.clear)

        # ── Bookmarks ─────────────────────────────────────────────────────────
        bm_m = mb.addMenu("Bookmarks")
        self._add_action(bm_m, "Add Bookmark",     self._add_bookmark,    "Ctrl+D")
        self._add_action(bm_m, "Show Bookmarks",   lambda: self._show_sidebar_page("Bookmarks"))
        bm_m.addSeparator()
        self._bm_menu = bm_m
        self._populate_bookmarks_menu()
        bm_m.aboutToShow.connect(self._populate_bookmarks_menu)

        # ── Window ────────────────────────────────────────────────────────────
        win_m = mb.addMenu("Window")
        self._add_action(win_m, "Minimize",       self.showMinimized, "Ctrl+M")
        self._add_action(win_m, "Next Tab",        self._next_tab,     "Ctrl+Tab")
        self._add_action(win_m, "Previous Tab",    self._prev_tab,     "Ctrl+Shift+Tab")
        win_m.addSeparator()
        self._add_action(win_m, "Duplicate Tab",   self._duplicate_tab)

    def _add_action(self, menu: QMenu, label: str, slot, shortcut: str = None) -> QAction:
        act = QAction(label, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    def _populate_bookmarks_menu(self):
        # Remove old bookmark entries (keep first 2 items: Add, Show)
        actions = self._bm_menu.actions()
        for act in actions[3:]:
            self._bm_menu.removeAction(act)
        for bm in self._bookmarks.get_all()[-20:]:
            act = QAction(bm.get("title", bm["url"])[:40], self)
            act.triggered.connect(lambda _, u=bm["url"]: self._navigate(u))
            self._bm_menu.addAction(act)

    # ══════════════════════════════════════════════════════════════════════════
    #  KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_shortcuts(self):
        pairs = [
            ("Ctrl+T",          self._open_new_tab),
            ("Ctrl+W",          self._close_current_tab),
            ("Ctrl+Tab",        self._next_tab),
            ("Ctrl+Shift+Tab",  self._prev_tab),
            ("Ctrl+L",          self._focus_url_bar),
            ("Ctrl+R",          self._reload),
            ("F5",              self._reload),
            ("Ctrl+F5",         self._hard_reload),
            ("F12",             self._open_devtools),
            ("Ctrl+D",          self._add_bookmark),
            ("Ctrl+B",          self._toggle_sidebar),
            ("Ctrl+=",          self._zoom_in),
            ("Ctrl+-",          self._zoom_out),
            ("Ctrl+0",          self._zoom_reset),
            ("Alt+Left",        self._go_back),
            ("Alt+Right",       self._go_forward),
            ("Escape",          self._escape),
            ("F11",             self._toggle_fullscreen),
            ("Ctrl+1",          lambda: self._select_tab(0)),
            ("Ctrl+2",          lambda: self._select_tab(1)),
            ("Ctrl+3",          lambda: self._select_tab(2)),
            ("Ctrl+4",          lambda: self._select_tab(3)),
            ("Ctrl+5",          lambda: self._select_tab(4)),
            ("Ctrl+6",          lambda: self._select_tab(5)),
            ("Ctrl+7",          lambda: self._select_tab(6)),
            ("Ctrl+8",          lambda: self._select_tab(7)),
            ("Ctrl+9",          lambda: self._select_tab_last()),
        ]
        for key, fn in pairs:
            act = QAction(self)
            act.setShortcut(QKeySequence(key))
            act.triggered.connect(fn)
            self.addAction(act)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    def _open_new_tab(self, url: str = None) -> BrowserTab:
        tab = BrowserTab(self._profile, self._settings, self)

        # Connect tab signals
        tab.urlChanged.connect(lambda u, t=tab: self._on_tab_url_changed(u, t))
        tab.titleChanged.connect(lambda title, t=tab: self._on_tab_title_changed(title, t))
        tab.loadStarted.connect(lambda t=tab: self._on_tab_load_started(t))
        tab.loadProgress.connect(lambda v, t=tab: self._on_tab_load_progress(v, t))
        tab.loadFinished.connect(lambda ok, t=tab: self._on_tab_load_finished(ok, t))

        # Link hover → status bar
        tab.view.page().linkHovered.connect(self._status_bar.set_url)

        idx_in_tabs = len(self._tabs)
        self._tabs.append(tab)
        self._web_stack.addWidget(tab)

        bar_idx = self._tab_bar.addTab("New Tab")

        # Set focus to new tab
        self._select_tab(bar_idx)

        # Load content
        new_tab_mode = self._settings.get("new_tab_page", "speed_dial")
        if url:
            tab.navigate(url)
        elif new_tab_mode == "game":
            self._load_game_into_tab(tab)
        elif new_tab_mode == "home":
            tab.navigate(self._settings.get("home_page", DEFAULT_HOME))
        elif new_tab_mode == "blank":
            tab.load_html("<html><body style='background:#050810'></body></html>")
        else:
            tab.load_html(SPEED_DIAL_HTML)

        return tab

    def _open_game_tab(self):
        tab = self._open_new_tab()
        self._load_game_into_tab(tab)
        idx = self._current_tab_idx
        self._tab_bar.setTabTitle(idx, "🎮 Arcade")

    def _load_game_into_tab(self, tab: BrowserTab):
        game_file = BASE_DIR / "game" / "index.html"
        if game_file.exists():
            tab.load_file(game_file)
        else:
            tab.load_html(GAME_HTML)

    def _close_tab(self, idx: int):
        if len(self._tabs) == 1:
            self._open_new_tab()
            self._close_tab_at(0)
            return
        self._close_tab_at(idx)

    def _close_tab_at(self, idx: int):
        if idx < 0 or idx >= len(self._tabs):
            return
        tab = self._tabs.pop(idx)
        self._web_stack.removeWidget(tab)
        tab.deleteLater()
        self._tab_bar.removeTab(idx)
        new_idx = min(idx, len(self._tabs) - 1)
        if new_idx >= 0:
            self._select_tab(new_idx)

    def _close_current_tab(self):
        self._close_tab(self._current_tab_idx)

    def _select_tab(self, idx: int):
        if idx < 0 or idx >= len(self._tabs):
            return
        self._current_tab_idx = idx
        self._tab_bar.setCurrentIndex(idx)
        self._web_stack.setCurrentWidget(self._tabs[idx])
        tab = self._tabs[idx]
        self._toolbar.url_bar.setUrl(tab.current_url())
        self._toolbar.set_can_go_back(tab.can_go_back())
        self._toolbar.set_can_go_forward(tab.can_go_forward())
        bm = self._bookmarks.is_bookmarked(tab.current_url())
        self._toolbar.set_bookmarked(bm)
        zoom = self._settings.get("zoom", 100)
        tab.set_zoom(zoom)

    def _select_tab_last(self):
        self._select_tab(len(self._tabs) - 1)

    def _next_tab(self):
        if not self._tabs:
            return
        self._select_tab((self._current_tab_idx + 1) % len(self._tabs))

    def _prev_tab(self):
        if not self._tabs:
            return
        self._select_tab((self._current_tab_idx - 1) % len(self._tabs))

    def _duplicate_tab(self):
        tab = self._current_tab()
        if tab:
            self._open_new_tab(tab.current_url())

    def _on_tab_selected(self, idx: int):
        if idx != self._current_tab_idx:
            self._select_tab(idx)

    def _current_tab(self) -> Optional[BrowserTab]:
        if 0 <= self._current_tab_idx < len(self._tabs):
            return self._tabs[self._current_tab_idx]
        return None

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB SIGNAL HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _tab_index_of(self, tab: BrowserTab) -> int:
        try:
            return self._tabs.index(tab)
        except ValueError:
            return -1

    def _on_tab_url_changed(self, url: str, tab: BrowserTab):
        idx = self._tab_index_of(tab)
        if idx < 0:
            return
        self._tab_bar.setTabUrl(idx, url)
        if idx == self._current_tab_idx:
            self._toolbar.url_bar.setUrl(url)
            self._toolbar.set_can_go_back(tab.can_go_back())
            self._toolbar.set_can_go_forward(tab.can_go_forward())
            bm = self._bookmarks.is_bookmarked(url)
            self._toolbar.set_bookmarked(bm)

    def _on_tab_title_changed(self, title: str, tab: BrowserTab):
        idx = self._tab_index_of(tab)
        if idx < 0:
            return
        self._tab_bar.setTabTitle(idx, title or "New Tab")
        if idx == self._current_tab_idx:
            self.setWindowTitle(f"{title} — Winternet" if title else "Winternet")
        # Add to history
        url = tab.current_url()
        if title and url and url not in ("about:blank", ""):
            self._history.add(url, title)

    def _on_tab_load_started(self, tab: BrowserTab):
        idx = self._tab_index_of(tab)
        if idx < 0:
            return
        self._tab_bar.setTabLoading(idx, True)
        if idx == self._current_tab_idx:
            self._toolbar.set_loading(True)
            self._progress.start()

    def _on_tab_load_progress(self, value: int, tab: BrowserTab):
        idx = self._tab_index_of(tab)
        if idx == self._current_tab_idx:
            self._progress.setValue(value)

    def _on_tab_load_finished(self, ok: bool, tab: BrowserTab):
        idx = self._tab_index_of(tab)
        if idx < 0:
            return
        self._tab_bar.setTabLoading(idx, False)
        if idx == self._current_tab_idx:
            self._toolbar.set_loading(False)
            self._progress.setValue(100)
            self._toolbar.set_can_go_back(tab.can_go_back())
            self._toolbar.set_can_go_forward(tab.can_go_forward())

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVIGATION
    # ══════════════════════════════════════════════════════════════════════════

    def _navigate(self, url: str):
        tab = self._current_tab()
        if tab:
            tab.navigate(url)

    def _go_back(self):
        tab = self._current_tab()
        if tab:
            tab.back()

    def _go_forward(self):
        tab = self._current_tab()
        if tab:
            tab.forward()

    def _reload(self):
        tab = self._current_tab()
        if tab:
            tab.reload()

    def _hard_reload(self):
        tab = self._current_tab()
        if tab:
            tab.view.page().triggerAction(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def _stop(self):
        tab = self._current_tab()
        if tab:
            tab.stop()

    def _go_home(self):
        tab = self._current_tab()
        if tab:
            tab.navigate(self._settings.get("home_page", DEFAULT_HOME))

    def _escape(self):
        tab = self._current_tab()
        if tab:
            tab.stop()
        self._toolbar.url_bar.focusEdit()

    def _focus_url_bar(self):
        self._toolbar.url_bar.focusEdit()

    # ══════════════════════════════════════════════════════════════════════════
    #  ZOOM
    # ══════════════════════════════════════════════════════════════════════════

    def _zoom_in(self):
        z = min(self._settings.get("zoom", 100) + 10, 300)
        self._settings.set("zoom", z)
        tab = self._current_tab()
        if tab:
            tab.set_zoom(z)
        self._status_bar.set_info(f"Zoom: {z}%")

    def _zoom_out(self):
        z = max(self._settings.get("zoom", 100) - 10, 25)
        self._settings.set("zoom", z)
        tab = self._current_tab()
        if tab:
            tab.set_zoom(z)
        self._status_bar.set_info(f"Zoom: {z}%")

    def _zoom_reset(self):
        self._settings.set("zoom", 100)
        tab = self._current_tab()
        if tab:
            tab.set_zoom(100)
        self._status_bar.set_info("Zoom: 100%")

    # ══════════════════════════════════════════════════════════════════════════
    #  BOOKMARKS
    # ══════════════════════════════════════════════════════════════════════════

    def _add_bookmark(self):
        tab = self._current_tab()
        if not tab:
            return
        url   = tab.current_url()
        title = tab.current_title() or url
        if self._bookmarks.is_bookmarked(url):
            self._bookmarks.remove(url)
            self._toolbar.set_bookmarked(False)
            self._status_bar.set_info("Bookmark removed")
        else:
            self._bookmarks.add(url, title)
            self._toolbar.set_bookmarked(True)
            self._status_bar.set_info(f"Bookmarked: {title[:40]}")

    def _toggle_bookmark(self):
        self._add_bookmark()

    # ══════════════════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════════════════

    def _toggle_sidebar(self):
        if self._sidebar.isVisible():
            self._close_sidebar()
        else:
            self._sidebar.show()
            self._toolbar.btn_sidebar.setChecked(True)
            self._settings.set("sidebar_open", True)

    def _close_sidebar(self):
        self._sidebar.hide()
        self._toolbar.btn_sidebar.setChecked(False)
        self._settings.set("sidebar_open", False)

    def _show_sidebar_page(self, page: str):
        if not self._sidebar.isVisible():
            self._toggle_sidebar()
        self._sidebar._show_page(page)

    # ══════════════════════════════════════════════════════════════════════════
    #  DEVELOPER TOOLS & VIEW SOURCE
    # ══════════════════════════════════════════════════════════════════════════

    def _open_devtools(self):
        tab = self._current_tab()
        if not tab:
            return
        dev_view = QWebEngineView()
        tab.view.page().setDevToolsPage(dev_view.page())
        win = QMainWindow(self)
        win.setWindowTitle("Developer Tools — Winternet")
        win.setCentralWidget(dev_view)
        win.resize(1000, 650)
        win.setStyleSheet("QMainWindow { background: #1a1a2e; }")
        win.show()

    def _view_source(self):
        tab = self._current_tab()
        if tab:
            self._open_new_tab(f"view-source:{tab.current_url()}")

    # ══════════════════════════════════════════════════════════════════════════
    #  FIND IN PAGE
    # ══════════════════════════════════════════════════════════════════════════

    def _find_in_page(self):
        tab = self._current_tab()
        if not tab:
            return
        text, ok = QInputDialog.getText(self, "Find in Page", "Search text:",
                                        QLineEdit.EchoMode.Normal, "")
        if ok and text:
            tab.view.findText(text)

    # ══════════════════════════════════════════════════════════════════════════
    #  SETTINGS DIALOG
    # ══════════════════════════════════════════════════════════════════════════

    def _show_settings(self):
        self._show_sidebar_page("Settings")

    # ══════════════════════════════════════════════════════════════════════════
    #  FULL SCREEN
    # ══════════════════════════════════════════════════════════════════════════

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ══════════════════════════════════════════════════════════════════════════
    #  NEW WINDOW
    # ══════════════════════════════════════════════════════════════════════════

    def _open_new_window(self):
        win = Winternet()
        win.show()

    # ══════════════════════════════════════════════════════════════════════════
    #  DOWNLOADS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_download_requested(self, item: QWebEngineDownloadRequest):
        path = self._settings.get("download_path", str(Path.home() / "Downloads"))
        filename = item.suggestedFileName() or "download"
        dest = os.path.join(path, filename)
        item.setDownloadDirectory(path)
        item.setDownloadFileName(filename)
        item.accept()
        self._status_bar.set_info(f"Downloading: {filename}")

    # ══════════════════════════════════════════════════════════════════════════
    #  STATUS BAR
    # ══════════════════════════════════════════════════════════════════════════

    def _update_status_info(self):
        blocked = self._interceptor.blocked_count
        zoom    = self._settings.get("zoom", 100)
        info_parts = []
        if blocked > 0:
            info_parts.append(f"🛡 {blocked} blocked")
        if zoom != 100:
            info_parts.append(f"Zoom {zoom}%")
        self._status_bar.set_info("  ·  ".join(info_parts))

    # ══════════════════════════════════════════════════════════════════════════
    #  WINDOW EVENTS
    # ══════════════════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        self._settings.save()
        event.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  APPLICATION ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    # ── Windows-specific crash prevention ────────────────────────────────────
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetDllDirectoryW(None)
        except Exception:
            pass

    # ── MUST be set before QApplication ──────────────────────────────────────
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Winternet")

    # Global font
    app.setFont(QFont("-apple-system", 13))

    # Global dark palette so native widgets don't flash white
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,       QColor(10,  14, 35))
    pal.setColor(QPalette.ColorRole.WindowText,   QColor(200, 220, 255))
    pal.setColor(QPalette.ColorRole.Base,         QColor(15,  20, 50))
    pal.setColor(QPalette.ColorRole.AlternateBase,QColor(20,  26, 60))
    pal.setColor(QPalette.ColorRole.Text,         QColor(200, 220, 255))
    pal.setColor(QPalette.ColorRole.Button,       QColor(22,  28, 65))
    pal.setColor(QPalette.ColorRole.ButtonText,   QColor(200, 220, 255))
    pal.setColor(QPalette.ColorRole.Highlight,    QColor(100, 160, 255))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(pal)

    window = Winternet()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()