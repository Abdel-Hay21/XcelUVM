from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QAbstractAnimation, QVariantAnimation, QPointF, QRect
from PyQt5.QtGui import QColor, QPainter, QLinearGradient, QBrush, QFont, QPen, QRadialGradient

from core.config import get_image_path


class GradientLabel(QLabel):
    def __init__(self, text, c1="#6366f1", c2="#a78bfa", parent=None):
        super().__init__(text, parent)
        self._c1, self._c2 = c1, c2

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(self._c1))
        grad.setColorAt(1.0, QColor(self._c2))
        p.setFont(self.font())
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        # draw text by using the gradient as a brush via drawText trick
        from PyQt5.QtGui import QPen
        pen = QPen(QBrush(grad), 0)
        p.setPen(pen)
        p.drawText(self.rect(), self.alignment(), self.text())
        p.end()



from PyQt5.QtWidgets import QGraphicsDropShadowEffect
class CTAButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("start_btn")
        self.setFixedSize(220, 52)
        self.setCursor(Qt.PointingHandCursor)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(139, 92, 246, 0))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        
        self.anim_group = QParallelAnimationGroup(self)
        
        self.glow_anim = QVariantAnimation(self)
        self.glow_anim.setDuration(300)
        self.glow_anim.valueChanged.connect(self._update_shadow)
        self.anim_group.addAnimation(self.glow_anim)
        
        self.scale_anim = QVariantAnimation(self)
        self.scale_anim.setDuration(300)
        self.scale_anim.setEasingCurve(QEasingCurve.OutBack)
        self.scale_anim.valueChanged.connect(self._update_scale)
        self.anim_group.addAnimation(self.scale_anim)
        
        self._base_text = text
        self.setText(self._base_text + "   →")
        
    def _update_shadow(self, val):
        self.shadow.setColor(QColor(139, 92, 246, int(val)))
        
    def _update_scale(self, val):
        self.setFixedSize(int(220 * val), int(52 * val))

    def enterEvent(self, e):
        super().enterEvent(e)
        self.setText(self._base_text + "      →")
        self.glow_anim.setStartValue(self.shadow.color().alpha())
        self.glow_anim.setEndValue(150)
        self.scale_anim.setStartValue(self.width() / 220.0)
        self.scale_anim.setEndValue(1.05)
        self.anim_group.start()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.setText(self._base_text + "   →")
        self.glow_anim.setStartValue(self.shadow.color().alpha())
        self.glow_anim.setEndValue(0)
        self.scale_anim.setStartValue(self.width() / 220.0)
        self.scale_anim.setEndValue(1.0)
        self.anim_group.start()

class WelcomePage(QWidget):
    start_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome_root")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        # ── Centre column ────────────────────────────────────────────────────
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setAlignment(Qt.AlignHCenter)

        # Title Layout (Logos + Text)
        title_lay = QHBoxLayout()
        title_lay.setSpacing(5) # Space between the combined logos and the text
        title_lay.setAlignment(Qt.AlignCenter)
        
        # --- Logos Overlay Group ---
        logos_wrapper = QWidget()
        logos_lay = QGridLayout(logos_wrapper)
        logos_lay.setContentsMargins(0, 0, 0, 0)
        
        from PyQt5.QtGui import QPixmap
        
        # Icon 1 (Main Logo)
        self.icon_lbl = QLabel()
        pix1 = QPixmap(get_image_path("Logo.png"))
        self.icon_lbl.setPixmap(pix1.scaledToHeight(110, Qt.SmoothTransformation))
        
        # Icon 2 (Second Logo - X.png)
        self.icon2_lbl = QLabel()
        pix2 = QPixmap(get_image_path("X.png"))
        self.icon2_lbl.setPixmap(pix2.scaledToHeight(80, Qt.SmoothTransformation))
        
        # ?? Control the overlap distance here! ??
        # Increase the left margin (e.g., 60, 70, 80) to push X.png to the right.
        # Decrease it (e.g., 40, 30, 20) to pull X.png more under the main logo.
        
        self.icon_lbl.setContentsMargins(0, 0, 0, 0)
        self.icon2_lbl.setContentsMargins(80, 0, 0, 0)
        
        # Add both to the same cell (0,0) to force overlay
        logos_lay.addWidget(self.icon2_lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        logos_lay.addWidget(self.icon_lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.icon_lbl.raise_() # Make sure main logo is on top!
        # ---------------------------
        
        # "celUVM" text
        title = QLabel()
        title.setText("<span style='color: #ffffff;'>cel</span><span style='color: #8b5cf6;'>UVM</span>")
        font = QFont("Segoe UI", 58, QFont.Bold)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        title.setContentsMargins(0, 0, 0, 0)

        title_lay.addWidget(logos_wrapper)
        title_lay.addWidget(title)
        
        col.addLayout(title_lay)

        # Underline accent bar
        bar = QFrame()
        bar.setFixedHeight(4)
        bar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #ffffff, stop:0.5 #a886f7, stop:1 #4d02f7);"
            "border-radius: 2px; margin: 0 780px;"
        )
        col.addWidget(bar)
        col.addSpacing(20)

        # Tagline
        tag = QLabel("UVM testbench generator")
        tag.setAlignment(Qt.AlignCenter)
        tag.setStyleSheet(
            "color: #94a3b8; font-size: 16px; font-family: 'Segoe UI';"
        )
        col.addWidget(tag)
        col.addSpacing(32)

        # Feature pills
        features = [
        ]
        for icon, text in features:
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignHCenter)
            row.setSpacing(10)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 16px;")
            tx = QLabel(text)
            tx.setStyleSheet(
                "color: #64748b; font-size: 13px; font-family: 'Segoe UI';"
            )
            row.addWidget(ic)
            row.addWidget(tx)
            col.addLayout(row)
            col.addSpacing(6)

        col.addSpacing(40)

        # Start button
        start_btn = QPushButton("Get Started  →")
        start_btn.setObjectName("start_btn")
        start_btn.setFixedSize(220, 52)
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.clicked.connect(self.start_clicked)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignHCenter)
        btn_row.addWidget(start_btn)
        col.addLayout(btn_row)

        outer.addLayout(col)
        outer.addStretch(1)

        # Version footer
        footer = QLabel("v1.0   ·   XcelUVM Tool")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            "color: #2a2d3e; font-size: 11px; font-family: 'Segoe UI';"
            "padding-bottom: 12px;"
        )
        outer.addWidget(footer)


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_x = 28.0 if checked else 2.0
        self.setFixedSize(56, 28)
        self.setCursor(Qt.PointingHandCursor)

    def _get_x(self): return self._thumb_x
    def _set_x(self, v): self._thumb_x = v; self.update()
    thumbX = pyqtProperty(float, _get_x, _set_x)

    def isChecked(self): return self._checked

    def setChecked(self, v):
        self._checked = v
        anim = QPropertyAnimation(self, b"thumbX", self)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(self._thumb_x)
        anim.setEndValue(28.0 if v else 2.0)
        anim.start()
        self.update()

    def mousePressEvent(self, e):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Track
        track = QColor("#6366f1") if self._checked else QColor("#2a2d3e")
        p.setBrush(QBrush(track))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 4, 56, 20, 10, 10)
        # Thumb
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(int(self._thumb_x), 2, 24, 24)
        p.end()

class CrossfadeOverlay(QWidget):
    def __init__(self, parent, pix1, pix2, direction=0):
        super().__init__(parent)
        self.pix1 = pix1
        self.pix2 = pix2
        self.direction = direction
        self.progress = 0.0
        
    def set_progress(self, p):
        self.progress = float(p)
        self.update()
        
    def paintEvent(self, e):
        p = QPainter(self)
        drift = 60 * self.direction
        
        # Old page: fades out and drifts in the opposite direction
        p.setOpacity(1.0 - self.progress)
        p.drawPixmap(int(-drift * self.progress), 0, self.pix1)
        
        # New page: fades in and drifts from the direction
        p.setOpacity(self.progress)
        p.drawPixmap(int(drift * (1.0 - self.progress)), 0, self.pix2)
        
        p.end()

class HeroTransitionOverlay(QWidget):
    def __init__(self, parent, pix1, pix2, rect1, rect2):
        super().__init__(parent)
        self.pix1 = pix1
        self.pix2 = pix2
        self.rect1 = rect1
        self.rect2 = rect2
        self.progress = 0.0
        from PyQt5.QtGui import QPixmap
        self.logo_pix = QPixmap(get_image_path("Logo.png"))
        
    def set_progress(self, p):
        self.progress = float(p)
        self.update()
        
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#0f1117"))
        
        # 1. Old page fades out in first 20%
        if self.progress < 0.2:
            op_old = 1.0 - (self.progress / 0.2)
            p.setOpacity(op_old)
            p.drawPixmap(0, 0, self.pix1)
        
        # 2. New page fades in after 50%
        if self.progress > 0.5:
            op_new = (self.progress - 0.5) / 0.5
            p.setOpacity(op_new)
            p.drawPixmap(0, 0, self.pix2)
        
        # 3. Draw moving logo image directly
        t = self.progress
        x = self.rect1.x() + (self.rect2.x() - self.rect1.x()) * t
        y = self.rect1.y() + (self.rect2.y() - self.rect1.y()) * t
        w = self.rect1.width()  + (self.rect2.width()  - self.rect1.width())  * t
        h = self.rect1.height() + (self.rect2.height() - self.rect1.height()) * t
        
        pix_h = int(110 + (30 - 110) * t)
        p.setOpacity(1.0)
        if pix_h > 0 and w > 0 and h > 0:
            pix_scaled = self.logo_pix.scaledToHeight(pix_h, Qt.SmoothTransformation)
            px = x + (w - pix_scaled.width()) / 2.0
            py = y + (h - pix_scaled.height()) / 2.0
            p.drawPixmap(int(px), int(py), pix_scaled)
        
        p.end()


class SuccessOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(parent.rect())
        
        self.progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(1000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self.set_progress)
        # Note: no deleteLater, it stays to provide the glow!
        
    def start(self):
        self.show()
        self.raise_()
        self.anim.start()
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self.fade_out)
        
    def fade_out(self):
        self.anim.setDirection(QAbstractAnimation.Backward)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()
        
    def set_progress(self, v):
        self.progress = float(v)
        self.update()
        
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        t = self.progress
        thickness = 120
        alpha = int(100 * t)  # Fade in to a subtle, classy glow
        
        w = self.width()
        h = self.height()
        
        c = QColor(16, 185, 129, alpha)
        trans = QColor(16, 185, 129, 0)
        
        gt = QLinearGradient(0, 0, 0, thickness)
        gt.setColorAt(0, c); gt.setColorAt(1, trans)
        p.fillRect(0, 0, w, thickness, gt)
        
        gb = QLinearGradient(0, h, 0, h - thickness)
        gb.setColorAt(0, c); gb.setColorAt(1, trans)
        p.fillRect(0, h - thickness, w, thickness, gb)
        
        gl = QLinearGradient(0, 0, thickness, 0)
        gl.setColorAt(0, c); gl.setColorAt(1, trans)
        p.fillRect(0, 0, thickness, h, gl)
        
        gr = QLinearGradient(w, 0, w - thickness, 0)
        gr.setColorAt(0, c); gr.setColorAt(1, trans)
        p.fillRect(w - thickness, 0, thickness, h, gr)
        
        p.end()

class SlidingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages, self._cur, self._busy = [], 0, False

    def addPage(self, w):
        w.setParent(self)
        self._pages.append(w)
        if len(self._pages) == 1:
            w.setGeometry(0, 0, max(self.width(),1), max(self.height(),1)); w.show()
        else:
            w.hide()

    def resizeEvent(self, e):
        if self._pages:
            self._pages[self._cur].setGeometry(0, 0, self.width(), self.height())

    def currentIndex(self): return self._cur
    
    def count(self): return len(self._pages)
    
    def clear(self):
        for w in self._pages:
            w.setParent(None)
            w.deleteLater()
        self._pages.clear()
        self._cur = 0

    def slide_to(self, idx, style="slide", mid_callback=None):
        if self._busy or idx == self._cur or not (0 <= idx < len(self._pages)): return
        d = 1 if idx > self._cur else -1
        cur, nxt = self._pages[self._cur], self._pages[idx]
        w, h = self.width(), self.height()
        self._busy = True

        if style == "fade_dark":
            from PyQt5.QtWidgets import QGraphicsOpacityEffect
            nxt.setGeometry(0, 0, w, h)
            nxt.hide()
            
            top = self.window()
            self._overlay = QFrame(top)
            self._overlay.setStyleSheet("background-color: #050505;")
            self._overlay.setGeometry(top.rect())
            self._overlay.show()
            self._overlay.raise_()
            
            self._op = QGraphicsOpacityEffect(self._overlay)
            self._op.setOpacity(0.0)
            self._overlay.setGraphicsEffect(self._op)
            
            self._fade_in = QPropertyAnimation(self._op, b"opacity")
            self._fade_in.setDuration(500)
            self._fade_in.setStartValue(0.0)
            self._fade_in.setEndValue(1.0)
            self._fade_in.setEasingCurve(QEasingCurve.InOutCubic)
            
            self._fade_out = QPropertyAnimation(self._op, b"opacity")
            self._fade_out.setDuration(600)
            self._fade_out.setStartValue(1.0)
            self._fade_out.setEndValue(0.0)
            self._fade_out.setEasingCurve(QEasingCurve.InOutCubic)
            
            _idx, _old = idx, cur
            def _mid():
                _old.hide()
                # update _cur NOW so currentIndex() returns the new value
                self._cur = _idx
                # ── call the mid_callback while screen is fully black ──────
                if mid_callback:
                    mid_callback()
                nxt.show()
                self._fade_out.start(QAbstractAnimation.DeleteWhenStopped)
                
            def _end():
                self._overlay.hide()
                self._overlay.deleteLater()
                self._done(_idx, _old)
                
            self._fade_in.finished.connect(_mid)
            self._fade_out.finished.connect(_end)
            self._fade_in.start(QAbstractAnimation.DeleteWhenStopped)
            return

        nxt.setGeometry(0, 0, w, h)
        # We need nxt to be fully laid out to grab it, so show it temporarily under cur
        nxt.lower()
        nxt.show()
        
        pix_cur = cur.grab()
        pix_nxt = nxt.grab()
        
        cur.hide()
        nxt.hide()
        
        self._overlay = CrossfadeOverlay(self, pix_cur, pix_nxt, direction=d)
        self._overlay.setGeometry(0, 0, w, h)
        self._overlay.show()
        self._overlay.raise_()

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(400)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.valueChanged.connect(self._overlay.set_progress)
        
        _idx, _old = idx, cur
        def _cleanup():
            self._overlay.hide()
            self._overlay.deleteLater()
            nxt.show()
            self._done(_idx, _old)
            
        self._anim.finished.connect(_cleanup)
        self._anim.start(QAbstractAnimation.DeleteWhenStopped)

    def _done(self, idx, old):
        old.hide(); self._pages[idx].setGeometry(0, 0, self.width(), self.height())
        self._cur = idx; self._busy = False

class StepBar(QWidget):
    LABELS = ["❶ Project", "❷ Reference Model", "❸ Options", "❹ Modules", "❺ Ports", "❻ Sequences", "❼ Generate"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cur = 0
        self.setFixedHeight(62)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(30, 10, 50, 10)
        lay.setSpacing(0)
        
        from PyQt5.QtGui import QPixmap
        self.logo_lbl = QLabel()
        pix = QPixmap(get_image_path("Logo.png"))
        self.logo_lbl.setPixmap(pix.scaledToHeight(30, Qt.SmoothTransformation))
        self.logo_lbl.setStyleSheet("background: transparent; border: none;")
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.logo_lbl)
        lay.addSpacing(15)
        
        self._items, self._conns = [], []
        for i, name in enumerate(self.LABELS):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(36)
            self._items.append(lbl)
            lay.addWidget(lbl)
            if i < len(self.LABELS) - 1:
                line = QFrame(); line.setFrameShape(QFrame.HLine)
                line.setFixedHeight(2)
                self._conns.append(line)
                lay.addWidget(line, stretch=1)
        self._refresh()

    def _refresh(self, progress=1.0):
        STATES = {
            'future': {'r': 71, 'g': 85, 'b': 105, 'br': 0, 'bg': 0, 'bb': 0, 'ba': 0, 'p': 10, 'w': 600, 'fs': 13},
            'active': {'r': 255, 'g': 255, 'b': 255, 'br': 99, 'bg': 102, 'bb': 241, 'ba': 255, 'p': 10, 'w': 800, 'fs': 13},
            'completed': {'r': 16, 'g': 185, 'b': 129, 'br': 16, 'bg': 185, 'bb': 129, 'ba': 25, 'p': 10, 'w': 700, 'fs': 13},
        }
        
        def lerp(v1, v2, p):
            return int(v1 + (v2 - v1) * p)

        old_idx = getattr(self, '_old_cur', self._cur)
        new_idx = self._cur

        for i, lbl in enumerate(self._items):
            old_s = STATES['active'] if i == old_idx else (STATES['completed'] if i < old_idx else STATES['future'])
            new_s = STATES['active'] if i == new_idx else (STATES['completed'] if i < new_idx else STATES['future'])
            
            r = lerp(old_s['r'], new_s['r'], progress)
            g = lerp(old_s['g'], new_s['g'], progress)
            b = lerp(old_s['b'], new_s['b'], progress)
            
            br = lerp(old_s['br'], new_s['br'], progress)
            bg = lerp(old_s['bg'], new_s['bg'], progress)
            bb = lerp(old_s['bb'], new_s['bb'], progress)
            ba = lerp(old_s['ba'], new_s['ba'], progress)
            
            pad = lerp(old_s['p'], new_s['p'], progress)
            fw = lerp(old_s['w'], new_s['w'], progress)
            fs = lerp(old_s['fs'], new_s['fs'], progress)
            
            lbl.setStyleSheet(f"""
                color: rgb({r},{g},{b});
                background: rgba({br},{bg},{bb},{ba});
                font-weight: {fw};
                font-family: 'Segoe UI';
                font-size: {fs}px;
                border-radius: 18px;
                padding: 0px {pad}px;
            """)
            
        for i, c in enumerate(self._conns):
            old_c = (16, 185, 129) if i < old_idx else (51, 65, 85)
            new_c = (16, 185, 129) if i < new_idx else (51, 65, 85)
            
            lr = lerp(old_c[0], new_c[0], progress)
            lg = lerp(old_c[1], new_c[1], progress)
            lb = lerp(old_c[2], new_c[2], progress)
            
            c.setStyleSheet(f"background: rgb({lr},{lg},{lb});")

    def set_step(self, idx):
        if idx == self._cur: return
        
        if hasattr(self, '_anim') and self._anim.state() == QAbstractAnimation.Running:
            self._anim.stop()
            
        self._old_cur = self._cur
        self._cur = idx
        
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(400)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        def update_frame(v):
            self._refresh(float(v))
            
        self._anim.valueChanged.connect(update_frame)
        self._anim.start()

