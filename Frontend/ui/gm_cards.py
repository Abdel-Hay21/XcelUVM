from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont, QRadialGradient, QBrush
import math

from core.config import get_image_path


class DiagramBox(QFrame):
    def __init__(self, text, icon_char, color_theme, is_glowing=False, width=130, height=90,
                 icon_size=24, text_size=13, glow_radius=40, glow_alpha=255, parent=None, icon_path=None):
        super().__init__(parent)
        self.text = text
        self.icon_path = icon_path
        self.color_theme = color_theme
        self.is_glowing = is_glowing
        self.box_width = width
        self.box_height = height
        self.base_icon_size = icon_size
        self.base_text_size = text_size
        self.glow_radius = glow_radius
        self.glow_alpha = glow_alpha
        self.current_scale = 1.0
        self._setup_ui(icon_char)

    def _setup_ui(self, icon_char):
        self.setFixedSize(self.box_width, self.box_height)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(5)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        if self.icon_path:
            from PyQt5.QtGui import QPixmap
            pix = QPixmap(self.icon_path)
            self.icon_lbl.setPixmap(pix.scaledToHeight(int(self.base_icon_size), Qt.SmoothTransformation))
        else:
            self.icon_lbl.setText(icon_char or "")
            if not icon_char:
                self.icon_lbl.hide()

        self.text_lbl = QLabel(self.text)
        self.text_lbl.setAlignment(Qt.AlignCenter)
        self.text_lbl.setWordWrap(True)

        lay.addWidget(self.icon_lbl)
        lay.addWidget(self.text_lbl)

        self.update_theme(self.color_theme)

    def set_scale(self, scale):
        self.current_scale = scale
        self.setFixedSize(int(self.box_width * scale), int(self.box_height * scale))
        self.update_theme(self.color_theme)

    def update_theme(self, color_theme, icon_size=23, text_size=20):
        self.color_theme = color_theme
        icon_sz = icon_size
        text_sz = text_size
        self.icon_lbl.setStyleSheet(f"font-size: {icon_sz}px; color: {self.color_theme['text']}; background: transparent; border: none;")
        self.text_lbl.setStyleSheet(f"font-size: {text_sz}px; font-weight: bold; color: {self.color_theme['text']}; background: transparent; font-family: 'Segoe UI'; border: none;")
        self.update_style()

    def set_glow_radius(self, radius):
        """غيّر درجة (نصاصة) الإشعاع في أي وقت."""
        self.glow_radius = radius
        self.update_style()

    def set_glow_alpha(self, alpha):
        """غيّر شفافية/قوة لون الإشعاع (0-255) في أي وقت."""
        self.glow_alpha = alpha
        self.update_style()

    def set_glow(self, is_glowing=None, radius=None, alpha=None):
        """دالة شاملة تتحكم في كل خصائص الـ glow مرة واحدة."""
        if is_glowing is not None:
            self.is_glowing = is_glowing
        if radius is not None:
            self.glow_radius = radius
        if alpha is not None:
            self.glow_alpha = alpha
        self.update_style()

    def update_style(self):
        bg = self.color_theme['bg']
        border = self.color_theme['border']
        self.setStyleSheet(f"""
            DiagramBox {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 16px;
            }}
        """)
        if self.is_glowing:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(self.glow_radius)
            effect.setOffset(0, 0)
            glow_color = QColor(self.color_theme['glow'])
            glow_color.setAlpha(self.glow_alpha)
            effect.setColor(glow_color)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

class DiagramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
        self.is_selected = False
        
    def set_selected(self, selected):
        self.is_selected = selected
        self.update_boxes()
        self.update()
        
    def update_boxes(self):
        pass
        
    def draw_dashed_line(self, p, p1, p2, color, arrow_at_p2=True, bidirectional=False):
        pen = QPen(QColor(color), 2, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(p1, p2)
        
        def draw_arrow(pt, angle):
            arrow_size = 8
            p.setBrush(QColor(color))
            p.setPen(Qt.NoPen)
            path = QPainterPath()
            path.moveTo(pt)
            path.lineTo(pt.x() - arrow_size * math.cos(angle - math.pi/6),
                        pt.y() - arrow_size * math.sin(angle - math.pi/6))
            path.lineTo(pt.x() - arrow_size * math.cos(angle + math.pi/6),
                        pt.y() - arrow_size * math.sin(angle + math.pi/6))
            path.closeSubpath()
            p.drawPath(path)
            
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        if arrow_at_p2:
            draw_arrow(p2, angle)
        if bidirectional:
            draw_arrow(p1, angle + math.pi)
        p.setBrush(Qt.NoBrush)

class RTLDiagram(DiagramWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.c_uvm_sel = {'bg': '#dcfce7', 'border': '#86efac', 'text': '#166534', 'glow': '#4ade80'}
        self.c_uvm_unsel = {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#581c87', 'glow': '#a855f7'}
        self.c_dut = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}
        self.c_gm_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': None}
        self.c_gm_unsel = {'bg': '#3b0764', 'border': '#9333ea', 'text': '#d8b4fe', 'glow': None}
        
        self.uvm_box = DiagramBox("UVM", "🛡️", self.c_uvm_unsel, is_glowing=True, width=200, height=150, parent=self)
        self.dut_box = DiagramBox("DUT", "⚙️", self.c_dut, width=140, height=80, parent=self)
        self.gm_box = DiagramBox("Reference Model\n(RTL)", None, self.c_gm_unsel, width=140, height=80, parent=self, icon_path=get_image_path("Reference_Model_RTL.png"), icon_size=25)
        
    def update_boxes(self):
        if self.is_selected:
            self.uvm_box.update_theme(self.c_uvm_sel, 55 ,25)
            self.gm_box.update_theme(self.c_gm_sel, 25, 12)
        else:
            self.uvm_box.update_theme(self.c_uvm_unsel, 55, 25)
            self.gm_box.update_theme(self.c_gm_unsel, 25, 12)
            
    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.uvm_box.move((w - self.uvm_box.width()) // 2, (h - 50 - self.uvm_box.height()) // 2 - 80)
        self.dut_box.move((w // 2) - self.dut_box.width() - 40, (h // 2) + 60)
        self.gm_box.move((w // 2) + 40, (h // 2) + 60)
        
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        line_color = "#22c55e" if self.is_selected else "#a855f7"
        
        uvm_rect = self.uvm_box.geometry()
        dut_rect = self.dut_box.geometry()
        gm_rect = self.gm_box.geometry()



        
        p1 = QPointF(dut_rect.center().x(), dut_rect.top())
        p2 = QPointF(uvm_rect.center().x() - 40, uvm_rect.bottom())
        pen = QPen(QColor(line_color), 2, Qt.DashLine)
        p.setPen(pen)
        path1 = QPainterPath()
        path1.moveTo(p1)
        path1.lineTo(p1.x(), p1.y() - 20)
        path1.lineTo(p2.x(), p1.y() - 20)
        path1.lineTo(p2)
        p.drawPath(path1)
        self.draw_dashed_line(p, QPointF(p2.x(), p1.y()-20), p2, line_color)
        
        p1 = QPointF(gm_rect.center().x(), gm_rect.top())
        p2 = QPointF(uvm_rect.center().x() + 40, uvm_rect.bottom())
        pen = QPen(QColor(line_color), 2, Qt.DashLine)
        p.setPen(pen)
        path2 = QPainterPath()
        path2.moveTo(p1)
        path2.lineTo(p1.x(), p1.y() - 20)
        path2.lineTo(p2.x(), p1.y() - 20)
        path2.lineTo(p2)
        p.drawPath(path2)
        self.draw_dashed_line(p, QPointF(p2.x(), p1.y()-20), p2, line_color)
        p.end()

class SBDiagram(DiagramWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.c_uvm_sel = {'bg': '#dcfce7', 'border': '#86efac', 'text': '#166534', 'glow': '#4ade80'}
        self.c_uvm_unsel = {'bg': '#f3e8ff', 'border': '#d8b4fe', 'text': '#581c87', 'glow': '#a855f7'}
        self.c_dut = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}
        self.c_sb_sel = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}
        self.c_sb_unsel = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}
        self.c_gm_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': None}
        self.c_gm_unsel = {'bg': '#3b0764', 'border': '#9333ea', 'text': '#d8b4fe', 'glow': None}
        
        self.uvm_box = DiagramBox("UVM", "🛡️", self.c_uvm_unsel, is_glowing=True, width=200, height=140, parent=self)
        self.dut_box = DiagramBox("DUT", "⚙️", self.c_dut, width=140, height=80, parent=self)
        self.sb_box = DiagramBox("Scoreboard", None, self.c_sb_unsel, width=140, height=82, parent=self, icon_path=get_image_path("Scoreboard.png"), icon_size=35)
        self.gm_box = DiagramBox("Reference Model\n(SW)", "❃", self.c_gm_unsel, width=140, height=82, parent=self)
        
    def update_boxes(self):
        if self.is_selected:
            self.uvm_box.update_theme(self.c_uvm_sel, 55, 25)
            self.sb_box.update_theme(self.c_sb_sel, 25, 17)
            self.gm_box.update_theme(self.c_gm_sel, 25, 12)
        else:
            self.uvm_box.update_theme(self.c_uvm_unsel, 55, 25)
            self.sb_box.update_theme(self.c_sb_unsel,25, 17)
            self.gm_box.update_theme(self.c_gm_unsel, 25, 12)
            
    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.uvm_box.move((w - self.uvm_box.width()) // 2, (h - self.uvm_box.height()) // 2 - 30)
        self.dut_box.move((w - self.dut_box.width()) // 2, (h // 2) + 70)
        self.sb_box.move((w // 2) - self.sb_box.width() - 40, (h // 2) - 200)
        self.gm_box.move((w // 2) + 40, (h // 2) - 200)
        
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        line_color = "#22c55e" if self.is_selected else "#a855f7"
        
        uvm_rect = self.uvm_box.geometry()
        dut_rect = self.dut_box.geometry()
        sb_rect = self.sb_box.geometry()
        gm_rect = self.gm_box.geometry()
        
        self.draw_dashed_line(p, QPointF(dut_rect.center().x(), dut_rect.top()), 
                              QPointF(uvm_rect.center().x(), uvm_rect.bottom()), line_color, bidirectional=True)
                              
        self.draw_dashed_line(p, QPointF(sb_rect.right(), sb_rect.center().y()), 
                              QPointF(gm_rect.left(), gm_rect.center().y()), line_color, bidirectional=True)
                              
        p1 = QPointF(uvm_rect.center().x() - 40, uvm_rect.top())
        p2 = QPointF(sb_rect.center().x(), sb_rect.bottom())
        pen = QPen(QColor(line_color), 2, Qt.DashLine)
        p.setPen(pen)
        path1 = QPainterPath()
        path1.moveTo(p1)
        path1.lineTo(p1.x(), p1.y() - 8)
        path1.lineTo(p2.x(), p1.y() - 8)
        path1.lineTo(p2)
        p.drawPath(path1)
        self.draw_dashed_line(p, QPointF(p2.x(), p1.y()-8), p2, line_color)

                
        p1 = QPointF(uvm_rect.center().x() + 40, uvm_rect.top())
        p2 = QPointF(gm_rect.center().x(), gm_rect.bottom())
        pen = QPen(QColor(line_color), 2, Qt.DashLine)
        p.setPen(pen)
        path1 = QPainterPath()
        path1.moveTo(p1)
        path1.lineTo(p1.x(), p1.y() - 8)
        path1.lineTo(p2.x(), p1.y() - 8)
        path1.lineTo(p2)
        p.drawPath(path1)
        self.draw_dashed_line(p, QPointF(p2.x(), p1.y()-8), p2, line_color)
        p.end()

class GMCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, subtitle, icon, diagram_cls, parent=None, icon_path=None):
        super().__init__(parent)
        self.is_selected = False
        self.diagram = diagram_cls()
        self.setCursor(Qt.PointingHandCursor)
        
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(20, 20, 20, 20)
        self.lay.setSpacing(15)
        
        head_lay = QHBoxLayout()
        icon_lbl = QLabel()
        if icon_path:
            from PyQt5.QtGui import QPixmap
            pix = QPixmap(icon_path)
            icon_lbl.setPixmap(pix.scaledToHeight(45, Qt.SmoothTransformation))
        else:
            icon_lbl.setText(icon or "")
            icon_lbl.setStyleSheet("font-size: 45px; background: transparent;")
        
        text_lay = QVBoxLayout()
        text_lay.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #e2e8f0; background: transparent; font-family: 'Segoe UI';")
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent; font-family: 'Segoe UI';")
        text_lay.addWidget(self.title_lbl)
        text_lay.addWidget(self.sub_lbl)
        
        self.check_lbl = QLabel("✔️")
        self.check_lbl.setAlignment(Qt.AlignCenter)
        self.check_lbl.setFixedSize(28, 28)
        
        head_lay.addWidget(icon_lbl)
        head_lay.addSpacing(10)
        head_lay.addLayout(text_lay)
        head_lay.addStretch()
        head_lay.addWidget(self.check_lbl)
        
        self.lay.addLayout(head_lay)
        
        diag_container = QFrame()
        diag_container.setStyleSheet("background-color: #1c2030; border-radius: 12px; border: 1px solid #1a1d27;")
        diag_lay = QVBoxLayout(diag_container)
        diag_lay.setContentsMargins(10, 10, 10, 10)
        diag_lay.addWidget(self.diagram)
        
        self.lay.addWidget(diag_container, stretch=1)
        self.update_style()
        
    def set_selected(self, selected):
        self.is_selected = selected
        self.diagram.set_selected(selected)
        self.update_style()
        
    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                GMCard {
                    background-color: #13161f;
                    border: 2px solid #22c55e;
                    border-radius: 16px;
                }
            """)
            self.check_lbl.setStyleSheet("background-color: #22c55e; color: white; border-radius: 14px; font-size: 14px;")
            self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #22c55e; background: transparent; font-family: 'Segoe UI';")
        else:
            self.setStyleSheet("""
                GMCard {
                    background-color: #13161f;
                    border: 1px solid #3b0764;
                    border-radius: 16px;
                }
                GMCard:hover {
                    border: 1px solid #8b5cf6;
                    background-color: #1a1d27;
                }
            """)
            self.check_lbl.setStyleSheet("background-color: transparent; color: transparent;")
            self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #a855f7; background: transparent; font-family: 'Segoe UI';")
            
    def mousePressEvent(self, event):
        self.clicked.emit()

class GMCardsContainer(QWidget):
    selection_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)
        
        self.rtl_card = GMCard(
            "Hardware Reference", 
            "Use a RTL file as reference model", 
            None, RTLDiagram, icon_path=get_image_path("Hardware.png")
        )
        self.sb_card = GMCard(
            "Software Reference", 
            "Use an algorithmic as reference model", 
            None, SBDiagram, icon_path=get_image_path("Software.png")
        )
        
        lay.addWidget(self.rtl_card)
        lay.addWidget(self.sb_card)
        
        self.rtl_card.clicked.connect(lambda: self.select("GM_RTL"))
        self.sb_card.clicked.connect(lambda: self.select("GM_SB"))

        self.select("None")

    def select(self, gm_type):
        self.rtl_card.set_selected(gm_type == "GM_RTL")
        self.sb_card.set_selected(gm_type == "GM_SB")
        self.selection_changed.emit(gm_type)
