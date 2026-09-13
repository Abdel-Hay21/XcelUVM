from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath
import math

# ── reuse DiagramBox and DiagramWidget from gm_cards ──────────────────────────
from ui.gm_cards import DiagramBox, DiagramWidget
from core.config import get_image_path



# ═══════════════════════════════════════════════════════════════════════════════
#  Single Agent Diagram
# ═══════════════════════════════════════════════════════════════════════════════
class SingleAgentDiagram(DiagramWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.c_agent_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': '#4ade80'}
        self.c_agent_unsel = {'bg': '#1e1b4b', 'border': '#6366f1', 'text': '#a5b4fc', 'glow': '#818cf8'}
        self.c_dut = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}
        self.c_interface_sel = {'bg': '#064e3b', 'border': '#10b981', 'text': '#6ee7b7', 'glow': None}
        self.c_interface_unsel = {'bg': '#312e81', 'border': '#6366f1', 'text': '#c7d2fe', 'glow': None}

        self.agent_box = DiagramBox("Agent", None, self.c_agent_unsel, is_glowing=True,
                                    width=180, height=130, parent=self, icon_path=get_image_path("agent.png"))
        self.interface_box = DiagramBox("⛓️‍💥 Interface", "", self.c_interface_unsel, width=180, height=50, parent=self)
        self.dut_box = DiagramBox("DUT", "⚙️", self.c_dut, width=100, height=80, parent=self)

    def update_boxes(self):
        if self.is_selected:
            self.agent_box.update_theme(self.c_agent_sel)
            self.interface_box.update_theme(self.c_interface_sel)
        else:
            self.agent_box.update_theme(self.c_agent_unsel)
            self.interface_box.update_theme(self.c_interface_unsel)


    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.agent_box.move((w - self.agent_box.width()) // 2,
                            (h - self.agent_box.height()) // 2 - 120)
        self.interface_box.move((w - self.interface_box.width()) // 2, h // 2 - 10)
        self.dut_box.move((w - self.dut_box.width()) // 2, h // 2 + 65)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lc = "#22c55e" if self.is_selected else "#818cf8"

        agent_r = self.agent_box.geometry()
        interface_r = self.interface_box.geometry()
        dut_r = self.dut_box.geometry()
   
        # Agent → Interface
        self.draw_dashed_line(p,
            QPointF(agent_r.center().x(), agent_r.bottom()),
            QPointF(interface_r.center().x(), interface_r.top()), lc, bidirectional=True)

        # Interface → DUT
        self.draw_dashed_line(p,
            QPointF(interface_r.center().x(), interface_r.bottom()),
            QPointF(dut_r.center().x(), dut_r.top()), lc, bidirectional=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Multi Agent Diagram
# ═══════════════════════════════════════════════════════════════════════════════
class MultiAgentDiagram(DiagramWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.c_a1_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': '#4ade80'}
        self.c_a1_unsel = {'bg': '#1e1b4b', 'border': '#6366f1', 'text': '#a5b4fc', 'glow': '#818cf8'}
        self.c_a2_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': '#4ade80'}
        self.c_a2_unsel = {'bg': '#1e1b4b', 'border': '#6366f1', 'text': '#a5b4fc', 'glow': '#818cf8'}
        self.c_an_sel = {'bg': '#14532d', 'border': '#22c55e', 'text': '#4ade80', 'glow': '#4ade80'}
        self.c_an_unsel = {'bg': '#1e1b4b', 'border': '#6366f1', 'text': '#a5b4fc', 'glow': '#818cf8'}
        self.c_interface_1_sel = {'bg': '#064e3b', 'border': '#10b981', 'text': '#6ee7b7', 'glow': None}
        self.c_interface_1_unsel = {'bg': '#312e81', 'border': '#6366f1', 'text': '#c7d2fe', 'glow': None}
        self.c_interface_2_sel = {'bg': '#064e3b', 'border': '#10b981', 'text': '#6ee7b7', 'glow': None}
        self.c_interface_2_unsel = {'bg': '#312e81', 'border': '#6366f1', 'text': '#c7d2fe', 'glow': None}
        self.c_interface_n_sel = {'bg': '#064e3b', 'border': '#10b981', 'text': '#6ee7b7', 'glow': None}
        self.c_interface_n_unsel = {'bg': '#312e81', 'border': '#6366f1', 'text': '#c7d2fe', 'glow': None}
        self.c_dut = {'bg': '#1e2132', 'border': '#2a2d3e', 'text': '#94a3b8', 'glow': None}

        self.a1_box = DiagramBox("Agent 1", None, self.c_a1_unsel, is_glowing=True, glow_radius=20,
                                 width=100, height=130, parent=self, icon_path=get_image_path("agent.png"))
        self.a2_box = DiagramBox("Agent 2", None, self.c_a2_unsel, is_glowing=True, glow_radius=20,
                                 width=100, height=130, parent=self, icon_path=get_image_path("agent.png"))
        self.an_box = DiagramBox("Agent N", None, self.c_an_unsel, is_glowing=True, glow_radius=20,
                                 width=100, height=130, parent=self, icon_path=get_image_path("agent.png"))
        self.interface_1_box = DiagramBox("⛓️‍💥 Interface 1", "", self.c_interface_1_unsel, width=100, height=50, parent=self)
        self.interface_2_box = DiagramBox("⛓️‍💥 Interface 2", "", self.c_interface_2_unsel, width=100, height=50, parent=self)
        self.interface_n_box = DiagramBox("⛓️‍💥 Interface N", "", self.c_interface_n_unsel, width=100, height=50, parent=self)
        self.dut_box = DiagramBox("DUT", "⚙️", self.c_dut, width=320, height=80, parent=self)

    def update_boxes(self):
        agent_size = 17
        interface_size = 10
        if self.is_selected:
            self.a1_box.update_theme(self.c_a1_sel,agent_size,agent_size)
            self.a2_box.update_theme(self.c_a2_sel,agent_size,agent_size)
            self.an_box.update_theme(self.c_an_sel,agent_size,agent_size)
            self.interface_1_box.update_theme(self.c_interface_1_sel,interface_size,interface_size)
            self.interface_2_box.update_theme(self.c_interface_2_sel,interface_size,interface_size)
            self.interface_n_box.update_theme(self.c_interface_n_sel,interface_size,interface_size)
        else:
            self.a1_box.update_theme(self.c_a1_unsel,agent_size,agent_size)
            self.a2_box.update_theme(self.c_a2_unsel,agent_size,agent_size)
            self.an_box.update_theme(self.c_an_unsel,agent_size,agent_size)
            self.interface_1_box.update_theme(self.c_interface_1_unsel,interface_size,interface_size)
            self.interface_2_box.update_theme(self.c_interface_2_unsel,interface_size,interface_size)
            self.interface_n_box.update_theme(self.c_interface_n_unsel,interface_size,interface_size)

    def resizeEvent(self, e):
        Seperation = 10
        w, h = self.width(), self.height()
        top_y = h // 2 - 180
        self.a1_box.move(w // 2 - self.a1_box.width() - self.a2_box.width() // 2 - Seperation, top_y)
        self.a2_box.move((w - self.a2_box.width()) // 2, top_y)
        self.an_box.move(w // 2 + self.a2_box.width() // 2 + Seperation, top_y)
        self.interface_1_box.move((w // 2 - self.interface_1_box.width() - self.interface_2_box.width() // 2 - Seperation), h // 2 - 10)
        self.interface_2_box.move((w - self.interface_2_box.width()) // 2, h // 2 - 10)
        self.interface_n_box.move((w // 2 + self.interface_2_box.width() // 2 + Seperation), h // 2 - 10)
        self.dut_box.move((w - self.dut_box.width()) // 2, h // 2 + 65)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lc = "#22c55e" if self.is_selected else "#818cf8"

        dut_r = self.dut_box.geometry()
        r = self.a1_box.geometry()
        z = self.interface_1_box.geometry()
        self.draw_dashed_line(p,
            QPointF(r.center().x(), r.bottom()),
            QPointF(r.center().x(), z.top()), lc, bidirectional=True)

        r = self.a2_box.geometry()
        z = self.interface_2_box.geometry()
        self.draw_dashed_line(p,
            QPointF(r.center().x(), r.bottom()),
            QPointF(r.center().x(), z.top()), lc, bidirectional=True)

        r = self.an_box.geometry()
        z = self.interface_n_box.geometry()
        self.draw_dashed_line(p,
            QPointF(r.center().x(), r.bottom()),
            QPointF(r.center().x(), z.top()), lc, bidirectional=True)

        r = self.interface_1_box.geometry() 
        self.draw_dashed_line(p,
                QPointF(r.center().x(), r.bottom()),
                QPointF(r.center().x(), dut_r.top()), lc, bidirectional=True)       

        r = self.interface_2_box.geometry() 
        self.draw_dashed_line(p,
                QPointF(r.center().x(), r.bottom()),
                QPointF(r.center().x(), dut_r.top()), lc, bidirectional=True)     

        r = self.interface_n_box.geometry() 
        self.draw_dashed_line(p,
                QPointF(r.center().x(), r.bottom()),
                QPointF(r.center().x(), dut_r.top()), lc, bidirectional=True)     


        
        # Draw "..." dots between Agent 2 and Agent N
        a2_r = self.a2_box.geometry()
        an_r = self.an_box.geometry()
        mid_x = (a2_r.right() + an_r.left()) / 2
        mid_y = a2_r.center().y()
        pen = QPen(QColor(lc), 2)
        p.setPen(pen)
        p.setBrush(QColor(lc))
        for dx in [-3, 0, 3]:
            p.drawEllipse(QPointF(mid_x + dx, mid_y), 1, 1)
        p.setBrush(Qt.NoBrush)


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Card  (mirrors GMCard)
# ═══════════════════════════════════════════════════════════════════════════════
class AgentCard(QFrame):
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
        self.title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #e2e8f0;"
            " background: transparent; font-family: 'Segoe UI';")
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(
            "font-size: 12px; color: #94a3b8;"
            " background: transparent; font-family: 'Segoe UI';")
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
        diag_container.setStyleSheet(
            "background-color: #1c2030; border-radius: 12px; border: 1px solid #1a1d27;")
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
                AgentCard {
                    background-color: #13161f;
                    border: 2px solid #22c55e;
                    border-radius: 16px;
                }
            """)
            self.check_lbl.setStyleSheet(
                "background-color: #22c55e; color: white;"
                " border-radius: 14px; font-size: 14px;")
            self.title_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #22c55e;"
                " background: transparent; font-family: 'Segoe UI';")
        else:
            self.setStyleSheet("""
                AgentCard {
                    background-color: #13161f;
                    border: 1px solid #3b0764;
                    border-radius: 16px;
                }
                AgentCard:hover {
                    border: 1px solid #8b5cf6;
                    background-color: #1a1d27;
                }
            """)
            self.check_lbl.setStyleSheet(
                "background-color: transparent; color: transparent;")
            self.title_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #a855f7;"
                " background: transparent; font-family: 'Segoe UI';")

    def mousePressEvent(self, event):
        self.clicked.emit()


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Cards Container  (mirrors GMCardsContainer)
# ═══════════════════════════════════════════════════════════════════════════════
class AgentCardsContainer(QWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        self.single_card = AgentCard(
            "Single Agent",
            "One agent driving and monitoring the DUT",
            None, SingleAgentDiagram, icon_path=get_image_path("single_agent.png")
        )
        self.multi_card = AgentCard(
            "Multi-Agent",
            "Multi-agent for complex verification",
            None, MultiAgentDiagram, icon_path=get_image_path("multi_agent.png")
        )

        lay.addWidget(self.single_card)
        lay.addWidget(self.multi_card)

        self.single_card.clicked.connect(lambda: self.select("SINGLE"))
        self.multi_card.clicked.connect(lambda: self.select("MULTI"))

        self.select("None")

    def select(self, mode):
        self.single_card.set_selected(mode == "SINGLE")
        self.multi_card.set_selected(mode == "MULTI")
        self.selection_changed.emit(mode)
