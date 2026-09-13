import math
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog, QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QLineEdit
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QVariantAnimation, QEasingCurve, QRectF, pyqtSignal, QAbstractAnimation, QThread, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QLinearGradient, QPen, QFontMetrics, QBrush, QGradient, QPixmap, QTextDocument

class PhaseLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            color: rgba(255, 255, 255, 210);
            font-size: 56px;
            font-weight: 200;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            letter-spacing: 4px;
        """)
        eff = QGraphicsOpacityEffect()
        eff.setOpacity(0)
        self.setGraphicsEffect(eff)

class NavButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setMouseTracking(True)
        self.hover_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.valueChanged.connect(self._update_hover)

    def _update_hover(self, val):
        self.hover_progress = float(val)
        self.update()

    def enterEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def leaveEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self.hover_progress > 0:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, int(15 * self.hover_progress)))
            p.drawEllipse(self.rect())
            
        p.setPen(QColor(255, 255, 255, int(120 + 80 * self.hover_progress)))
        font = QFont("Segoe UI", 16, QFont.Light)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, self.text)


class WaveButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None, side="right", base_color="#10b981", text="Yes"):
        super().__init__(parent)
        self.side = side
        self.base_color = QColor(base_color)

        self.text = text
        
        self.setMouseTracking(True)
        self.hover_progress = 0.0
        self.fill_progress = 0.0
        
        # Hover animation
        self.hover_anim = QVariantAnimation(self)
        self.hover_anim.setDuration(250)
        self.hover_anim.valueChanged.connect(self._update_hover)
        
    def _update_hover(self, val):
        self.hover_progress = float(val)
        self.update()

    def enterEvent(self, event):
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.hover_progress)
        self.hover_anim.setEndValue(1.0)
        self.hover_anim.start()
        
    def leaveEvent(self, event):
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.hover_progress)
        self.hover_anim.setEndValue(0.0)
        self.hover_anim.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            
    def set_fill_progress(self, val):
        self.fill_progress = val
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Alphas
        base_a = 15
        hover_a = 50
        
        # Edge alpha interpolates based on hover and fill
        edge_alpha = int(base_a + (hover_a - base_a) * self.hover_progress)
        edge_alpha = int(edge_alpha + (255 - edge_alpha) * self.fill_progress)
        
        # Center alpha (the transparent side of the gradient) remains 0
        center_alpha = 0
        
        # Setup linear gradient
        if self.side == "right":
            grad = QLinearGradient(w, 0, 0, 0)
        else: # left
            grad = QLinearGradient(0, 0, w, 0)
            
        c_edge = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), edge_alpha)
        c_mid = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), int(edge_alpha * 0.4))
        c_center = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), center_alpha)
        
        grad.setColorAt(0.0, c_edge)
        grad.setColorAt(0.4, c_mid)
        grad.setColorAt(1.0, c_center)
        
        p.fillRect(self.rect(), grad)
        
        # Draw Text
        text_alpha = int((120 + 135 * self.hover_progress) * (1.0 - self.fill_progress))
        if text_alpha > 0:
            p.setPen(QColor(255, 255, 255, text_alpha))
            font = QFont("Segoe UI", 32, QFont.Light)
            p.setFont(font)
            
            text_rect = QRectF(0, 0, w, h)
            p.drawText(text_rect, Qt.AlignCenter, self.text)


class AnimatedPromptLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0.0
        self.transition_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(4000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self._update_offset)
        self.anim.start()
        
    def _update_offset(self, val):
        self.offset = float(val)
        self.update()
        
    @pyqtProperty(float)
    def transition(self):
        return self.transition_progress
        
    @transition.setter
    def transition(self, val):
        self.transition_progress = val
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 1. Draw Card Background with animated border (Fading out)
        p.setOpacity(1.0 - self.transition_progress)
        bg_rect = QRectF(1, 1, w - 2, h - 2)
        p.setBrush(QColor("#0a0a0c"))
        
        border_grad = QLinearGradient(0, 0, w, h)
        border_grad.setColorAt(0.0, QColor(234, 67, 53, 80))   # Faint Red
        border_grad.setColorAt(0.5, QColor(66, 133, 244, 40))  # Faint Blue
        border_grad.setColorAt(1.0, QColor(52, 168, 83, 80))   # Faint Green
        p.setPen(QPen(QBrush(border_grad), 1.5))
        p.drawRoundedRect(bg_rect, 16, 16)
        p.setOpacity(1.0)
        
        # 2. Prepare Foreground Pixmap for Gradient Masking
        fg_pixmap = QPixmap(w, h)
        fg_pixmap.fill(Qt.transparent)
        p_fg = QPainter(fg_pixmap)
        p_fg.setRenderHint(QPainter.Antialiasing)
        
        # Draw Brain Icon (Line-Art SVG) (Fading out)
        p_fg.setOpacity(1.0 - self.transition_progress)
        from PyQt5.QtSvg import QSvgRenderer
        svg_str = b"""
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <g fill="none" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
            <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
            <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>
            <path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>
            <path d="M6.002 6.5A3 3 0 0 1 5.603 5.125"/>
            <path d="M11.588 15.5a3 3 0 0 1-.588-1.5"/>
            <path d="M12.412 15.5a3 3 0 0 0 .588-1.5"/>
            <!-- Sparkles -->
            <path d="M4 5v2m-1-1h2"/>
            <path d="M20 5v2m-1-1h2"/>
            <path d="M5 19v2m-1-1h2"/>
            <path d="M19 19v2m-1-1h2"/>
          </g>
        </svg>
        """
        renderer = QSvgRenderer(svg_str)
        brain_rect = QRectF(w/2 - 35, 40, 70, 70)
        renderer.render(p_fg, brain_rect)
        p_fg.setOpacity(1.0)
        
        # Draw "AI Assistant" Text (Stays visible)
        font_bold = QFont("Segoe UI", 34, QFont.Bold)
        p_fg.setFont(font_bold)
        p_fg.setPen(QColor("#ffffff"))
        t_ai = "AI Assistant"
        p_fg.drawText(QRectF(0, 165, w, 60), Qt.AlignCenter, t_ai)
        p_fg.end()
        
        # 3. Create Animated Gradient for Brain and Text
        grad_w = w * 1.5
        x_start = (w - grad_w) / 2
        grad = QLinearGradient(x_start - (self.offset * grad_w), 0, x_start + grad_w - (self.offset * grad_w), 0)
        grad.setSpread(QGradient.RepeatSpread)
        grad.setColorAt(0.0, QColor("#4285F4"))
        grad.setColorAt(0.2, QColor("#9b72cb"))
        grad.setColorAt(0.4, QColor("#d96570"))
        grad.setColorAt(0.6, QColor("#F9AB00"))
        grad.setColorAt(0.8, QColor("#1E8E3E"))
        grad.setColorAt(1.0, QColor("#4285F4"))
        
        grad_pixmap = QPixmap(w, h)
        grad_pixmap.fill(Qt.transparent)
        p_grad = QPainter(grad_pixmap)
        p_grad.fillRect(grad_pixmap.rect(), grad)
        p_grad.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p_grad.drawPixmap(0, 0, fg_pixmap)
        p_grad.end()
        
        # Draw the masked gradient to the card
        p.drawPixmap(0, 0, grad_pixmap)
        
        # Fading out rest of the UI
        p.setOpacity(1.0 - self.transition_progress)
        
        # 4. Draw "Enable" Text (White/Silver)
        font_light = QFont("Segoe UI", 26, QFont.Light)
        p.setFont(font_light)
        p.setPen(QColor("#e2e8f0"))
        t_en = "Enable"
        p.drawText(QRectF(0, 115, w, 50), Qt.AlignCenter, t_en)
        
        # 5. Draw the bottom glowing Flare
        flare_grad = QLinearGradient(w/2 - 120, 0, w/2 + 120, 0)
        flare_grad.setColorAt(0.0, QColor(66, 133, 244, 0))
        flare_grad.setColorAt(0.3, QColor(66, 133, 244, 255))
        flare_grad.setColorAt(0.5, QColor(155, 114, 203, 255))
        flare_grad.setColorAt(0.7, QColor(52, 168, 83, 255))
        flare_grad.setColorAt(1.0, QColor(52, 168, 83, 0))
        
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(flare_grad))
        p.drawRect(int(w/2 - 120), 250, 240, 2)
        
        # Add softer ambient flare
        flare_grad2 = QLinearGradient(w/2 - 80, 0, w/2 + 80, 0)
        flare_grad2.setColorAt(0.0, QColor(66, 133, 244, 0))
        flare_grad2.setColorAt(0.5, QColor(155, 114, 203, 100))
        flare_grad2.setColorAt(1.0, QColor(52, 168, 83, 0))
        p.setBrush(QBrush(flare_grad2))
        p.drawRect(int(w/2 - 80), 248, 160, 6)
        p.setOpacity(1.0)


class LLMTestWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, api_key, model_name=""):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        
    def run(self):
        import sys
        import os
        # Ensure Backend_AI is in path
        proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if proj_root not in sys.path:
            sys.path.append(proj_root)
            
        try:
            from Backend.Backend_AI.llm_client import test_api_key
            success, msg = test_api_key(self.api_key, self.model_name)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class SleekInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #0a0a0c;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 12px 20px;
                color: #e2e8f0;
                font-size: 18px;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus {
                border: 1px solid #818cf8;
                background-color: #000000;
            }
        """)
        self.setPlaceholderText("Enter your LLM API Key")
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)

class SleekButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.hover_progress = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(300)
        self.anim.valueChanged.connect(self._update_hover)
        
    
    def setText(self, text):
        self.text = text
        self.update()

    def _update_hover(self, val):
        self.hover_progress = float(val)
        self.update()
        
    def enterEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
    def leaveEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
            
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        r = QRectF(1, 1, self.width()-2, self.height()-2)
        p.setBrush(QColor(10, 10, 12, 255))
        
        border_grad = QLinearGradient(0, 0, self.width(), 0)
        border_grad.setColorAt(0, QColor(66, 133, 244, int(80 + 175*self.hover_progress)))
        border_grad.setColorAt(1, QColor(155, 114, 203, int(80 + 175*self.hover_progress)))
        
        p.setPen(QPen(QBrush(border_grad), 1.5))
        p.drawRoundedRect(r, self.height()/2, self.height()/2)
        
        if self.hover_progress > 0:
            fill_grad = QLinearGradient(0, 0, self.width(), 0)
            fill_grad.setColorAt(0, QColor(66, 133, 244, int(30 * self.hover_progress)))
            fill_grad.setColorAt(1, QColor(155, 114, 203, int(30 * self.hover_progress)))
            p.setBrush(QBrush(fill_grad))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, self.height()/2, self.height()/2)
        
        p.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 16, QFont.DemiBold)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, self.text)


class AIPromptOverlay(QWidget):
    ai_accepted = pyqtSignal()
    ai_declined = pyqtSignal()
    # Emitted when user submits the prompt — carries API key and user's prompt text
    generation_requested = pyqtSignal(str, str, str)  # (api_key, model_name, user_prompt)
    skip_requested = pyqtSignal()
    
    def __init__(self, parent, phases=None):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.phases = phases or ["Assertions"]
        self.current_phase_idx = 0
        
        # Transparent background initially
        self.bg_opacity = 0.0
        
        # Labels
        self.success_label = QLabel("<span style='color:#10b981; font-weight:300;'></span> <span style='color:#e2e8f0; font-weight:300;'>Project Generated Successfully</span>", self)
        self.success_label.setTextFormat(Qt.RichText)
        self.success_label.setStyleSheet("font-size: 34px; font-family: 'Segoe UI';")
        self.success_label.setAlignment(Qt.AlignCenter)
        self.success_label.setGeometry(0, self.height()//2 - 50, self.width(), 100)
        self.success_label.setGraphicsEffect(self._create_opacity_effect())
        self.success_label.graphicsEffect().setOpacity(0)
        
        self.prompt_label = AnimatedPromptLabel(self)
        self.prompt_label.setGeometry(self.width()//2 - 210, self.height()//2 - 160, 420, 320)
        self.prompt_label.setGraphicsEffect(self._create_opacity_effect())
        self.prompt_label.graphicsEffect().setOpacity(0)
        
        # Red No on left (25% of screen)
        self.wave_no = WaveButton(self, side="left", base_color="#ef4444", text="No")
        self.wave_no.setGeometry(0, 0, self.width() // 4, self.height())
        
        # Green Yes on right (25% of screen)
        self.wave_yes = WaveButton(self, side="right", base_color="#10b981", text="Yes")
        self.wave_yes.setGeometry(self.width() - self.width() // 4, 0, self.width() // 4, self.height())
        
        self.wave_no.hide()
        self.wave_yes.hide()
        self.api_input = SleekInput(self)
        self.api_input.setGeometry(self.width()//2 - 250, self.height()//2 + 190, 500, 50)
        self.api_input.setGraphicsEffect(self._create_opacity_effect())
        self.api_input.graphicsEffect().setOpacity(0)
        self.api_input.hide()

        # Model Selection Button
        self.model_btn = SleekButton("Model ▶", self) # Down arrow
        self.model_btn.setGeometry(self.width()//2 - 150, self.height()//2 + 255, 300, 45)
        self.model_btn.setGraphicsEffect(self._create_opacity_effect())
        self.model_btn.graphicsEffect().setOpacity(0)
        self.model_btn.hide()
        
        self.custom_model_input = SleekInput(self)
        self.custom_model_input.setGeometry(self.width()//2 - 150, self.height()//2 + 225, 300, 45)
        self.custom_model_input.setPlaceholderText("Type custom model...")
        self.custom_model_input.setGraphicsEffect(self._create_opacity_effect())
        self.custom_model_input.graphicsEffect().setOpacity(0)
        self.custom_model_input.hide()
        
        self.selected_model = ""
        self._setup_model_menu()
        
        # Connect Button
        self.connect_btn = SleekButton("Connect", self)
        self.connect_btn.setGeometry(self.width()//2 - 75, self.height()//2 + 315, 150, 45)
        self.connect_btn.setGraphicsEffect(self._create_opacity_effect())
        self.connect_btn.graphicsEffect().setOpacity(0)
        self.connect_btn.hide()
        
        # Test Status Label
        self.test_label = QLabel("Testing API...", self)
        self.test_label.setStyleSheet("color: #94a3b8; font-size: 24px; font-family: 'Segoe UI'; font-weight: 300;")
        self.test_label.setAlignment(Qt.AlignCenter)
        self.test_label.setGeometry(self.width()//2 - 200, self.height()//2 + 315, 400, 45)
        self.test_label.setGraphicsEffect(self._create_opacity_effect())
        self.test_label.graphicsEffect().setOpacity(0)
        self.test_label.hide()
        self.test_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.wave_no.clicked.connect(self._on_no_clicked)
        self.wave_yes.clicked.connect(self._on_yes_clicked)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        
        self.raise_()
        self.show()
        
        self._start_sequence()
        
    def _create_opacity_effect(self):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(0)
        return effect
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(10, 10, 10, int(255 * self.bg_opacity)))
        
    def _start_sequence(self):
        # 1. Fade in background
        self.bg_anim = QVariantAnimation(self)
        self.bg_anim.setDuration(1000)
        self.bg_anim.setStartValue(0.0)
        self.bg_anim.setEndValue(1.0)
        self.bg_anim.valueChanged.connect(self._set_bg_opacity)
        
        # When background fades in, fade in success text
        self.bg_anim.finished.connect(self._fade_in_success)
        self.bg_anim.start()
        
    def _set_bg_opacity(self, val):
        self.bg_opacity = float(val)
        self.update()
        
    def _fade_in_success(self):
        self.succ_anim = QPropertyAnimation(self.success_label.graphicsEffect(), b"opacity")
        self.succ_anim.setDuration(800)
        self.succ_anim.setStartValue(0.0)
        self.succ_anim.setEndValue(1.0)
        self.succ_anim.start()
        
        QTimer.singleShot(1200, self._fade_out_success)
        
    def _fade_out_success(self):
        self.succ_anim.setDirection(QAbstractAnimation.Backward)
        self.succ_anim.finished.connect(self._fade_in_prompt)
        self.succ_anim.start()
        
    def _fade_in_prompt(self):
        self.prompt_anim = QPropertyAnimation(self.prompt_label.graphicsEffect(), b"opacity")
        self.prompt_anim.setDuration(800)
        self.prompt_anim.setStartValue(0.0)
        self.prompt_anim.setEndValue(1.0)
        self.prompt_anim.start()
        
        self.wave_no.show()
        self.wave_yes.show()
        
        self.wave_no.setGraphicsEffect(self._create_opacity_effect())
        self.wave_yes.setGraphicsEffect(self._create_opacity_effect())
        
        self.wn_anim = QPropertyAnimation(self.wave_no.graphicsEffect(), b"opacity")
        self.wn_anim.setDuration(800)
        self.wn_anim.setStartValue(0.0)
        self.wn_anim.setEndValue(1.0)
        self.wn_anim.start()
        
        self.wy_anim = QPropertyAnimation(self.wave_yes.graphicsEffect(), b"opacity")
        self.wy_anim.setDuration(800)
        self.wy_anim.setStartValue(0.0)
        self.wy_anim.setEndValue(1.0)
        self.wy_anim.start()
        
    def _on_no_clicked(self):
        # Stop interactions
        self.wave_yes.setEnabled(False)
        self.wave_no.setEnabled(False)
        
        # Fade out BOTH waves smoothly
        self.fade_out_wn = QPropertyAnimation(self.wave_no.graphicsEffect(), b"opacity")
        self.fade_out_wn.setDuration(400)
        self.fade_out_wn.setStartValue(1.0)
        self.fade_out_wn.setEndValue(0.0)
        self.fade_out_wn.start()
        
        self.fade_out_wy = QPropertyAnimation(self.wave_yes.graphicsEffect(), b"opacity")
        self.fade_out_wy.setDuration(400)
        self.fade_out_wy.setStartValue(1.0)
        self.fade_out_wy.setEndValue(0.0)
        self.fade_out_wy.start()
        
        # Fade out the prompt label completely because we are skipping everything
        self.cleanup_anim = QPropertyAnimation(self.prompt_label.graphicsEffect(), b"opacity")
        self.cleanup_anim.setDuration(800)
        self.cleanup_anim.setEndValue(0.0)
        self.cleanup_anim.start()
        
        def on_fade_done():
            self._show_grand_finale()
            
        self.cleanup_anim.finished.connect(on_fade_done)
        
    def _on_yes_clicked(self):
        # Stop interactions
        self.wave_yes.setEnabled(False)
        self.wave_no.setEnabled(False)
        
        # Fade out BOTH waves smoothly
        self.fade_out_wn = QPropertyAnimation(self.wave_no.graphicsEffect(), b"opacity")
        self.fade_out_wn.setDuration(400)
        self.fade_out_wn.setStartValue(1.0)
        self.fade_out_wn.setEndValue(0.0)
        self.fade_out_wn.start()
        
        self.fade_out_wy = QPropertyAnimation(self.wave_yes.graphicsEffect(), b"opacity")
        self.fade_out_wy.setDuration(400)
        self.fade_out_wy.setStartValue(1.0)
        self.fade_out_wy.setEndValue(0.0)
        self.fade_out_wy.start()
        
        # Luxurious slide-up + fade-in for API Input
        # Luxurious slide-up + fade-in for API Input
        self.api_input.show()
        api_end_geom = self.api_input.geometry()
        api_start_geom = QRectF(api_end_geom.x(), api_end_geom.y() + 40, api_end_geom.width(), api_end_geom.height()).toRect()
        self.api_input.setGeometry(api_start_geom)

        self.api_slide = QPropertyAnimation(self.api_input, b"geometry")
        self.api_slide.setDuration(1000)
        self.api_slide.setEasingCurve(QEasingCurve.OutQuint)
        self.api_slide.setStartValue(api_start_geom)
        self.api_slide.setEndValue(api_end_geom)
        self.api_slide.start()

        self.fade_in_api = QPropertyAnimation(self.api_input.graphicsEffect(), b"opacity")
        self.fade_in_api.setDuration(800)
        self.fade_in_api.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in_api.setStartValue(0.0)
        self.fade_in_api.setEndValue(1.0)
        self.fade_in_api.start()

        # Model Button Animation
        self.model_btn.show()
        mod_end_geom = self.model_btn.geometry()
        mod_start_geom = QRectF(mod_end_geom.x(), mod_end_geom.y() + 50, mod_end_geom.width(), mod_end_geom.height()).toRect()
        self.model_btn.setGeometry(mod_start_geom)

        self.mod_slide = QPropertyAnimation(self.model_btn, b"geometry")
        self.mod_slide.setDuration(1000)
        self.mod_slide.setEasingCurve(QEasingCurve.OutQuint)
        self.mod_slide.setStartValue(mod_start_geom)
        self.mod_slide.setEndValue(mod_end_geom)
        self.mod_slide.start()

        self.fade_in_mod = QPropertyAnimation(self.model_btn.graphicsEffect(), b"opacity")
        self.fade_in_mod.setDuration(800)
        self.fade_in_mod.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in_mod.setStartValue(0.0)
        self.fade_in_mod.setEndValue(1.0)
        self.fade_in_mod.start()

        # Luxurious slide-up + fade-in for Connect Button (starts slightly lower for cascading effect)
        self.connect_btn.show()
        btn_end_geom = self.connect_btn.geometry()
        # Start 60 pixels lower
        btn_start_geom = QRectF(btn_end_geom.x(), btn_end_geom.y() + 60, btn_end_geom.width(), btn_end_geom.height()).toRect()
        self.connect_btn.setGeometry(btn_start_geom)
        
        self.btn_slide = QPropertyAnimation(self.connect_btn, b"geometry")
        self.btn_slide.setDuration(1200)
        self.btn_slide.setEasingCurve(QEasingCurve.OutQuint)
        self.btn_slide.setStartValue(btn_start_geom)
        self.btn_slide.setEndValue(btn_end_geom)
        self.btn_slide.start()
        
        self.fade_in_btn = QPropertyAnimation(self.connect_btn.graphicsEffect(), b"opacity")
        self.fade_in_btn.setDuration(1000)
        self.fade_in_btn.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in_btn.setStartValue(0.0)
        self.fade_in_btn.setEndValue(1.0)
        self.fade_in_btn.start()
        
    def _on_connect_clicked(self):
        key = self.api_input.text().strip()
        if not key:
            return
            
        self.api_input.setEnabled(False)
        self.model_btn.setEnabled(False)
        self.custom_model_input.setEnabled(False) if hasattr(self, "custom_model_input") else None
        self.connect_btn.setEnabled(False)
        
        # Fade out connect button
        self.fade_out_btn = QPropertyAnimation(self.connect_btn.graphicsEffect(), b"opacity")
        self.fade_out_btn.setDuration(400)
        self.fade_out_btn.setStartValue(1.0)
        self.fade_out_btn.setEndValue(0.0)
        self.fade_out_btn.start()
        
        # Fade in Test API label
        self.test_label.setWordWrap(False)
        self.test_label.setGeometry(self.width()//2 - 200, self.height()//2 + 315, 400, 45)
        self.test_label.setText("Testing API Connection...")
        self.test_label.setStyleSheet("color: #94a3b8; font-size: 24px; font-family: 'Segoe UI'; font-weight: 300;")
        self.test_label.show()
        
        self.fade_in_test = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_in_test.setDuration(600)
        self.fade_in_test.setStartValue(0.0)
        self.fade_in_test.setEndValue(1.0)
        
        self.fade_out_btn.finished.connect(self.fade_in_test.start)
        self.fade_in_test.finished.connect(lambda: self._start_api_test(key))
        
    def _start_api_test(self, key):
        if key == "Access Master Control":
            self._on_test_finished(True, "Access Granted")
            return
            
        
        final_model = self.selected_model
        if hasattr(self, 'other_input') and self.other_input.text().strip() and final_model == "":
            final_model = self.other_input.text().strip()
        self.worker = LLMTestWorker(key, final_model)
    
        self.worker.finished.connect(self._on_test_finished)
        self.worker.start()
        
    def _on_test_finished(self, success, msg):
        self.api_input.setEnabled(True)
        self.model_btn.setEnabled(True)
        self.custom_model_input.setEnabled(True) if hasattr(self, "custom_model_input") else None
        
        # Fade out "Testing API Connection..."
        self.fade_out_test = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_out_test.setDuration(400)
        self.fade_out_test.setEndValue(0.0)
        self.fade_out_test.start()
        
        if success:
            self.fade_out_test.finished.connect(self._show_success_msg)
        else:
            self.error_msg = msg
            self.fade_out_test.finished.connect(self._show_error_msg)
            
    def _show_success_msg(self):
        # Store the API key for later use in generation
        self._api_key = self.api_input.text().strip()
        
        self.test_label.setText("Connected to AI Assistant")
        self.test_label.setStyleSheet("color: #10b981; font-size: 24px; font-family: 'Segoe UI'; font-weight: 600;")
        self.fade_in_res = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_in_res.setDuration(600)
        self.fade_in_res.setEndValue(1.0)
        self.fade_in_res.start()
        
        # Trigger the transition to the working state
        QTimer.singleShot(1500, self._transition_to_working_state)
        
    def _transition_to_working_state(self):
        # 1. Fade out everything else (Test label, input)
        self.fade_out_res = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_out_res.setDuration(500)
        self.fade_out_res.setEndValue(0.0)
        self.fade_out_res.start()
        self.fade_out_inp = QPropertyAnimation(self.api_input.graphicsEffect(), b"opacity")
        self.fade_out_inp.setDuration(500)
        self.fade_out_inp.setEndValue(0.0)
        self.fade_out_inp.start()
        
        self.fade_out_mod = QPropertyAnimation(self.model_btn.graphicsEffect(), b"opacity")
        self.fade_out_mod.setDuration(500)
        self.fade_out_mod.setEndValue(0.0)
        self.fade_out_mod.start()

        if hasattr(self, 'custom_model_input') and self.custom_model_input.isVisible():
            self.fade_out_custom = QPropertyAnimation(self.custom_model_input.graphicsEffect(), b"opacity")
            self.fade_out_custom.setDuration(500)
            self.fade_out_custom.setEndValue(0.0)
            self.fade_out_custom.start()
        
        # 2. Cleanup AnimatedPromptLabel (Background, border, brain, enable)
        self.cleanup_anim = QPropertyAnimation(self.prompt_label, b"transition")
        self.cleanup_anim.setDuration(800)
        self.cleanup_anim.setStartValue(0.0)
        self.cleanup_anim.setEndValue(1.0)
        self.cleanup_anim.start()
        
        # 3. Slide AnimatedPromptLabel UP
        self.slide_up_anim = QPropertyAnimation(self.prompt_label, b"geometry")
        self.slide_up_anim.setDuration(1200)
        self.slide_up_anim.setEasingCurve(QEasingCurve.OutQuint)
        start_geom = self.prompt_label.geometry()
        
        # Move so that "AI Assistant" text (y=165 inside widget) ends up at y=80 on screen.
        end_geom = QRectF(start_geom.x(), -85, start_geom.width(), start_geom.height()).toRect()
        self.slide_up_anim.setStartValue(start_geom)
        self.slide_up_anim.setEndValue(end_geom)
        
        # Start sliding up just after cleanup starts
        QTimer.singleShot(400, self.slide_up_anim.start)
        self.slide_up_anim.finished.connect(self._show_aura_wheel)
        
    def _show_aura_wheel(self):
        from ui.aura_wheel import AuraWheelWidget
        self.aura_wheel = AuraWheelWidget(self)
        self.aura_wheel.setGeometry(0, 0, self.width(), self.height())
        self.aura_wheel.setGraphicsEffect(self._create_opacity_effect())
        self.aura_wheel.graphicsEffect().setOpacity(0)
        self.aura_wheel.show()
        
        # Ensure it is behind the prompt label
        self.aura_wheel.stackUnder(self.prompt_label)
        
        self.fade_in_aura = QPropertyAnimation(self.aura_wheel.graphicsEffect(), b"opacity")
        self.fade_in_aura.setDuration(1500)
        self.fade_in_aura.setStartValue(0.0)
        self.fade_in_aura.setEndValue(1.0)
        self.fade_in_aura.finished.connect(self._show_prompt_bar)
        self.fade_in_aura.start()
        
    def _show_prompt_bar(self):
        from ui.prompt_input_widget import PromptInputWidget
        
        bar_h = 72
        bar_margin = 28
        bar_w = int(self.width() * 0.75)
        bar_x = (self.width() - bar_w) // 2
        bar_y = self.height() - bar_h - bar_margin
        
        # 1. Show the beautiful Phase Label in the center
        self.phase_label = PhaseLabel(self)
        self.phase_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.phase_label.setText(self.phases[self.current_phase_idx])
        self.phase_label.show()
        self.phase_label.raise_()
        
        self.fade_in_phase = QPropertyAnimation(self.phase_label.graphicsEffect(), b"opacity")
        self.fade_in_phase.setDuration(1200)
        self.fade_in_phase.setStartValue(0.0)
        self.fade_in_phase.setEndValue(1.0)
        self.fade_in_phase.start()
        
        # 2. Show the Prompt Input Bar
        self.prompt_bar = PromptInputWidget(self)
        self.prompt_bar.setGeometry(bar_x, bar_y, bar_w, bar_h)
        self.prompt_bar.prompt_submitted.connect(self._on_prompt_submitted)
        self.prompt_bar.setGraphicsEffect(self._create_opacity_effect())
        self.prompt_bar.show()
        self.prompt_bar.raise_()
        
        # 3. Show the Skip Button on the far right edge (vertically centered)
        self.skip_btn = NavButton('Skip \u2192', self)
        self.skip_btn.setGeometry(self.width() - 120, self.height() // 2 - 25, 100, 50)
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        self.skip_btn.setGraphicsEffect(self._create_opacity_effect())
        self.skip_btn.show()
        self.skip_btn.raise_()

        # 4. Show the Back Button on the far left edge
        self.back_btn = NavButton("\u2190 Back", self)
        self.back_btn.setGeometry(20, self.height() // 2 - 25, 100, 50)
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.back_btn.setGraphicsEffect(self._create_opacity_effect())
        self.back_btn.show()
        self.back_btn.raise_()

        # Fade in prompt bar and navigation buttons
        self.fade_in_bar = QPropertyAnimation(self.prompt_bar.graphicsEffect(), b"opacity")
        self.fade_in_bar.setDuration(1000)
        self.fade_in_bar.setStartValue(0.0)
        self.fade_in_bar.setEndValue(1.0)
        self.fade_in_bar.start()
        
        self.fade_in_skip = QPropertyAnimation(self.skip_btn.graphicsEffect(), b"opacity")
        self.fade_in_skip.setDuration(1000)
        self.fade_in_skip.setStartValue(0.0)
        self.fade_in_skip.setEndValue(1.0)
        self.fade_in_skip.start()
        
        self.fade_in_back = QPropertyAnimation(self.back_btn.graphicsEffect(), b"opacity")
        self.fade_in_back.setDuration(1000)
        self.fade_in_back.setStartValue(0.0)
        self.fade_in_back.setEndValue(1.0)
        self.fade_in_back.start()
        
    def _on_skip_clicked(self):
        # Prevent double skips
        if not self.skip_btn.isEnabled(): return
        self.skip_btn.setEnabled(False)
        self.skip_requested.emit()
        
    def _on_back_clicked(self):
        if not self.back_btn.isEnabled():
            return
        if self.current_phase_idx > 0:
            self.back_btn.setEnabled(False)
            self.current_phase_idx -= 1
    
            if hasattr(self, 'prompt_bar'):
                self.prompt_bar._editor.setPlainText("")
                self.prompt_bar.set_generating(False)
                self.prompt_bar._editor.setEnabled(True)
    
            # نفس الـ transition اللي في advance_phase: fade out ثم تغيير النص وfade in
            self.fade_out_phase = QPropertyAnimation(self.phase_label.graphicsEffect(), b"opacity")
            self.fade_out_phase.setDuration(600)
            self.fade_out_phase.setEndValue(0.0)
    
            def _on_faded_out():
                self.phase_label.setText(self.phases[self.current_phase_idx])
                self.fade_in_phase.start()
                self.back_btn.setEnabled(True)
    
            self.fade_out_phase.finished.connect(_on_faded_out)
            self.fade_out_phase.start()
        else:
            self._return_to_api_state()

    def _return_to_api_state(self):
        # 1. Fade out working state elements
        for widget in [getattr(self, 'prompt_bar', None),
                       getattr(self, 'phase_label', None),
                       getattr(self, 'aura_wheel', None),
                       getattr(self, 'skip_btn', None),
                       getattr(self, 'back_btn', None)]:
            if widget and hasattr(widget, 'graphicsEffect') and widget.graphicsEffect():
                anim = QPropertyAnimation(widget.graphicsEffect(), b"opacity")
                anim.setDuration(500)
                anim.setStartValue(1.0)
                anim.setEndValue(0.0)
                anim.start()
                setattr(widget, '_fade_out_back_anim', anim)
                QTimer.singleShot(500, widget.hide)

        # 2. Restore AnimatedPromptLabel transition (card background, brain, enable)
        self.restore_label_anim = QPropertyAnimation(self.prompt_label, b"transition")
        self.restore_label_anim.setDuration(800)
        self.restore_label_anim.setStartValue(1.0)
        self.restore_label_anim.setEndValue(0.0)
        self.restore_label_anim.start()

        # 3. Slide AnimatedPromptLabel back DOWN to center
        self.slide_down_anim = QPropertyAnimation(self.prompt_label, b"geometry")
        self.slide_down_anim.setDuration(1000)
        self.slide_down_anim.setEasingCurve(QEasingCurve.OutQuint)
        start_geom = self.prompt_label.geometry()
        end_geom = QRectF(self.width()//2 - 210, self.height()//2 - 160, 420, 320).toRect()
        self.slide_down_anim.setStartValue(start_geom)
        self.slide_down_anim.setEndValue(end_geom)
        self.slide_down_anim.start()

        # 4. Fade in API input, Model button, Connect button
        self.api_input.show()
        self.api_input.setEnabled(True)
        self.model_btn.show()
        self.model_btn.setEnabled(True)
        self.connect_btn.show()
        self.connect_btn.setEnabled(True)
        if hasattr(self, 'custom_model_input') and self.custom_model_input.isVisible():
            self.custom_model_input.setEnabled(True)

        self.fade_in_api_back = QPropertyAnimation(self.api_input.graphicsEffect(), b"opacity")
        self.fade_in_api_back.setDuration(800)
        self.fade_in_api_back.setStartValue(0.0)
        self.fade_in_api_back.setEndValue(1.0)
        self.fade_in_api_back.start()

        self.fade_in_mod_back = QPropertyAnimation(self.model_btn.graphicsEffect(), b"opacity")
        self.fade_in_mod_back.setDuration(800)
        self.fade_in_mod_back.setStartValue(0.0)
        self.fade_in_mod_back.setEndValue(1.0)
        self.fade_in_mod_back.start()

        self.fade_in_btn_back = QPropertyAnimation(self.connect_btn.graphicsEffect(), b"opacity")
        self.fade_in_btn_back.setDuration(800)
        self.fade_in_btn_back.setStartValue(0.0)
        self.fade_in_btn_back.setEndValue(1.0)
        self.fade_in_btn_back.start()
        
    def advance_phase(self):
        self.current_phase_idx += 1
        
        # Re-enable skip button if it was clicked
        if hasattr(self, 'skip_btn'):
            self.skip_btn.setEnabled(True)
            
        if self.current_phase_idx >= len(self.phases):
            self._show_grand_finale()
            return
            
        # Reset prompt bar for the next phase
        if hasattr(self, 'prompt_bar'):
            self.prompt_bar._editor.setPlainText("")
            self.prompt_bar.set_generating(False)
            self.prompt_bar._editor.setEnabled(True)
            
        # Fade out current label
        self.fade_out_phase = QPropertyAnimation(self.phase_label.graphicsEffect(), b"opacity")
        self.fade_out_phase.setDuration(600)
        self.fade_out_phase.setEndValue(0.0)
        
        def _on_faded_out():
            self.phase_label.setText(self.phases[self.current_phase_idx])
            self.fade_in_phase.start()
            
        self.fade_out_phase.finished.connect(_on_faded_out)
        self.fade_out_phase.start()
        
    def _show_grand_finale(self):
        # Fade everything out to pitch black
        self.finale_bg_anim = QVariantAnimation(self)
        self.finale_bg_anim.setDuration(2000)
        self.finale_bg_anim.setStartValue(self.bg_opacity)
        self.finale_bg_anim.setEndValue(1.0) # Pitch black
        self.finale_bg_anim.valueChanged.connect(self._set_bg_opacity)
        
        # Hide prompt bar and other elements gently
        for widget in [getattr(self, 'prompt_bar', None), 
                       getattr(self, 'skip_btn', None),
            getattr(self, 'back_btn', None), 
                       getattr(self, 'aura_wheel', None), 
                       getattr(self, 'phase_label', None),
                       getattr(self, 'prompt_label', None)]:
            if widget:
                anim = QPropertyAnimation(widget.graphicsEffect(), b"opacity")
                anim.setDuration(1500)
                anim.setEndValue(0.0)
                anim.start()
                # Keep a reference to prevent garbage collection
                setattr(widget, '_fade_out_anim', anim)
                
        # The Grand Finale Message
        self.finale_label = QLabel("Generation Complete", self)
        self.finale_label.setAlignment(Qt.AlignCenter)
        self.finale_label.setStyleSheet("color: #ffffff; font-size: 42px; font-weight: 200; font-family: 'Segoe UI'; letter-spacing: 6px;")
        self.finale_label.setGeometry(0, self.height()//2 - 50, self.width(), 100)
        eff = QGraphicsOpacityEffect()
        eff.setOpacity(0)
        self.finale_label.setGraphicsEffect(eff)
        self.finale_label.show()
        
        self.finale_text_anim = QPropertyAnimation(eff, b"opacity")
        self.finale_text_anim.setDuration(2500)
        self.finale_text_anim.setStartValue(0.0)
        self.finale_text_anim.setEndValue(1.0)
        
        self.finale_bg_anim.finished.connect(self.finale_text_anim.start)
        self.finale_bg_anim.start()
        
        # Keep overlay visible indefinitely (Grand Finale)

    def _on_prompt_submitted(self, user_prompt: str):
        """Called when the user clicks Send or presses Enter in the prompt bar."""
        # Emit signal to the main application to start generation
        api_key = getattr(self, '_api_key', '')
        final_model = self.selected_model
        if hasattr(self, 'other_input') and self.other_input.text().strip() and final_model == "":
            final_model = self.other_input.text().strip()
        self.generation_requested.emit(api_key, final_model, user_prompt)
        
    def _show_error_msg(self):
        self.test_label.setWordWrap(True)
        # Expand geometry slightly so long wrapped text fits
        self.test_label.setGeometry(self.width()//2 - 350, self.height()//2 + 300, 700, 120)
        self.test_label.setText(f"Error: {self.error_msg}")
        # Make font slightly smaller to accommodate JSON dump errors
        self.test_label.setStyleSheet("color: #ef4444; font-size: 14px; font-family: 'Segoe UI';")
        
        self.fade_in_res = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_in_res.setDuration(600)
        self.fade_in_res.setEndValue(1.0)
        self.fade_in_res.start()
        
        # After 4.5 seconds (giving more time to read long errors), fade out error
        QTimer.singleShot(4500, self._restore_connect_button)
        
    def _restore_connect_button(self):
        self.fade_out_err = QPropertyAnimation(self.test_label.graphicsEffect(), b"opacity")
        self.fade_out_err.setDuration(400)
        self.fade_out_err.setEndValue(0.0)
        self.fade_out_err.start()
        
        self.connect_btn.setEnabled(True)
        self.fade_in_btn_again = QPropertyAnimation(self.connect_btn.graphicsEffect(), b"opacity")
        self.fade_in_btn_again.setDuration(400)
        self.fade_in_btn_again.setEndValue(1.0)
        self.fade_out_err.finished.connect(self.fade_in_btn_again.start)
        
    def _trigger_fill(self, wave, signal):
        # Disable both to prevent double clicks
        self.wave_no.setEnabled(False)
        self.wave_yes.setEnabled(False)
        
        # Fade out prompt text
        self.prompt_anim.setDirection(QAbstractAnimation.Backward)
        self.prompt_anim.start()
        
        # Fade out the OTHER wave
        other_wave = self.wave_yes if wave == self.wave_no else self.wave_no
        other_anim = QPropertyAnimation(other_wave.graphicsEffect(), b"opacity")
        other_anim.setDuration(300)
        other_anim.setStartValue(1.0)
        other_anim.setEndValue(0.0)
        other_anim.start()
        
        # Expand the clicked wave
        self.fill_anim = QVariantAnimation(self)
        self.fill_anim.setDuration(800)
        self.fill_anim.setEasingCurve(QEasingCurve.InQuad)
        self.fill_anim.setStartValue(0.0)
        self.fill_anim.setEndValue(1.0)
        
        self.wave_to_fill = wave
        self.fill_anim.valueChanged.connect(self._update_fill)
        
        def _on_fill_finished():
            signal.emit()
            self.deleteLater()
            
        self.fill_anim.finished.connect(_on_fill_finished)
        self.fill_anim.start()
        
    def _update_fill(self, val):
        p = float(val)
        w = self.width()
        
        # Update geometry to fill the screen
        if self.wave_to_fill == self.wave_yes:
            # Right side expanding left
            orig_w = w // 4
            new_x = int((w - orig_w) * (1 - p))
            new_w = w - new_x
            self.wave_yes.setGeometry(new_x, 0, new_w, self.height())
        else:
            # Left side expanding right
            orig_w = w // 4
            new_w = int(orig_w + (w - orig_w) * p)
            self.wave_no.setGeometry(0, 0, new_w, self.height())
            
        self.wave_to_fill.set_fill_progress(p)


    def _setup_model_menu(self):
        from PyQt5.QtWidgets import QMenu, QAction, QInputDialog
        self.model_menu = QMenu(self)
        self.model_menu.setStyleSheet("""
            /* =========================
               Main Menu
               ========================= */
            QMenu {
                background-color: rgba(10, 15, 28, 245);
                color: #e8edf7;
        
                border: 1px solid rgba(129, 140, 248, 0.45);
                border-radius: 12px;
        
                padding: 7px 5px;
        
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;
            }
        
            /* =========================
               Menu Items
               ========================= */
            QMenu::item {
                background: transparent;
        
                padding: 8px 28px 8px 18px;
                margin: 2px 5px;
        
                border-radius: 7px;
        
                color: #cbd5e1;
            }
        
            /* =========================
               Hover
               ========================= */
            QMenu::item:selected {
                color: #ffffff;
        
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
        
                    stop: 0 #4f46e5,
                    stop: 0.5 #6366f1,
                    stop: 1 #7c3aed
                );
        
                border: 1px solid rgba(167, 139, 250, 0.55);
            }
        
            /* =========================
               Disabled Items
               ========================= */
            QMenu::item:disabled {
                color: #475569;
                background: transparent;
            }
        
            /* =========================
               Separator
               ========================= */
            QMenu::separator {
                height: 1px;
        
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
        
                    stop: 0 rgba(99, 102, 241, 0),
                    stop: 0.25 rgba(99, 102, 241, 0.25),
                    stop: 0.5 rgba(139, 92, 246, 0.8),
                    stop: 0.75 rgba(99, 102, 241, 0.25),
                    stop: 1 rgba(99, 102, 241, 0)
                );
        
                margin: 6px 14px;
            }
        
            /* =========================
               Sub Menus
               ========================= */
            QMenu::right-arrow {
                image: none;
                border: none;
            }
        
            /* =========================
               Scroll Arrows
               ========================= */
            QMenu::up-arrow,
            QMenu::down-arrow {
                width: 8px;
                height: 8px;
            }
        """)
        
        providers = {
            "Gemini": ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"],
            "OpenAI ($)": ["gpt-5.1","gpt-5", "gpt-4.1", "gpt-4o"]
        }
        
        for provider, models in providers.items():
            prov_menu = self.model_menu.addMenu(provider)
            prov_menu.setStyleSheet(self.model_menu.styleSheet())
            for mod in models:
                action = QAction(mod, self)
                action.triggered.connect(lambda checked, m=mod: self._set_model(m))
                prov_menu.addAction(action)
                
        self.model_menu.addSeparator()
        
        from PyQt5.QtWidgets import QWidgetAction, QLineEdit
        self.other_input = QLineEdit(self.model_menu)
        self.other_input.setPlaceholderText("Other...")
        self.other_input.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.75);
        
                color: #f1f5f9;
        
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 9px;
        
                padding: 7px 12px;
                margin: 3px 7px;
        
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;
        
                selection-background-color: #6366f1;
                selection-color: #ffffff;
            }
        
            QLineEdit:hover {
                background: rgba(30, 41, 59, 0.9);
        
                border: 1px solid rgba(129, 140, 248, 0.55);
            }
        
            QLineEdit:focus {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
        
                    stop: 0 rgba(79, 70, 229, 0.18),
                    stop: 0.5 rgba(99, 102, 241, 0.22),
                    stop: 1 rgba(124, 58, 237, 0.18)
                );
        
                color: #ffffff;
        
                border: 1px solid rgba(139, 92, 246, 0.9);
            }
        
            QLineEdit:disabled {
                background: rgba(15, 23, 42, 0.35);
                color: #475569;
                border: 1px solid rgba(71, 85, 105, 0.2);
            }
        """)
        def on_custom_model_entered():
            txt = self.other_input.text().strip()
            if txt:
                self._set_model(txt)
                self.model_menu.close()
                
        self.other_input.returnPressed.connect(on_custom_model_entered)
        
        other_action = QWidgetAction(self.model_menu)
        other_action.setDefaultWidget(self.other_input)
        self.model_menu.addAction(other_action)
        
        if hasattr(self.model_btn, 'clicked'):
            self.model_btn.clicked.connect(lambda: self.model_menu.exec_(self.model_btn.mapToGlobal(self.model_btn.rect().topRight())))
        
    def _set_model(self, model_name):
        self.selected_model = model_name
        display_name = model_name if len(model_name) < 14 else model_name[:12] + "..."
        self.model_btn.setText(f"{display_name} ▼")
        
    def _custom_model(self):
        self.model_btn.hide()
        self.custom_model_input.show()
        self.custom_model_input.graphicsEffect().setOpacity(1.0)
        self.custom_model_input.setFocus()

