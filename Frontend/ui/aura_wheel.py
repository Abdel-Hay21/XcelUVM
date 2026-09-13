from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QVariantAnimation, Qt, QRectF, QPointF, QEasingCurve, QAbstractAnimation
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush, QFont, QPainterPath
import math

class AuraWheelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pulse_alpha = 1.0
        self.task_name = "Assertions"
        
        # Soft pulsating animation for the glow using a sine wave
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(4000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(math.pi * 2)
        self.anim.setLoopCount(-1) # infinite
        self.anim.valueChanged.connect(self._update_pulse)
        self.anim.start()

    def _update_pulse(self, val):
        # Calculate a smooth pulse between 0.3 and 1.0 using sine wave
        norm = (math.sin(float(val)) + 1.0) / 2.0
        self.pulse_alpha = 0.3 + (0.7 * norm)
        self.update()

    def set_task_name(self, name):
        self.task_name = name
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx = w / 2
        cy = 80 # Matches the final resting Y coordinate of 'AI Assistant' text
        
        # The beautiful color gradient
        grad = QLinearGradient(cx - 300, 0, cx + 300, 0)
        grad.setColorAt(0.0, QColor(255, 105, 180, 0))    # Transparent Pink
        grad.setColorAt(0.1, QColor(255, 105, 180, 255))  # Pink/Magenta
        grad.setColorAt(0.3, QColor(255, 165, 0, 255))    # Orange
        grad.setColorAt(0.5, QColor(255, 255, 0, 255))    # Yellow
        grad.setColorAt(0.7, QColor(52, 168, 83, 255))    # Green
        grad.setColorAt(0.9, QColor(0, 255, 255, 255))    # Cyan
        grad.setColorAt(1.0, QColor(0, 255, 255, 0))      # Transparent Cyan
        
        p.setCompositionMode(QPainter.CompositionMode_Screen)
        
        steps = 50
        for i in range(steps):
            path = QPainterPath()
            
            # Directional expansion (out of radius downwards/outwards)
            sx = cx - 300 - i * 1.5
            ex = cx + 300 + i * 1.5
            sy = cy + 20 + i * 0.2
            ey = cy + 20 + i * 0.2
            
            # Control point drops faster to bulge outwards
            cy_ctrl = cy + 180 + i * 3.5
            
            path.moveTo(sx, sy)
            path.quadTo(cx, cy_ctrl, ex, ey)
            
            # Fade calculation
            factor = (steps - i) / steps
            alpha = factor ** 2.0  # exponential drop-off
            
            opacity = 0.08 * alpha * self.pulse_alpha
            
            # The core line itself should be extremely subtle
            if i == 0:
                opacity = 0.25 * self.pulse_alpha
                p.setPen(QPen(QBrush(grad), 1.5, Qt.SolidLine, Qt.RoundCap))
            else:
                p.setPen(QPen(QBrush(grad), 2, Qt.SolidLine, Qt.RoundCap))
                
            p.setOpacity(opacity)
            p.drawPath(path)
            
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw "Assertions" purely on top of the glow background
        font = QFont("Segoe UI", 20, QFont.Light)
        p.setFont(font)
        p.setPen(QColor("#f8fafc"))
        
        curve_bottom_y = cy + 100
        text_rect = QRectF(0, curve_bottom_y + 15, w, 50)
        p.drawText(text_rect, Qt.AlignCenter, self.task_name)
