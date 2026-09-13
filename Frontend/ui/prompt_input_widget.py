"""
Prompt Input Widget
===================
A premium floating prompt bar styled after Gemini / ChatGPT.
Appears at the bottom of the screen after the AI connection is established.

Emits:
    prompt_submitted(str)  — the user's typed prompt (can be empty string)
"""

from PyQt5.QtWidgets import QWidget, QTextEdit, QGraphicsOpacityEffect, QSizePolicy
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QRectF, QPointF, QSize, QVariantAnimation
)
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush, QFont,
    QPainterPath, QTextOption, QFontMetrics
)
from PyQt5.QtCore import QThread, pyqtSignal

class STTWorker(QThread):
    partial_result = pyqtSignal(str)
    final_result = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._running = True
        
    def stop(self):
        self._running = False
        
    def run(self):
        try:
            import vosk
            import sounddevice as sd
            import queue
            import json
            
            q = queue.Queue()
            def callback(indata, frames, time, status):
                if status:
                    print(status)
                q.put(bytes(indata))
                
            # Auto-downloads small en-us model if not present (~40MB)
            model = vosk.Model(lang='en-us')
            
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                   channels=1, callback=callback):
                rec = vosk.KaldiRecognizer(model, 16000)
                full_text = ""
                
                while self._running:
                    try:
                        data = q.get(timeout=0.1)
                    except queue.Empty:
                        continue
                        
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get('text', '')
                        if text:
                            full_text += text + " "
                            self.final_result.emit(full_text.strip())
                    else:
                        partial = json.loads(rec.PartialResult())
                        p_text = partial.get('partial', '')
                        if p_text:
                            self.partial_result.emit((full_text + p_text).strip())
                            
                # User stopped recording
                final_res = json.loads(rec.FinalResult())
                f_text = final_res.get('text', '')
                if f_text:
                    full_text += f_text
                self.final_result.emit(full_text.strip())
                
        except Exception as e:
            self.error.emit(str(e))


class _GlassTextEdit(QTextEdit):
    """
    A transparent QTextEdit that renders custom placeholder text
    and intercepts Enter/Shift+Enter.
    """
    enter_pressed = pyqtSignal()

    PLACEHOLDER = (
        "Describe what you need (optional)"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(0)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 15px;
                font-family: 'Segoe UI';
                padding: 0px;
            }
            QScrollBar { width: 0px; height: 0px; }
        """)
        self.document().setDocumentMargin(0)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter = new line
                super().keyPressEvent(event)
            else:
                # Enter = submit
                self.enter_pressed.emit()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw placeholder if empty
        if not self.toPlainText():
            p = QPainter(self.viewport())
            p.setRenderHint(QPainter.Antialiasing)
            font = QFont("Segoe UI", 14)
            font.setItalic(True)
            p.setFont(font)
            p.setPen(QColor(120, 130, 150, 180))
            opt = QTextOption(Qt.AlignLeft | Qt.AlignVCenter)
            opt.setWrapMode(QTextOption.WordWrap)
            p.drawText(QRectF(self.viewport().rect()), self.PLACEHOLDER, opt)


class PromptInputWidget(QWidget):
    """
    Floating prompt bar — bottom of screen, Gemini/GPT style.
    """
    prompt_submitted = pyqtSignal(str)   # emits the typed text (or "" if empty)

    # Colors for the gradient border (matching the Aura Wheel)
    _GRAD_COLORS = [
        (0.0, QColor(255, 105, 180, 80)),   # Pink (faint)
        (0.4, QColor(255, 165,   0, 80)),   # Orange
        (0.6, QColor( 52, 168,  83, 80)),   # Green
        (1.0, QColor(  0, 255, 255, 80)),   # Cyan (faint)
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._is_generating = False
        self._spin_angle = 0.0
        # Spinner animation for generating state
        self._spin_anim = QVariantAnimation(self)
        self._spin_anim.setDuration(1000)
        self._spin_anim.setStartValue(0.0)
        self._spin_anim.setEndValue(360.0)
        self._spin_anim.setLoopCount(-1)
        self._spin_anim.valueChanged.connect(self._on_spin)
        self._build_ui()

    def _on_spin(self, val):
        self._spin_angle = float(val)
        self.update()

    def set_generating(self, generating: bool):
        """Switch between normal and generating (spinning) state."""
        self._is_generating = generating
        self._editor.setEnabled(not generating)
        if generating:
            self._editor.setPlainText("")
            self._spin_anim.start()
        else:
            self._spin_anim.stop()
        self.update()

    def set_result(self, success: bool, message: str):
        """Show success or error result in the editor."""
        self.set_generating(False)
        self._editor.setEnabled(False)
        prefix = "✅  " if success else "❌  "
        self._editor.setPlainText(prefix + message)

    def _build_ui(self):
        # Text area
        self._editor = _GlassTextEdit(self)
        self._editor.enter_pressed.connect(self._on_submit)

        # Send button hover state
        self._send_hovered = False
        self._mic_hovered = False
        self._is_recording = False
        self.setMouseTracking(True)

    def showEvent(self, event):
        super().showEvent(event)
        self._layout_children()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_children()

    def _layout_children(self):
        w, h = self.width(), self.height()
        pad = 24
        btn_size = 38
        # Editor takes full width minus padding and buttons (send + mic + spacing)
        self._editor.setGeometry(
            pad, (h - 56) // 2,
            w - pad * 2 - btn_size * 2 - 20,
            56
        )

    def _send_button_rect(self):
        w, h = self.width(), self.height()
        btn_size = 38
        pad = 24
        bx = w - pad - btn_size
        by = (h - btn_size) // 2
        return QRectF(bx, by, btn_size, btn_size)

    def _mic_button_rect(self):
        w, h = self.width(), self.height()
        btn_size = 38
        pad = 24
        # Place it to the left of the send button with some spacing
        bx = w - pad - btn_size * 2 - 12
        by = (h - btn_size) // 2
        return QRectF(bx, by, btn_size, btn_size)

    def mousePressEvent(self, event):
        if self._send_button_rect().contains(event.pos()):
            self._on_submit()
        elif self._mic_button_rect().contains(event.pos()):
            self._on_mic_clicked()
        else:
            self._editor.setFocus()

    def mouseMoveEvent(self, event):
        was_send = self._send_hovered
        was_mic = self._mic_hovered
        
        self._send_hovered = self._send_button_rect().contains(event.pos())
        self._mic_hovered = self._mic_button_rect().contains(event.pos())
        
        if was_send != self._send_hovered or was_mic != self._mic_hovered:
            self.update()

    def _on_mic_clicked(self):
        if self._is_generating: return
        
        if self._is_recording:
            # Stop recording
            if hasattr(self, '_stt_worker'):
                self._stt_worker.stop()
                self._stt_worker.wait(1000)
            self._is_recording = False
            self.update()
            return
            
        self._is_recording = True
        self.update()
        
        self._pre_record_text = self._editor.toPlainText().strip()
        
        self._stt_worker = STTWorker()
        self._stt_worker.partial_result.connect(self._on_stt_live)
        self._stt_worker.final_result.connect(self._on_stt_live)
        self._stt_worker.error.connect(self._on_stt_error)
        self._stt_worker.start()
        
    def _on_stt_live(self, text: str):
        if not text: return
        
        new_text = f"{self._pre_record_text} {text}".strip() if self._pre_record_text else text
        self._editor.setPlainText(new_text)
        
        # Scroll to bottom
        cursor = self._editor.textCursor()
        from PyQt5.QtGui import QTextCursor
        cursor.movePosition(QTextCursor.End)
        self._editor.setTextCursor(cursor)
        
    def _on_stt_error(self, err: str):
        self._is_recording = False
        self.update()
        print(f"STT Error: {err}")

    def _on_submit(self):
        text = self._editor.toPlainText().strip()
        self.prompt_submitted.emit(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2  # pill radius

        # --- Background (dark glass pill) ---
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(0, 0, w, h), r, r)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(12, 13, 18, 230))
        p.drawPath(bg_path)

        # --- Gradient border (glows brighter while generating) ---
        alpha_mult = 2.5 if self._is_generating else 1.0
        border_grad = QLinearGradient(0, 0, w, 0)
        for pos, color in self._GRAD_COLORS:
            c = QColor(color)
            c.setAlpha(min(255, int(color.alpha() * alpha_mult)))
            border_grad.setColorAt(pos, c)

        p.setPen(QPen(QBrush(border_grad), 2.0 if self._is_generating else 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(bg_path)

        # --- Button area ---
        btn = self._send_button_rect()
        cx, cy_ = btn.center().x(), btn.center().y()
        btn_r = btn.width() / 2

        if self._is_generating:
            # Draw spinning gradient ring (generating indicator)
            import math
            p.setPen(Qt.NoPen)
            dot_count = 8
            for i in range(dot_count):
                angle = math.radians(self._spin_angle + i * (360 / dot_count))
                dx = cx + math.cos(angle) * btn_r * 0.65
                dy = cy_ + math.sin(angle) * btn_r * 0.65
                # Fade older dots
                alpha = int(255 * (i + 1) / dot_count)
                # Color cycles through aura palette
                hue = int(self._spin_angle + i * (360 / dot_count)) % 360
                c = QColor.fromHsv(hue, 200, 255, alpha)
                p.setBrush(c)
                dot_r = btn_r * 0.18
                p.drawEllipse(QPointF(dx, dy), dot_r, dot_r)
        else:
            # --- Mic Button ---
            mic_rect = self._mic_button_rect()
            mx, my = mic_rect.center().x(), mic_rect.center().y()
            mic_r = btn_r
            
            # Hover effect for mic
            if self._mic_hovered:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 20))
                p.drawEllipse(mic_rect)
                
            p.setPen(QPen(QColor(160, 170, 180) if not self._is_recording else QColor(239, 68, 68), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            
            # Draw mic (pill shape for body, arc for stand)
            p.drawRoundedRect(QRectF(mx - mic_r*0.2, my - mic_r*0.4, mic_r*0.4, mic_r*0.6), mic_r*0.2, mic_r*0.2)
            p.drawArc(QRectF(mx - mic_r*0.4, my - mic_r*0.1, mic_r*0.8, mic_r*0.6), 180 * 16, 180 * 16)
            p.drawLine(QPointF(mx, my + mic_r*0.5), QPointF(mx, my + mic_r*0.7))

            # --- Send Button (Blue circle + Thin right arrow) ---
            circle_color = QColor(0, 110, 220, 255) if self._send_hovered else QColor(0, 132, 255, 255)
            p.setPen(Qt.NoPen)
            p.setBrush(circle_color)
            p.drawEllipse(btn)

            # Thin Right Arrow icon (→)
            arrow_pen = QPen(QColor("#ffffff"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(arrow_pen)
            p.setBrush(Qt.NoBrush)
            
            p.drawLine(QPointF(cx - btn_r * 0.3, cy_), QPointF(cx + btn_r * 0.3, cy_))
            p.drawLine(QPointF(cx + btn_r * 0.3, cy_), QPointF(cx + btn_r * 0.0, cy_ - btn_r * 0.3))
            p.drawLine(QPointF(cx + btn_r * 0.3, cy_), QPointF(cx + btn_r * 0.0, cy_ + btn_r * 0.3))
