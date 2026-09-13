import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QFileDialog, QStackedWidget,
    QSpinBox, QScrollArea, QListWidget
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QVariantAnimation
from PyQt5.QtGui import QColor, QTextCursor, QIcon
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from core.parser import parse_run_tcl
from core.runner import TclRunner
from core.config import get_run_tcl, LOGO_PATH, get_image_path, BACKEND_SELF_DIR, BACKEND_AI_DIR
from core.theme import apply_dark_titlebar

from ui.widgets import GradientLabel, ToggleSwitch, SlidingWidget, StepBar, WelcomePage
from ui.sections import PortSection, SeqSection

class MainWindow(QMainWindow):
    # Flag to easily show or hide the log section on the Generate page
    SHOW_LOG_UI = False

    def __init__(self):
        super().__init__()
        self.setWindowTitle("XcelUVM")
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setMinimumSize(860, 730)
        self.resize(970, 860)
        self._runner = None
        self.sb_language = None   # default language when Software Reference is chosen
        self.golden_model_type = None
        self.agent_mode = None
        self.num_active_agents = 0
        self.num_passive_agents = 0
        self._lang_anims = []     # keep animation refs alive
        self._agent_anims = []
        self._apply_stylesheet()
        apply_dark_titlebar(self)


        self._outer = QStackedWidget()
        self.setCentralWidget(self._outer)

        # Page 0 — Welcome
        welcome = WelcomePage()
        welcome.start_clicked.connect(self._do_warp_transition)
        self._outer.addWidget(welcome)

        # Page 1 — Wizard (Project → Ports → Sequences)
        # parse_run_tcl() with no args auto-picks the most recently modified
        # run.tcl — i.e. whichever was last used.
        tcl = parse_run_tcl()
        # ui_state maps directly to the TCL data — no separate JSON needed
        self.ui_state = tcl
            
        self._outer.addWidget(self._build_wizard(tcl))
        self._outer.setCurrentIndex(0)
        
        # Globally dismiss status bar errors on any user interaction
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() in (QEvent.KeyPress, QEvent.MouseButtonPress):
            msg = self.statusBar().currentMessage()
            if msg and msg.startswith("⚠"):
                self.statusBar().clearMessage()
        return super().eventFilter(obj, event)

    # ── Wizard builder ─────────────────────────────────────────────────────────
    def _do_warp_transition(self):
        from ui.widgets import HeroTransitionOverlay
        from PyQt5.QtCore import QVariantAnimation, QEasingCurve, QTimer, QPoint, QRect
        from PyQt5.QtWidgets import QApplication
        
        w_old = self._outer.widget(0)
        
        # Hide old logo before grabbing full page
        w_old.icon_lbl.hide()
        pix_old = w_old.grab()
        w_old.icon_lbl.show()
        
        # Compute start rect (before switching pages)
        p1 = w_old.icon_lbl.mapTo(self, QPoint(0,0))
        rect1 = QRect(p1, w_old.icon_lbl.size())
        
        # Create the overlay immediately with pix_old (prevents any flash)
        self._warp_overlay = HeroTransitionOverlay(self, pix_old, pix_old, rect1, rect1)
        self._warp_overlay.setGeometry(self.rect())
        self._warp_overlay.show()
        self._warp_overlay.raise_()
        QApplication.processEvents()
        
        # Now switch pages hidden behind the overlay
        self._outer.setCurrentIndex(1)
        QApplication.processEvents()
        
        # Hide the real logo_lbl invisibly (preserves layout space) and grab the new page
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        temp_effect = QGraphicsOpacityEffect()
        temp_effect.setOpacity(0.0)
        self._step_bar.logo_lbl.setGraphicsEffect(temp_effect)
        pix_new = self._outer.widget(1).grab()
        
        # Compute end rect
        p2 = self._step_bar.logo_lbl.mapTo(self, QPoint(0,0))
        rect2 = QRect(p2, self._step_bar.logo_lbl.size())
        self._warp_overlay.pix2 = pix_new
        self._warp_overlay.rect2 = rect2

        self._warp_anim = QVariantAnimation(self)
        self._warp_anim.setDuration(1000)
        self._warp_anim.setStartValue(0.0)
        self._warp_anim.setEndValue(1.0)
        self._warp_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        def on_val(v):
            self._warp_overlay.set_progress(v)
            
        def on_done():
            self._warp_overlay.hide()
            self._warp_overlay.deleteLater()
            del self._warp_overlay
            # Show the real logo now by removing the transparency effect
            self._step_bar.logo_lbl.setGraphicsEffect(None)
            
        self._warp_anim.valueChanged.connect(on_val)
        self._warp_anim.finished.connect(on_done)
        self._warp_anim.start()

    def _build_wizard(self, tcl):
        root = QWidget(); root.setObjectName("root")
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # Step bar
        self._step_bar = StepBar()
        self._step_bar.setStyleSheet("background:#0f1117; border-bottom:1px solid #1e2132;")
        vlay.addWidget(self._step_bar)

        # Sliding content area
        self._slider = SlidingWidget()
        vlay.addWidget(self._slider, stretch=1)

        # ── Page 0: Project ───────────────────────────────────────────────────
        p0 = self._make_card()
        c0 = p0.property("cl")
        hdr_1, _ = self._step_header("STEP 1", "Project Configuration")
        c0.addWidget(hdr_1)
        c0.addWidget(self._lbl("Set the project name and output directory", "subtitle"))
        c0.addWidget(self._divider())
        c0.addSpacing(16)

        inner_card = QFrame()
        inner_card.setObjectName("premium_card")
        ic_lay = QVBoxLayout(inner_card)
        ic_lay.setContentsMargins(36, 36, 36, 36)
        ic_lay.setSpacing(32)

        pn_lay = QVBoxLayout(); pn_lay.setSpacing(10)
        lbl_pn = self._lbl("✨ PROJECT NAME", "premium_label")
        pn_lay.addWidget(lbl_pn)
        self.project_input = QLineEdit(self.ui_state.get("project_name", tcl["project_name"]))
        self.project_input.setObjectName("premium_input")
        self.project_input.setPlaceholderText("e.g.  AXI_Master")
        pn_lay.addWidget(self.project_input)
        ic_lay.addLayout(pn_lay)

        dir_lay = QVBoxLayout(); dir_lay.setSpacing(10)
        lbl_dir = self._lbl("📁 OUTPUT DIRECTORY", "premium_label")
        dir_lay.addWidget(lbl_dir)
        rw = QHBoxLayout(); rw.setSpacing(12)
        self.path_input = QLineEdit(self.ui_state.get("path", tcl["path"] or ""))
        self.path_input.setObjectName("premium_input")
        self.path_input.setPlaceholderText("Select where the UVM files will be generated...")
        rw.addWidget(self.path_input, stretch=1)
        
        bb = QPushButton("Browse")
        bb.setObjectName("premium_browse")
        bb.setCursor(Qt.PointingHandCursor)
        bb.clicked.connect(self._on_browse); rw.addWidget(bb)
        dir_lay.addLayout(rw)
        ic_lay.addLayout(dir_lay)

        c0.addWidget(inner_card)
        c0.addStretch()
        self._slider.addPage(p0)

        # ── Page 1: Reference Model Type ─────────────────────────────────────────
        pgm = self._make_card()
        cgm = pgm.property("cl")
        hdr_2, _ = self._step_header("STEP 2", "Reference Model Type")
        cgm.addWidget(hdr_2)
        cgm.addWidget(self._lbl("Select the type of Reference Model that best fits your verification environment.", "subtitle"))
        cgm.addWidget(self._divider())

        cgm.addSpacing(16)

        from ui.gm_cards import GMCardsContainer
        self.gm_cards = GMCardsContainer(self)
        self.gm_lay = QHBoxLayout()
        self.gm_lay.addWidget(self.gm_cards)
        cgm.addLayout(self.gm_lay)
        cgm.addSpacing(12)
        
        self.golden_model_type = None

        # ── Language tree (only visible when Software Reference is selected) ─
        self.lang_tree = QWidget()
        self.lang_tree.setObjectName("lang_tree")
        tree_layout = QVBoxLayout(self.lang_tree)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)

        # Top box: Golden Model
        gm_box = QLabel("REFERENCE MODEL")
        gm_box.setAlignment(Qt.AlignCenter)
        gm_box.setFixedSize(220, 48)
        gm_box.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                border: 2px solid #d4af37;
                color: #fce78b;
                font-weight: bold;
                border-radius: 24px;
                font-size: 16px;
                font-family: 'Georgia', serif;
            }
        """)
        box_lay = QHBoxLayout(); box_lay.addStretch(); box_lay.addWidget(gm_box); box_lay.addStretch()
        
        # Trunk
        line_color = "#334155"
        trunk = QFrame(); trunk.setFixedSize(2, 24); trunk.setStyleSheet(f"background:{line_color}; border:none;")
        tr_lay = QHBoxLayout(); tr_lay.addStretch(); tr_lay.addWidget(trunk); tr_lay.addStretch()
        
        # Horizontal bar
        hbar = QFrame(); hbar.setFixedHeight(2); hbar.setStyleSheet(f"background:{line_color}; border:none;")
        hbar_lay = QHBoxLayout(); hbar_lay.setContentsMargins(110, 0, 110, 0); hbar_lay.addWidget(hbar)

        # three leaf buttons
        lang_row = QHBoxLayout(); lang_row.setSpacing(16)
        lang_data = [
            ("SV",  " SystemVerilog", "#07304f", "#13161f", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #989fa6,stop:1 #1b3d61)", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #989fa6,stop:1 #295e94)", get_image_path("SV_Logo.png")),
            ("C",   " C / C++",       "#07304f", "#13161f", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #426385,stop:1 #0f2140)", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4f759c,stop:1 #173363)", get_image_path("C_Logo.png")),
            ("PY",  " Python",        "#07304f", "#13161f", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1e3349,stop:1 #423c26)", "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #285073,stop:1 #71612d)", get_image_path("python_logo.png")),
        ]
        self._lang_btns = {}
        from PyQt5.QtCore import QSize
        for code, label, accent, bg_normal, bg_hover, bg_checked, icon_path in lang_data:
            btn = QPushButton(label)
            if icon_path:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(33, 33)) if code == "SV" else btn.setIconSize(QSize(24, 24))
            btn.setCheckable(True)
            btn.setObjectName("lang_btn")
            btn.setFixedHeight(56)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton#lang_btn {{
                    background: {bg_normal};
                    color: #94a3b8;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: 'Segoe UI';
                    border: 2px solid #1e293b;
                    border-radius: 12px;
                    padding: 0 20px;
                }}
                QPushButton#lang_btn:hover {{
                    background: {bg_hover};
                    color: #e2e8f0;
                    border: 2px solid {accent}88;
                }}
                QPushButton#lang_btn:checked {{
                    background: {bg_checked};
                    border: 2px solid {accent};
                    color: #ffffff;
                    font-weight: 600;
                }}
            """)
            self._lang_btns[code] = btn
            
            # Stem above each button
            col = QVBoxLayout()
            col.setSpacing(0)
            col.setAlignment(Qt.AlignHCenter)
            stem = QFrame(); stem.setFixedSize(2, 24); stem.setStyleSheet(f"background:{line_color}; border:none;")
            col.addWidget(stem, 0, Qt.AlignHCenter)
            col.addWidget(btn)
            lang_row.addLayout(col)

        def _set_lang(code):
            self.sb_language = code
            for c, b in self._lang_btns.items():
                b.setChecked(c == code)

        for code, btn in self._lang_btns.items():
            btn.clicked.connect(lambda _, c=code: _set_lang(c))

        tree_layout.addSpacing(10)
        tree_layout.addLayout(box_lay)
        tree_layout.addLayout(tr_lay)
        tree_layout.addLayout(hbar_lay)
        tree_layout.addLayout(lang_row)

        # Remove opacity effect and use height animation instead
        self.lang_tree.setMaximumHeight(0)
        self.lang_tree.setVisible(False)

        cgm.addWidget(self.lang_tree)
        cgm.addStretch()
        self._slider.addPage(pgm)

        # ── wire gm_changed AFTER all widgets exist ──────────────────────────
        def gm_changed(gm_type):
            self.golden_model_type = gm_type.replace("GM_", "")
            if hasattr(self, 'assumption_note'):
                self.assumption_note.setVisible(self.golden_model_type == "RTL")
            if hasattr(self, 'golden_widget'):
                self.golden_widget.setVisible(self.golden_model_type == "RTL")
            if hasattr(self, 'rtl_source_title'):
                if self.golden_model_type == "RTL":
                    self.rtl_source_title.setText("DUT SOURCE FILES")
                    self.ref_source_zone.show()
                else:
                    self.rtl_source_title.setText("RTL SOURCE FILES")
                    self.ref_source_zone.hide()

        self.gm_cards.selection_changed.connect(gm_changed)

        # ── Page 2: Options ───────────────────────────────────────────────────
        po = self._make_card()
        co = po.property("cl")
        hdr_3, _ = self._step_header("STEP 3", "Options")
        co.addWidget(hdr_3)
        co.addWidget(self._lbl("Enable or disable optional UVM features", "subtitle"))
        co.addWidget(self._divider())

        opt_row = QHBoxLayout()
        label = self._lbl("Assertions", "field_label")
        label.setStyleSheet("font-size:12pt;")
        opt_row.addWidget(label)
        opt_row.addStretch()
        self.assert_toggle = ToggleSwitch(checked=tcl.get("assertions", True))
        opt_row.addWidget(self.assert_toggle)
        co.addLayout(opt_row)
        
        opt_row2 = QHBoxLayout()
        label2 = self._lbl("Code Coverage", "field_label")
        label2.setStyleSheet("font-size:12pt;")
        opt_row2.addWidget(label2)
        opt_row2.addStretch()
        self.C_cover_toggle = ToggleSwitch(checked=tcl.get("Code_Coverage", True))
        opt_row2.addWidget(self.C_cover_toggle)
        co.addLayout(opt_row2)

        opt_row3 = QHBoxLayout()
        label3 = self._lbl("Functional Coverage", "field_label")
        label3.setStyleSheet("font-size:12pt;")
        opt_row3.addWidget(label3)
        opt_row3.addStretch()
        self.cover_toggle = ToggleSwitch(checked=tcl.get("coverage", True))
        opt_row3.addWidget(self.cover_toggle)
        co.addLayout(opt_row3)


        co.addStretch()
        self._slider.addPage(po)

        # ── Page 3: Number of Agents ──────────────────────────────────────────
        p_agent = self._make_card()
        c_agent = p_agent.property("cl")
        hdr_4, _ = self._step_header("STEP 4", "Number Of Agents")
        c_agent.addWidget(hdr_4)
        c_agent.addWidget(self._lbl("Choose between a single-agent or multi-agent UVM environment", "subtitle"))
        c_agent.addWidget(self._divider())
        c_agent.addSpacing(16)

        from ui.agent_cards import AgentCardsContainer
        self.agent_cards = AgentCardsContainer(self)
        self.agent_lay = QHBoxLayout()
        self.agent_lay.addWidget(self.agent_cards)
        c_agent.addLayout(self.agent_lay)
        c_agent.addSpacing(12)

        # ── Agent config (hidden until Multi-Agent morph) ─────────────────────
        self.agent_config = QWidget()
        self.agent_config.setObjectName("agent_config")
        agent_cfg_lay = QHBoxLayout(self.agent_config)
        agent_cfg_lay.setContentsMargins(0, 10, 0, 0)
        agent_cfg_lay.setSpacing(30)

        # active agents
        active_col = QVBoxLayout()
        active_col.setSpacing(8)
        active_title = QLabel("Active Agents")
        active_title.setStyleSheet(
            "font-size:15px; font-weight:700; color:#22c55e;"
            " font-family:'Segoe UI'; background:transparent;")
        active_title.setAlignment(Qt.AlignCenter) 
        active_sub = QLabel("Number of Active (driver + monitor) agents")
        active_sub.setStyleSheet(
            "font-size:11px; color:#64748b; font-family:'Segoe UI'; background:transparent;")
        active_sub.setAlignment(Qt.AlignCenter)
        self.active_spin = QSpinBox()
        self.active_spin.setObjectName("bits_spin")
        self.active_spin.setRange(0, 50)
        self.active_spin.setValue(0)
        self.active_spin.setFixedHeight(44)       
        self.active_spin.setStyleSheet(
            "QSpinBox { background:#0d0f18; border:2px solid #22c55e55;"
            " border-radius:10px; color:#e2e8f0; font-size:18px;"
            " font-weight:700; font-family:'Segoe UI'; padding:4px 14px; }"
            "QSpinBox:focus { border:2px solid #22c55e; }"
            "QSpinBox::up-button {"
            " width:20px; background:#1e2132;"
            " border-top-right-radius:7px;"
            " border-bottom-right-radius:0px; }"
            
            "QSpinBox::down-button {"
            " width:20px; background:#1e2132;"
            " border-bottom-right-radius:7px;"
            " border-top-right-radius:0px; }"
            f"QSpinBox::up-arrow {{ image: url({get_image_path('triangle_up.png')}); width:10px; height:10px; }}"
            f"QSpinBox::down-arrow {{ image: url({get_image_path('triangle_down.png')}); width:10px; height:10px; }}")
        
        active_col.addWidget(active_title)
        active_col.addWidget(active_sub)
        active_col.addWidget(self.active_spin)
        active_col.addStretch()

        # passive agents
        passive_col = QVBoxLayout()
        passive_col.setSpacing(8)
        passive_title = QLabel("Passive Agents")
        passive_title.setStyleSheet(
            "font-size:15px; font-weight:700; color:#a78bfa;"
            " font-family:'Segoe UI'; background:transparent;")
        passive_title.setAlignment(Qt.AlignCenter) 
        passive_sub = QLabel("Number of Passive (monitor-only) agents")
        passive_sub.setStyleSheet(
            "font-size:11px; color:#64748b; font-family:'Segoe UI'; background:transparent;")
        passive_sub.setAlignment(Qt.AlignCenter)
        self.passive_spin = QSpinBox()
        self.passive_spin.setObjectName("bits_spin")
        self.passive_spin.setRange(0, 50)
        self.passive_spin.setValue(0)
        self.passive_spin.setFixedHeight(44)
        self.passive_spin.setStyleSheet(
            "QSpinBox { background:#0d0f18; border:2px solid #22c55e55;"
            " border-radius:10px; color:#e2e8f0; font-size:18px;"
            " font-weight:700; font-family:'Segoe UI'; padding:4px 14px; }"
            "QSpinBox:focus { border:2px solid #22c55e; }"
            "QSpinBox::up-button {"
            " width:20px; background:#1e2132;"
            " border-top-right-radius:7px;"
            " border-bottom-right-radius:0px; }"
            
            "QSpinBox::down-button {"
            " width:20px; background:#1e2132;"
            " border-bottom-right-radius:7px;"
            " border-top-right-radius:0px; }"
            f"QSpinBox::up-arrow {{ image: url({get_image_path('triangle_up.png')}); width:10px; height:10px; }}"
            f"QSpinBox::down-arrow {{ image: url({get_image_path('triangle_down.png')}); width:10px; height:10px; }}")
        
        passive_col.addWidget(passive_title)
        passive_col.addWidget(passive_sub)
        passive_col.addWidget(self.passive_spin)
        passive_col.addStretch()

        agent_cfg_lay.addLayout(active_col)
        agent_cfg_lay.addLayout(passive_col)

        self.agent_config.setMaximumHeight(0)
        self.agent_config.setVisible(False)

        c_agent.addWidget(self.agent_config)

        # ── Agent Interfaces config (hidden until interfaces morph) ───────────
        self.agent_interfaces_scroll = QScrollArea()
        self.agent_interfaces_scroll.setWidgetResizable(True)
        self.agent_interfaces_scroll.setObjectName("agent_scroll")
        self.agent_interfaces_scroll.setStyleSheet("QScrollArea#agent_scroll { background: transparent; border: none; }")
        self.agent_interfaces_config = QWidget()
        self.agent_interfaces_config.setObjectName("agent_config")
        self.agent_interfaces_config.setStyleSheet("QWidget#agent_config { background: transparent; }")
        self.agent_interfaces_lay = QHBoxLayout(self.agent_interfaces_config)
        self.agent_interfaces_lay.setContentsMargins(0, 10, 0, 0)
        self.agent_interfaces_lay.setSpacing(30)
        self.agent_interfaces_scroll.setWidget(self.agent_interfaces_config)
        self.agent_interfaces_scroll.setMaximumHeight(0)
        self.agent_interfaces_scroll.setVisible(False)
        c_agent.addWidget(self.agent_interfaces_scroll)

        c_agent.addStretch()
        self._slider.addPage(p_agent)

        def agent_changed(mode):
            self.agent_mode = mode
        self.agent_cards.selection_changed.connect(agent_changed)

        # ── Page 5: Module Names ──────────────────────────────────────────────
        p_mod = self._make_card()
        c_mod = p_mod.property("cl")
        hdr_5, _ = self._step_header("STEP 5", "Module Names")
        c_mod.addWidget(hdr_5)
        c_mod.addWidget(self._lbl("Name the design blocks that will be connected by your verification environment.", "subtitle"))
        c_mod.addWidget(self._divider())

        # ── Info banner ──


        # ── Module cards row ──
        mod_row = QHBoxLayout(); mod_row.setSpacing(14)

        # --- DUT Card ---
        dut_card = QFrame(); dut_card.setObjectName("module_name_card")
        dut_col = QVBoxLayout(dut_card); dut_col.setContentsMargins(20, 18, 20, 18); dut_col.setSpacing(10)
        dut_top = QHBoxLayout(); dut_top.setSpacing(10)
        dut_badge = QLabel("⚙️"); dut_badge.setObjectName("dut_badge")
        dut_top.addWidget(dut_badge)
        dut_top.addWidget(self._lbl("DUT MODULE", "module_card_title"))
        dut_top.addStretch()
        dut_top.addWidget(self._lbl("REQUIRED", "required_tag"))
        dut_col.addLayout(dut_top)
        dut_col.addWidget(self._lbl("The hardware implementation under test", "module_card_hint"))
        dut_col.addSpacing(4)
        self.dut_input = QLineEdit(self.ui_state.get("dut_module", tcl["dut_module"]))
        self.dut_input.setObjectName("module_input")
        self.dut_input.setPlaceholderText("e.g.  FFT_DUT")
        self.dut_input.setFixedHeight(44)
        dut_col.addWidget(self.dut_input)
        self.dut_preview = self._lbl("Instance: dut", "module_preview")
        dut_col.addWidget(self.dut_preview)
        mod_row.addWidget(dut_card, stretch=1)

        self.golden_widget = QWidget()
        golden_card = QFrame(); golden_card.setObjectName("module_name_card")
        golden_col = QVBoxLayout(golden_card); golden_col.setContentsMargins(20, 18, 20, 18); golden_col.setSpacing(10)
        golden_top = QHBoxLayout(); golden_top.setSpacing(10)
        golden_badge = QLabel("📐"); golden_badge.setObjectName("golden_badge")
        golden_top.addWidget(golden_badge)
        golden_top.addWidget(self._lbl("GOLDEN MODEL", "module_card_title"))
        golden_top.addStretch()
        golden_top.addWidget(self._lbl("REFERENCE", "reference_tag"))
        golden_col.addLayout(golden_top)
        golden_col.addWidget(self._lbl("The expected-behavior reference module", "module_card_hint"))
        golden_col.addSpacing(4)
        self.golden_input = QLineEdit(self.ui_state.get("golden_module", tcl["golden_module"]))
        self.golden_input.setObjectName("module_input")
        self.golden_input.setPlaceholderText("e.g.  FFT_Golden_Model")
        self.golden_input.setFixedHeight(44)
        golden_col.addWidget(self.golden_input)
        self.golden_preview = self._lbl("Instance: golden_model", "module_preview")
        golden_col.addWidget(self.golden_preview)
        golden_widget_lay = QVBoxLayout(self.golden_widget)
        golden_widget_lay.setContentsMargins(0, 0, 0, 0)
        golden_widget_lay.addWidget(golden_card)
        mod_row.addWidget(self.golden_widget, stretch=1)
        self.golden_widget.setVisible(self.golden_model_type == "RTL")

        c_mod.addLayout(mod_row)

        def update_module_preview():
            dut_name = self.dut_input.text().strip() or "dut"
            golden_name = self.golden_input.text().strip() or "golden_model"
            self.dut_preview.setText(f"Instance: {dut_name.lower()}")
            self.golden_preview.setText(f"Instance: {golden_name.lower()}")

        self.dut_input.textChanged.connect(update_module_preview)
        self.golden_input.textChanged.connect(update_module_preview)
        update_module_preview()
        c_mod.addSpacing(6)


        # ── Source Files Zones (DUT & REF) ────────────────────────────────────
        def _build_src_zone(default_title, state_key):
            if state_key not in self.ui_state:
                self.ui_state[state_key] = []
            source_list = self.ui_state[state_key]
            
            zone = QFrame()
            zone.setObjectName("rtl_zone")
            zone_lay = QVBoxLayout(zone)
            zone_lay.setContentsMargins(18, 16, 18, 16)
            zone_lay.setSpacing(10)
            
            header = QHBoxLayout()
            title_col = QVBoxLayout(); title_col.setSpacing(2)
            title_lbl = self._lbl(default_title, "rtl_zone_title")
            title_col.addWidget(title_lbl)
            title_col.addWidget(self._lbl("Select the .v / .sv files", "rtl_zone_hint"))
            header.addLayout(title_col, stretch=1)
            
            browse_btn = QPushButton("+  Add Files")
            browse_btn.setObjectName("rtl_browse_btn")
            browse_btn.setFixedHeight(36)
            browse_folder_btn = QPushButton('+  Add Folder')
            browse_folder_btn.setObjectName('rtl_browse_folder_btn')
            browse_folder_btn.setFixedHeight(36)
            buttons_lay = QHBoxLayout()
            buttons_lay.addWidget(browse_btn)
            buttons_lay.addWidget(browse_folder_btn)
            header.addLayout(buttons_lay)
            zone_lay.addLayout(header)
            
            order_hint = self._lbl("Please order the files (Drag & Drop to reorder)", "rtl_zone_hint")
            order_hint.setStyleSheet("color: #60a5fa; font-weight: bold; font-style: italic; margin-top: -5px;")
            order_hint.hide()
            zone_lay.addWidget(order_hint)
            
            from PyQt5.QtWidgets import QAbstractItemView, QListWidgetItem
            files_list = QListWidget()
            files_list.setObjectName("rtl_files_list")
            files_list.setMinimumHeight(120)
            files_list.setSpacing(4)
            files_list.setSelectionMode(QListWidget.ExtendedSelection)
            files_list.setDragDropMode(QAbstractItemView.InternalMove)
            
            for f in source_list:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, f)
                files_list.addItem(item)
                
            zone_lay.addWidget(files_list, stretch=1)
            
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            clear_btn = QPushButton("✕  Remove Selected")
            clear_btn.setObjectName("rtl_clear_btn")
            clear_btn.setFixedHeight(28)
            btn_row.addWidget(clear_btn)
            zone_lay.addLayout(btn_row)
            
            def _refresh():
                count = files_list.count()
                order_hint.setVisible(count > 1)
                source_list.clear()
                for i in range(count):
                    item = files_list.item(i)
                    full_path = item.data(Qt.UserRole)
                    source_list.append(full_path)
                    import os
                    basename = os.path.basename(full_path)
                    if i == 0:
                        item.setText(f"{basename}    ← [Top module]")
                    else:
                        item.setText(basename)
            
            _refresh()
            files_list.model().rowsMoved.connect(lambda *args: _refresh())
            
            def _on_browse():
                from PyQt5.QtWidgets import QFileDialog
                files, _ = QFileDialog.getOpenFileNames(self, f"Select {default_title}", "", "RTL Files (*.v *.sv *.vhd *.vhdl);;All Files (*)")
                for f in files:
                    f = f.replace("\\", "/")
                    already_in = False
                    for i in range(files_list.count()):
                        if files_list.item(i).data(Qt.UserRole) == f:
                            already_in = True
                            break
                    if not already_in:
                        item = QListWidgetItem()
                        item.setData(Qt.UserRole, f)
                        files_list.addItem(item)
                _refresh()

            def _on_browse_folder():
                from PyQt5.QtWidgets import QFileDialog
                folder = QFileDialog.getExistingDirectory(self, f"Select {default_title} Folder", "")
                if folder:
                    import glob
                    # Add all .v and .sv files in the folder
                    for ext in ["*.v", "*.sv", "*.vhd", "*.vhdl"]:
                        for f in glob.glob(os.path.join(folder, ext)):
                            f = f.replace("\\", "/")
                            already_in = False
                            for i in range(files_list.count()):
                                if files_list.item(i).data(Qt.UserRole) == f:
                                    already_in = True
                                    break
                            if not already_in:
                                item = QListWidgetItem()
                                item.setData(Qt.UserRole, f)
                                files_list.addItem(item)
                    _refresh()
                
            def _on_clear():
                for item in files_list.selectedItems():
                    files_list.takeItem(files_list.row(item))
                _refresh()
                
            browse_btn.clicked.connect(_on_browse)
            browse_folder_btn.clicked.connect(_on_browse_folder)
            clear_btn.clicked.connect(_on_clear)
            
            return zone, title_lbl, source_list, files_list

        self.rtl_source_zone, self.rtl_source_title, self.rtl_source_files, self.rtl_files_list = _build_src_zone("DUT SOURCE FILES" if self.golden_model_type == "RTL" else "RTL SOURCE FILES", "rtl_files")
        self.ref_source_zone, self.ref_source_title, self.ref_source_files, self.ref_files_list = _build_src_zone("REF SOURCE FILES", "ref_files")
        
        src_zones_lay = QHBoxLayout()
        src_zones_lay.setSpacing(14)
        src_zones_lay.addWidget(self.rtl_source_zone, stretch=1)
        src_zones_lay.addWidget(self.ref_source_zone, stretch=1)
        c_mod.addLayout(src_zones_lay, stretch=1)
        
        self.ref_source_zone.setVisible(self.golden_model_type == "RTL")

        self._slider.addPage(p_mod)


        # ── Page 6: Ports (Dynamic internal pages) ─────────────────────────────
        p_ports = self._make_card()
        c_ports = p_ports.property("cl")
        
        ports_hdr, self.ports_title = self._step_header("STEP 6", "Interface Ports")
        self.ports_subtitle = self._lbl("Configure each agent interface and its optional clock signal", "subtitle")
        self.ports_subtitle.setFixedHeight(20)
        c_ports.addWidget(ports_hdr)
        c_ports.addWidget(self.ports_subtitle)
        ports_divider = self._divider()
        ports_divider.setFixedHeight(1)
        c_ports.addWidget(ports_divider)
        c_ports.addSpacing(4)
        
        # ── Assumption notice ─────────────────────────────────────────────────
        self.assumption_note = QLabel(
            "⚠  Assumption: The port names in the DUT and "
            "Golden Model are identical.")
        self.assumption_note.setWordWrap(True)
        self.assumption_note.setStyleSheet(
            "color:#fbbf24; font-size:11px; font-family:'Segoe UI';"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1c1700,stop:1 #1a1510);"
            "border:1px solid #78430a;"
            "border-radius:10px; padding:10px 14px;")
        c_ports.addWidget(self.assumption_note)
        self.assumption_note.setVisible(self.golden_model_type == "RTL")
        c_ports.addSpacing(4)

        self.ports_slider = SlidingWidget(self)
        c_ports.addWidget(self.ports_slider, stretch=1)
        self.port_sections = []  # tuples: (title, subtitle, input section, output section, page)
        
        self._slider.addPage(p_ports)

        # ── Page 7: Sequences ─────────────────────────────────────────────────
        p_seq = self._make_card()
        c_seq = p_seq.property("cl")
        hdr_7, _ = self._step_header("STEP 7", "Sequences")
        c_seq.addWidget(hdr_7)
        c_seq.addWidget(self._lbl("Add test sequences for your UVM environment", "subtitle"))
        c_seq.addWidget(self._divider())

        saved_seqs = self.ui_state.get("sequence_list", tcl["sequence_list"])
        self.seq_section = SeqSection(defaults=saved_seqs)
        c_seq.addWidget(self._wrap_port_card(self.seq_section))
        c_seq.addStretch()
        self._slider.addPage(p_seq)

        # ── Page 5: Generate ──────────────────────────────────────────────────
        p_gen = QWidget()
        p_gen.setStyleSheet("background-color: #000000;")
        c_gen = QVBoxLayout(p_gen)
        c_gen.setContentsMargins(40, 40, 40, 40)
        
        # Custom Back Button since bottom nav is hidden
        top_lay = QHBoxLayout()
        self.gen_back_btn = QPushButton("← Back to Sequences")
        self.gen_back_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #475569; font-size: 15px; border: none; font-family: 'Segoe UI'; font-weight: bold;
            }
            QPushButton:hover { color: #a78bfa; }
        """)
        self.gen_back_btn.setCursor(Qt.PointingHandCursor)
        self.gen_back_btn.clicked.connect(self._go_back)
        top_lay.addWidget(self.gen_back_btn)
        top_lay.addStretch()
        c_gen.addLayout(top_lay)
        
        c_gen.addStretch()
        
        gen_lay = QHBoxLayout()
        gen_lay.addStretch()
        
        self.big_generate_btn = QPushButton("GENERATE⚡UVM")
        self.big_generate_btn.setObjectName("big_generate_btn")
        self.big_generate_btn.setCursor(Qt.PointingHandCursor)
        self.big_generate_btn.setFixedSize(int(400*1.1), int(110*1.1))
        self.big_generate_btn_style = """
            QPushButton#big_generate_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: white;
                font-size: 32px;
                font-weight: 900;
                font-family: 'Segoe UI';
                border-radius: 45px;
                border: 2px solid #a78bfa;
            }
            QPushButton#big_generate_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
                border: 2px solid #ddd6fe;
            }
            QPushButton#big_generate_btn:pressed {
                background: #3730a3;
                border: 2px solid #c4b5fd;
            }
        """
        self.big_generate_btn.setStyleSheet(self.big_generate_btn_style)

        
        # Pulsing glow effect
        self.glow_effect = QGraphicsDropShadowEffect(self.big_generate_btn)
        self.glow_effect.setBlurRadius(100)
        self.glow_effect.setOffset(0, 0)
        self.glow_effect.setColor(QColor(139, 92, 246, 255))
        self.big_generate_btn.setGraphicsEffect(self.glow_effect)

        # Breathing animation: blur oscillates 80 → 300 → 80
        self._glow_anim = QVariantAnimation(self)
        self._glow_anim.setStartValue(100.0)
        self._glow_anim.setEndValue(300.0)
        self._glow_anim.setDuration(1800)  # half-cycle in ms
        self._glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._glow_anim.setLoopCount(-1)   # infinite
        self._glow_anim.valueChanged.connect(
            lambda v: self.glow_effect.setBlurRadius(v))
        # Reverse direction each cycle for true in/out breathing
        self._glow_forward = True
        def _on_glow_iteration():
            self._glow_forward = not self._glow_forward
            self._glow_anim.setStartValue(100.0 if self._glow_forward else 300.0)
            self._glow_anim.setEndValue(300.0 if self._glow_forward else 100.0)
        self._glow_anim.currentLoopChanged.connect(_on_glow_iteration)
        self._glow_anim.start()
        
        self.big_generate_btn.clicked.connect(self._on_generate)
        
        gen_lay.addWidget(self.big_generate_btn)
        gen_lay.addStretch()
        c_gen.addLayout(gen_lay)
        c_gen.addSpacing(40)
        
        from PyQt5.QtWidgets import QSizePolicy
        self.bottom_spacer = QWidget()
        self.bottom_spacer.setStyleSheet("background: transparent; border: none;")
        self.bottom_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        c_gen.addWidget(self.bottom_spacer)
        if self.SHOW_LOG_UI:
            self.bottom_spacer.hide()

        
        # Log Output
        self.log_container = QWidget()
        log_lay = QVBoxLayout(self.log_container)
        log_lay.setContentsMargins(0, 0, 0, 0)
        
        lh = QHBoxLayout()
        lh.addWidget(self._lbl("OUTPUT LOG", "log_label")); lh.addStretch()
        self.clear_btn = QPushButton("Clear"); self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        lh.addWidget(self.clear_btn); log_lay.addLayout(lh)
        
        self.log_output = QTextEdit(); self.log_output.setObjectName("log_output")
        self.log_output.setReadOnly(True); self.log_output.setMinimumHeight(150)
        self.clear_btn.clicked.connect(self.log_output.clear)
        log_lay.addWidget(self.log_output)
        
        c_gen.addWidget(self.log_container)
        
        if not self.SHOW_LOG_UI:
            self.log_container.hide()
        
        self._slider.addPage(p_gen)

        # ── Navigation row ────────────────────────────────────────────────────
        self.nav = QWidget()
        self.nav.setObjectName("nav_bar")
        self.nav.setStyleSheet("QWidget#nav_bar { background:#0a0c13; border-top:1px solid rgba(255, 255, 255, 0.07); }")
        nl = QHBoxLayout(self.nav); nl.setContentsMargins(28, 14, 28, 14); nl.setSpacing(14)

        self._back_btn = QPushButton("← Back"); self._back_btn.setObjectName("back_btn")
        self._back_btn.setFixedHeight(40); self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.clicked.connect(self._go_back)
        nl.addWidget(self._back_btn)
        nl.addStretch()


        self._next_btn = QPushButton("Next →"); self._next_btn.setObjectName("next_btn")
        self._next_btn.setFixedHeight(40); self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.clicked.connect(self._go_next)
        nl.addWidget(self._next_btn)

        vlay.addWidget(self.nav)
        self._update_nav()
        return root

    def _make_card(self):
        """Returns a scrollable outer widget containing a styled card. card's QVBoxLayout stored as Qt property 'cl'."""
        outer = QWidget(); outer.setObjectName("root")
        ol = QVBoxLayout(outer); ol.setContentsMargins(20, 20, 20, 14); ol.setSpacing(0)
        card = QFrame(); card.setObjectName("card")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(40); sh.setOffset(0,8)
        sh.setColor(QColor(0,0,0,100)); card.setGraphicsEffect(sh)
        cl = QVBoxLayout(card); cl.setContentsMargins(26,24,26,24); cl.setSpacing(12)
        outer.setProperty("cl", cl)
        ol.addWidget(card)
        return outer

    def _build_interface_port_page(self, title, subtitle, in_defaults=None, out_defaults=None):
        """Build one interface page with one optional, prominent clock signal."""
        page = QWidget()
        page.title = title
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(0, 0, 0, 0)
        page_lay.setSpacing(14)

        timing_zone = QFrame()
        timing_zone.setObjectName("timing_zone")
        timing_lay = QVBoxLayout(timing_zone)
        timing_lay.setContentsMargins(18, 16, 18, 18)
        timing_lay.setSpacing(12)

        timing_header = QVBoxLayout()
        timing_header.setSpacing(3)
        header_title = self._lbl("CLOCK CONFIGURATION", "timing_title")
        header_title.setAlignment(Qt.AlignCenter)
        timing_header.addWidget(header_title)
        timing_lay.addLayout(timing_header)

        clock_card = QFrame()
        clock_card.setObjectName("clock_feature_card")
        clock_card.setFixedWidth(620)
        clock_lay = QVBoxLayout(clock_card)
        clock_lay.setContentsMargins(16, 12, 16, 12)
        clock_lay.setSpacing(6)

        clock_head = QHBoxLayout()
        clock_head.setSpacing(10)
        badge = QLabel("CLK")
        badge.setObjectName("clock_badge")
        clock_head.addWidget(badge)
        label_col = QVBoxLayout(); label_col.setSpacing(2)
        label_col.addWidget(self._lbl("CLOCK SIGNAL", "timing_signal_title"))
        label_col.addWidget(self._lbl("Does this interface have a clock port?", "timing_signal_hint"))
        clock_head.addLayout(label_col)
        clock_head.addStretch()
        clock_toggle = ToggleSwitch(checked=True)
        clock_head.addWidget(clock_toggle)
        clock_lay.addLayout(clock_head)

        clock_input = QLineEdit("clk")
        clock_input.setObjectName("timing_input")
        clock_input.setPlaceholderText("Enter the clock port name, e.g. clk_i")
        clock_input.setFixedHeight(42)
        clock_lay.addWidget(clock_input)
        clock_toggle.toggled.connect(clock_input.setEnabled)

        # Restore clock state from saved ui_state (parsed from run.tcl by parser.py)
        saved_clock_name = getattr(self, '_saved_clock_name', self.ui_state.get("clock_name", "clk"))
        saved_clock_en   = getattr(self, '_saved_clock_en',   self.ui_state.get("clock_en",   True))
        clock_input.setText(saved_clock_name)
        clock_toggle.setChecked(saved_clock_en)
        clock_input.setEnabled(saved_clock_en)

        clock_row = QHBoxLayout()
        clock_row.addStretch()
        clock_row.addWidget(clock_card)
        clock_row.addStretch()
        timing_lay.addLayout(clock_row)
        page_lay.addWidget(timing_zone)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("ports_separator")
        page_lay.addWidget(separator)

        ports_row = QHBoxLayout()
        ports_row.setSpacing(14)
        in_section = PortSection("INPUT PORTS", defaults=in_defaults)
        out_section = PortSection("OUTPUT PORTS", defaults=out_defaults)
        ports_row.addWidget(self._wrap_port_card(in_section), stretch=1)
        ports_row.addWidget(self._wrap_port_card(out_section), stretch=1)
        page_lay.addLayout(ports_row)

        page.clock_toggle = clock_toggle
        page.clock_input = clock_input
        page.in_section = in_section
        page.out_section = out_section
        return page, in_section, out_section
    def _generate_port_pages(self):
        self.ports_slider.clear()
        self.port_sections = []

        def add_interface_page(title, subtitle, in_defaults=None, out_defaults=None):
            page, in_section, out_section = self._build_interface_port_page(
                title, subtitle, in_defaults=in_defaults, out_defaults=out_defaults)
            self.ports_slider.addPage(page)
            self.port_sections.append((title, subtitle, in_section, out_section, page))

        if self.agent_mode == "SINGLE":
            # input_ports in ui_state are already stripped of the clock port by parser.py
            add_interface_page(
                "Single Agent Interface",
                "Configure timing signals and data ports for the single verification interface.",
                in_defaults=self.ui_state.get("input_ports", []),
                out_defaults=self.ui_state.get("output_ports", []))

        elif self.agent_mode == "MULTI":
            active_names = [
                field.text().strip() or field.placeholderText()
                for field in getattr(self, "_active_interface_inputs", [])
            ]
            passive_names = [
                field.text().strip() or field.placeholderText()
                for field in getattr(self, "_passive_interface_inputs", [])
            ]
            for name in active_names:
                add_interface_page(
                    f"Active Agent: {name}",
                    f"Configure timing signals and data ports for the {name} interface.")
            for name in passive_names:
                add_interface_page(
                    f"Passive Agent: {name}",
                    f"Configure timing signals and data ports for the {name} interface.")

        self._update_ports_title()

    def _collect_port_data(self):
        """Collect every enabled timing signal and regular port from Step 6."""
        input_ports, output_ports = [], []
        for _, _, in_section, out_section, page in self.port_sections:
            if page.clock_toggle.isChecked() and page.clock_input.text().strip():
                input_ports.append((page.clock_input.text().strip(), 1))
            input_ports.extend(in_section.get_ports())
            output_ports.extend(out_section.get_ports())
        return input_ports, output_ports

    def _update_ports_title(self):
        idx = self.ports_slider.currentIndex()
        if 0 <= idx < len(self.port_sections):
            title, subtitle, *_ = self.port_sections[idx]
            self.ports_title.setText(title)
            self.ports_subtitle.setText(subtitle)

    def _update_nav(self, target_idx=None):
        if target_idx is not None:
            idx = target_idx
        else:
            idx = self._slider.currentIndex()

        self._back_btn.setVisible(idx > 0)
        self._next_btn.setVisible(idx < 7)

        # Agents page (slider index 3) is skipped — map slider idx to step bar idx.
        # StepBar has 7 labels (Agents removed), so slider indices 4-7 map to bar 3-6.
        bar_idx = idx if idx < 3 else idx - 1
        self._step_bar.set_step(bar_idx)

        is_gen = (idx == 7)
        self._step_bar.setVisible(not is_gen)
        self.nav.setVisible(not is_gen)

        if is_gen:
            self.statusBar().hide()
        else:
            self.statusBar().show()

    def _go_next(self):
        if hasattr(self, '_slider') and getattr(self._slider, '_busy', False): return
        idx = self._slider.currentIndex()
        if idx == 0:
            if not self.project_input.text().strip():
                self.statusBar().showMessage("⚠  Enter a project name first"); return
            if not self.path_input.text().strip():
                self.statusBar().showMessage("⚠  Enter an output directory first"); return
                
        if idx == 1:
            if not getattr(self, 'golden_model_type', None):
                self.statusBar().showMessage("⚠  Please select a Golden Model Type first"); return
                
            if self.golden_model_type == "SB":
                if not getattr(self, '_is_morphed', False):
                    self._morph_step2(forward=True)
                    return
                if not self.sb_language:
                    self.statusBar().showMessage("⚠  Please select a Software Language first"); return

        # Skip Agents page entirely — always use Single Agent configuration
        if idx == 2:
            self.agent_mode = "SINGLE"
            self.num_active_agents = 0
            self.num_passive_agents = 0
            self._update_nav(4)
            self._slider.slide_to(4)
            return

        if idx == 4:
            if not self.dut_input.text().strip():
                self.statusBar().showMessage("⚠  Enter a DUT module name"); return
            if self.golden_model_type == "RTL" and not self.golden_input.text().strip():
                self.statusBar().showMessage("⚠  Enter a Golden Model module name"); return
                
            if not getattr(self, 'rtl_source_files', None):
                self.statusBar().showMessage("⚠  Please add your RTL source file"); return
                
            if self.golden_model_type == "RTL" and not getattr(self, 'ref_source_files', None):
                self.statusBar().showMessage("⚠  Please add your Reference Model source file"); return
                
            # Automatically parse SV Top Module for ports
            top_file = None
            if hasattr(self, 'rtl_source_files') and self.rtl_source_files:
                top_file = self.rtl_source_files[0]
            
            if top_file:
                import os, sys, re
                if os.path.exists(top_file):
                    if BACKEND_SELF_DIR not in sys.path:
                        sys.path.append(BACKEND_SELF_DIR)
                    try:
                        from sv_parser import parse_sv_ports
                        parsed_ports = parse_sv_ports(top_file)
                        if parsed_ports:
                            in_ports = []
                            out_ports = []
                            # Build a parameter value map from the file
                            param_values = {}
                            try:
                                import math
                                raw = open(top_file, 'r', encoding='utf-8').read()
                                raw = re.sub(r'//.*', '', raw)
                                raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)
                                # Pass 1: plain integer parameters only (e.g. DATA_WIDTH = 32, DEPTH = 7)
                                for pm in re.finditer(r'\bparameter\b[^=\n]*?(\w+)\s*=\s*(\d+)', raw):
                                    param_values[pm.group(1).strip()] = int(pm.group(2))
                                # Pass 2: clog2-based parameters (e.g. ADDR_DEPTH = (DEPTH>1)?$clog2(DEPTH):1)
                                for pm in re.finditer(r'\bparameter\b[^=\n]*?(\w+)\s*=.*?\$clog2\((\w+)\)', raw):
                                    pname = pm.group(1).strip()
                                    ref   = pm.group(2).strip()
                                    if ref in param_values:
                                        param_values[pname] = max(1, math.ceil(math.log2(param_values[ref])))
                            except Exception:
                                pass

                            def extract_bits(w, pvals=param_values):
                                if not w: return 1
                                # Concrete [N:M]
                                m = re.search(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', w)
                                if m: return abs(int(m.group(1)) - int(m.group(2))) + 1
                                # Symbolic [PARAM-1:0]
                                m = re.search(r'\[\s*(\w+)\s*-\s*1\s*:\s*0\s*\]', w)
                                if m:
                                    pname = m.group(1)
                                    if pname in pvals:
                                        return pvals[pname]
                                    return 32
                                if ':' in w: return 32
                                return 1
                            
                            for p in parsed_ports:
                                name = p["name"]
                                dir_ = p["direction"]
                                bits = extract_bits(p["width"])
                                
                                # Only filter out clear clock signals (not resets)
                                lower_name = name.lower()
                                if lower_name in ["clk", "clock"] or lower_name.endswith("_clk") or lower_name.endswith("_clock") or lower_name.startswith("clk_"):
                                    self.ui_state["clock_name"] = name
                                    continue
                                    
                                if dir_ == "input":
                                    in_ports.append((name, bits))
                                elif dir_ in ["output", "inout", "ref"]:
                                    out_ports.append((name, bits))
                                    
                            if in_ports or out_ports:
                                self.ui_state["input_ports"] = in_ports
                                self.ui_state["output_ports"] = out_ports
                    except Exception as e:
                        print("SV Parse error:", e)
                        
            # Entering Ports step -> regenerate dynamic pages
            self._generate_port_pages()
            self._update_nav(idx + 1)
            self._slider.slide_to(idx + 1)
            return

        if idx == 5:
            internal_idx = self.ports_slider.currentIndex()
            if internal_idx < self.ports_slider.count() - 1:
                self.ports_slider.slide_to(internal_idx + 1)
                QTimer.singleShot(420, self._update_ports_title)
                return
            else:
                self._update_nav(idx + 1)
                self._slider.slide_to(idx + 1)
                return

        if idx == 6:
            seqs = self.seq_section.get_sequences()
            if not seqs:
                self.statusBar().showMessage("⚠  Add at least one sequence before continuing"); return
            
            seen_seqs = set()
            for seq_name, _ in seqs:
                if seq_name in seen_seqs:
                    self.statusBar().showMessage(f"⚠  Sequence '{seq_name}' is duplicated"); return
                seen_seqs.add(seq_name)

            self._slider.slide_to(7, style="fade_dark", mid_callback=lambda: self._update_nav(7))
        else:
            self._update_nav(idx + 1)
            self._slider.slide_to(idx + 1)

    def _go_back(self):
        if hasattr(self, '_slider') and getattr(self._slider, '_busy', False): return
        idx = self._slider.currentIndex()
        if idx == 1 and getattr(self, '_is_morphed', False):
            self._morph_step2(forward=False)
            return

        # Skip Agents page entirely when navigating back from Modules
        if idx == 4:
            self.agent_mode = None
            self._update_nav(2)
            self._slider.slide_to(2)
            return

        if idx == 5:
            internal_idx = self.ports_slider.currentIndex()
            if internal_idx > 0:
                self.ports_slider.slide_to(internal_idx - 1)
                QTimer.singleShot(420, self._update_ports_title)
                return
            else:
                self._update_nav(idx - 1)
                self._slider.slide_to(idx - 1)
                return
        
        if idx == 7:
            self._slider.slide_to(6, style="fade_dark", mid_callback=lambda: self._update_nav(6))
            return

        self._update_nav(idx - 1)
        self._slider.slide_to(idx - 1)

    # ── Stylesheet ─────────────────────────────────────────────────────────────
    def _apply_stylesheet(self):
        self.setStyleSheet("""
        QMainWindow, QWidget#root { background: #0f1117; }
        QFrame#card { background:#1a1d27; border-radius:16px; border:1px solid #2a2d3e; }
        QPushButton#gm_btn {
            background:#1e2132; color:#94a3b8; font-size:14px; font-weight:600; font-family:'Segoe UI';
            border:2px solid #2a2d3e; border-radius:12px; padding:10px; text-align: center;
        }
        QPushButton#gm_btn:hover { border:2px solid #6366f1; background:#23273b; }
        QPushButton#gm_btn:checked { border:2px solid #22c55e; color:#e2e8f0; background:#1c2f2d; }
        QPushButton#gm_btn QLabel { background: transparent; color: inherit; }
        
        QFrame#premium_card { background: #12151e; border: 1px solid #23273b; border-radius: 16px; }
        QLabel#premium_label { color: #94a3b8; font-size: 12px; font-weight: 800; font-family: 'Segoe UI'; letter-spacing: 1px; }
        QLineEdit#premium_input {
            background: #090a0f; border: 2px solid #1e2132; border-radius: 12px;
            color: #f1f5f9; font-size: 15px; font-family: 'Segoe UI'; padding: 14px 18px;
        }
        QLineEdit#premium_input:focus { border: 2px solid #6366f1; background: #0f1117; }
        
        QPushButton#premium_browse {
            background: #1e2132; color: #cbd5e1; font-size: 14px; font-weight: 700;
            font-family: 'Segoe UI'; border: 2px solid #2a2d3e; border-radius: 12px; padding: 14px 24px;
        }
        QPushButton#premium_browse:hover { background: #23273b; border: 2px solid #6366f1; color: white; }
        QPushButton#premium_browse:pressed { background: #1a1d27; }

        QLabel#title   { color:#e2e8f0; font-size:18px; font-weight:700; font-family:'Segoe UI'; }
        QLabel#step_number { color:#8b5cf6; font-size:13px; font-weight:800; font-family:'Segoe UI'; letter-spacing:1.5px; }
        QLabel#step_title { color:#ffffff; font-size:26px; font-weight:700; font-family:'Segoe UI'; }
        QLabel#subtitle{ color:#64748b; font-size:12px; font-family:'Segoe UI'; }
        QLabel#field_label { color:#94a3b8; font-size:11px; font-weight:700;
                             font-family:'Segoe UI'; letter-spacing:1.2px; }
        QLabel#seq_header_label { color:#14b8a6; font-size:11px; font-weight:800;
                             font-family:'Segoe UI'; letter-spacing:1.2px; text-transform:uppercase; }
        QLabel#bit_lbl { color:#4a5568; font-size:11px; font-family:'Segoe UI'; }
        QLineEdit#project_input, QLineEdit#path_input {
            background:#0f1117; border:2px solid #2a2d3e; border-radius:10px;
            color:#e2e8f0; font-size:14px; font-family:'Segoe UI'; padding:10px 14px; }
        QLineEdit#project_input:focus, QLineEdit#path_input:focus { border:2px solid #6366f1; }
        QLineEdit#port_input {
            background:#0d0f18; border:1px solid #2a2d3e; border-radius:7px;
            color:#e2e8f0; font-size:12px; font-family:'Segoe UI'; padding:3px 8px;
            min-height:20px; max-height:20px; }
        QLineEdit#port_input:focus { border:1px solid #6366f1; }
        QFrame#module_intro {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0f1633,stop:0.5 #151b38,stop:1 #111531);
            border:1px solid #29355a; border-radius:13px; }
        QLabel#module_intro_icon { color:#818cf8; font-size:20px; font-weight:700; background:transparent; }
        QLabel#module_intro_title { color:#c7d2fe; font-size:12px; font-weight:800;
                                   font-family:'Segoe UI'; letter-spacing:1.6px; }
        QLabel#module_intro_text { color:#8590ad; font-size:11px; font-family:'Segoe UI'; }
        QFrame#module_name_card {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #151a2a,stop:1 #111624);
            border:1px solid #293044; border-radius:14px; }
        QFrame#module_name_card:hover { border-color:#6366f1; background:#171d2e; }
        QLabel#module_card_title { color:#e2e8f0; font-size:13px; font-weight:800;
                                  font-family:'Segoe UI'; letter-spacing:1.2px; }
        QLabel#module_card_hint { color:#71809a; font-size:11px; font-family:'Segoe UI'; }
        QLabel#dut_badge, QLabel#golden_badge {
            min-width:28px; max-width:28px; min-height:28px; max-height:28px;
            border-radius:14px; qproperty-alignment:AlignCenter; font-size:14px; font-weight:800; background:transparent; }
        QLabel#dut_badge { background:#1e3a5f; color:#7dd3fc; border:1px solid #38bdf8; }
        QLabel#golden_badge { background:#35234f; color:#c4b5fd; border:1px solid #8b5cf6; }
        QPushButton#rtl_browse_btn, QPushButton#rtl_browse_folder_btn {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e293b,stop:1 #334155);
            color:#e2e8f0; font-size:12px; font-weight:700; font-family:'Segoe UI';
            border:1px solid #475569; border-radius:10px; padding:0 18px; }
        QPushButton#rtl_browse_btn:hover, QPushButton#rtl_browse_folder_btn:hover {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #334155,stop:1 #475569);
            color:#ffffff; border-color:#94a3b8; }
        QPushButton#rtl_browse_btn:pressed, QPushButton#rtl_browse_folder_btn:pressed { background:#0f172a; }
        QLabel#required_tag, QLabel#reference_tag {
            border-radius:8px; padding:4px 10px; font-size:9px; font-weight:800;
            font-family:'Segoe UI'; letter-spacing:.8px; }
        QLabel#required_tag { background:#1d3b32; color:#6ee7b7; border:1px solid #34d39988; }
        QLabel#reference_tag { background:#302640; color:#c4b5fd; border:1px solid #8b5cf688; }
        QLineEdit#module_input {
            background:#0b0f18; border:2px solid #1e293b; border-radius:10px;
            color:#f1f5f9; font-size:14px; font-family:'Consolas','Courier New'; padding:8px 12px; }
        QLineEdit#module_input:hover { border-color:#475569; }
        QLineEdit#module_input:focus { border:2px solid #818cf8; background:#0e1422; }
        QLabel#module_preview { color:#64748b; font-size:10px; font-family:'Consolas','Courier New'; }
        QLabel#module_flow { color:#6366f1; font-size:22px; font-weight:700; min-width:30px; }
        QFrame#rtl_zone {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #151a2a,stop:1 #111624);
            border:1px solid #293044; border-radius:14px; }
        QLabel#rtl_zone_title { color:#e2e8f0; font-size:13px; font-weight:800;
                                font-family:'Segoe UI'; letter-spacing:1.2px; }
        QLabel#rtl_zone_hint  { color:#71809a; font-size:11px; font-family:'Segoe UI'; }
        QPushButton#rtl_browse_btn {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e293b,stop:1 #334155);
            color:#e2e8f0; font-size:12px; font-weight:700; font-family:'Segoe UI';
            border:1px solid #475569; border-radius:9px; padding:0 16px; }
        QPushButton#rtl_browse_btn:hover {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #334155,stop:1 #475569);
            color:#ffffff; border-color:#94a3b8; }
        QPushButton#rtl_browse_btn:pressed { background:#0f172a; }
        QPushButton#rtl_clear_btn {
            background:transparent; color:#7f1d1d; font-size:11px; font-family:'Segoe UI';
            border:1px solid #962323; border-radius:7px; padding:0 12px; }
        QPushButton#rtl_clear_btn:hover { background:#1e2132; color:#f87171; border-color:#962323; }
        QListWidget#rtl_files_list {
            background:transparent; border:none; outline:none;
            color:#f1f5f9; font-size:12px; font-family:'Consolas','Courier New'; }
        QListWidget#rtl_files_list::item { 
            background:#0b0f18; border:2px solid #1e293b; border-radius:10px; padding:6px 12px; }
        QListWidget#rtl_files_list::item:selected { 
            background:#1e293b; border:2px solid #818cf8; color:#ffffff; }
        QListWidget#rtl_files_list::item:hover { 
            border-color:#475569; }

        QFrame#timing_zone {
            background:#101827; border:1px solid #334155; border-radius:15px; }
        QLabel#timing_title { color:#c7d2fe; font-size:12px; font-weight:800;
                              font-family:'Segoe UI'; letter-spacing:1.7px; }
        QLabel#timing_note { color:#8290a8; font-size:11px; font-family:'Segoe UI'; }
        QFrame#clock_feature_card {
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #132d46,stop:.5 #162238,stop:1 #1c1932);
            border:1px solid #536b91; border-radius:13px; }
        QFrame#clock_feature_card:hover { border-color:#7dd3fc; background:#162f49; }
        QLabel#clock_badge {
            min-width:48px; max-width:48px; min-height:42px; max-height:42px;
            border-radius:11px; qproperty-alignment:AlignCenter; font-size:12px; font-weight:900;
            font-family:'Segoe UI'; background:#0c4a6e; color:#bae6fd; border:1px solid #38bdf8; }
        QLabel#timing_signal_title { color:#f1f5f9; font-size:15px; font-weight:800;
                                     font-family:'Segoe UI'; letter-spacing:1px; }
        QLabel#timing_signal_hint { color:#b3c6dc; font-size:11px; font-family:'Segoe UI'; }

        QLineEdit#timing_input {
            background:#080d16; border:1px solid #4d6687; border-radius:8px;
            color:#f1f5f9; font-size:13px; font-family:'Consolas','Courier New'; padding:8px 11px; }
        QLineEdit#timing_input:hover { border-color:#7dd3fc; }
        QLineEdit#timing_input:focus { border:1px solid #a5b4fc; background:#0c1420; }
        QLineEdit#timing_input:disabled {
            background:#090d14; border-color:#1f2937; color:#475569; }
        QFrame#ports_separator { color:#344155; border:none; background:#344155; max-height:1px; }
        QSpinBox#bits_spin {
            background:#0d0f18; border:1px solid #2a2d3e; border-radius:7px;
            color:#e2e8f0; font-size:12px; font-family:'Segoe UI'; padding:2px 4px;
            min-height:20px; max-height:20px; min-width:56px; max-width:56px; }
        QSpinBox#bits_spin:focus { border:1px solid #6366f1; }
        QSpinBox#bits_spin::up-button {width:16px; background:#1e2132;border-top-right-radius:7px;
        border-bottom-right-radius:0px; }
          
        QSpinBox#bits_spin::down-button {width:16px; background:#1e2132;border-bottom-right-radius:7px;
        border-top-right-radius:0px; }


        QSpinBox::up-arrow { image: none; width:8px; height:8px; }
        QSpinBox::down-arrow { image: none; width:8px; height:8px; }
        QPushButton#generate_btn {
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366f1,stop:1 #8b5cf6);
            color:#fff; font-size:13px; font-weight:700; font-family:'Segoe UI';
            border:none; border-radius:10px; padding:0 28px; }
        QPushButton#generate_btn:hover {
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #818cf8,stop:1 #a78bfa); }
        QPushButton#generate_btn:disabled { background:#2a2d3e; color:#4a4d60; }
        QPushButton#next_btn {
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:0,
                stop:0 #4f46e5,
                stop:0.5 #6d28d9,
                stop:1 #7c3aed
            );
        
            color: #ffffff;
        
            font-family: "Segoe UI";
            font-size: 13px;
            font-weight: 700;
        
            border: 1px solid #8b5cf6;
            border-radius: 15px;
        
            padding: 0px 24px;
            min-height: 40px;
        }
        
        QPushButton#next_btn:hover {
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:0,
                stop:0 #6366f1,
                stop:0.5 #7c3aed,
                stop:1 #9333ea
            );
        
            border: 1px solid #c4b5fd;
        }
        
        QPushButton#next_btn:pressed {
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:0,
                stop:0 #3730a3,
                stop:0.5 #5b21b6,
                stop:1 #6d28d9
            );
        
            border: 1px solid #a78bfa;
        }
        
        QPushButton#next_btn:disabled {
            background: #1c1d27;
            color: #555b6e;
            border: 1px solid #292c3a;
        }

        QPushButton#back_btn {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1d2e, stop:1 #121422);
            color: #cbd5e1;
            font-size: 13px;
            font-weight: 700;
            font-family: 'Segoe UI';
            border: 1px solid #2a2d3e;
            border-radius: 15px;
            padding: 0px 24px;
            min-height: 40px;
        }
        QPushButton#back_btn:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #262c42, stop:1 #1a1e30);
            color: #f8fafc;
            border: 1px solid #4a4d60;
        }
        QPushButton#back_btn:pressed {
            background: #0f111a;
            border: 1px solid #1e2132;
        }
        QPushButton#back_btn:disabled {
            background: #10121a;
            color: #374151;
            border: 1px solid #1a1d29;
        }
        QPushButton#browse_btn {
            background:#1e2132; color:#94a3b8; font-size:12px; font-weight:600;
            font-family:'Segoe UI'; border:1px solid #2a2d3e; border-radius:10px; padding:0 18px; }
        QPushButton#browse_btn:hover { background:#2a2d3e; color:#e2e8f0; border-color:#6366f1; }
        QPushButton#add_btn {
            background:transparent; color:#6366f1; font-size:12px; font-weight:600;
            font-family:'Segoe UI'; border:1px dashed #3d4070; border-radius:8px; padding:0 10px; }
        QPushButton#add_btn:hover { background:#1e2040; border-color:#6366f1; color:#818cf8; }
        QPushButton#del_btn {
            background:#1e1215; color:#e05252; font-size:11px;
            border:1px solid #3d1f1f; border-radius:7px;
            min-height:20px; max-height:20px; min-width:20px; max-width:20px; }
        QPushButton#del_btn:hover { background:#c0392b; color:#fff; }
        QPushButton#clear_btn {
            background:transparent; color:#64748b; font-size:12px; font-family:'Segoe UI';
            border:1px solid #2a2d3e; border-radius:8px; padding:6px 14px; }
        QPushButton#clear_btn:hover { color:#e2e8f0; background:#2a2d3e; }
        QTextEdit#log_output {
            background:#070a10; border:1px solid #1e2132; border-radius:10px;
            color:#a8b5cc; font-size:12px; font-family:'Consolas','Courier New'; padding:10px; }
        QLabel#log_label { color:#475569; font-size:11px; font-weight:600;
                           font-family:'Segoe UI'; letter-spacing:1.5px; }
        QFrame#port_card { background:#13161f; border:1px solid #22253a; border-radius:12px; }
        QStatusBar { background:#0f1117; color:#475569; font-size:11px;
                     font-family:'Segoe UI'; border-top:1px solid #1e2132; }
        QWidget#welcome_root { background:#0f1117; }
        QPushButton#start_btn {
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366f1,stop:1 #8b5cf6);
            color:#fff; font-size:15px; font-weight:700; font-family:'Segoe UI';
            border:none; border-radius:26px; }
        QPushButton#start_btn:hover {
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #818cf8,stop:1 #a78bfa); }
        """)
        # Append dynamic image paths for QSpinBox arrows (must use absolute paths for EXE portability)
        up_img   = get_image_path("triangle_up.png")
        down_img = get_image_path("triangle_down.png")
        self.setStyleSheet(self.styleSheet() + f"""
        QSpinBox::up-arrow   {{ image: url({up_img});   width:8px; height:8px; }}
        QSpinBox::down-arrow {{ image: url({down_img}); width:8px; height:8px; }}
        """)

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _lbl(text, obj):
        l = QLabel(text); l.setObjectName(obj); return l

    @staticmethod
    def _step_header(step_text, title_text):
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lbl_num = QLabel(step_text)
        lbl_num.setObjectName("step_number")
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("step_title")
        lay.addWidget(lbl_num)
        lay.addWidget(lbl_title)
        return container, lbl_title

    @staticmethod
    def _divider():
        f = QFrame(); f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("color:#2a2d3e;"); return f

    @staticmethod
    def _wrap_port_card(section):
        card = QFrame(); card.setObjectName("port_card")
        lay = QVBoxLayout(card); lay.setContentsMargins(14,14,14,14); lay.setSpacing(8)
        lay.addWidget(section); return card

    # ── Morph animation ─────────────────────────────────────────────────────────
    def _morph_step2(self, forward: bool):
        self._is_morphed = forward
        
        if forward:
            self._rtl_card_w = self.gm_cards.rtl_card.width()
            
            # Align the layout to center at the start so the movement is smooth and doesn't snap!
            self.gm_lay.setAlignment(Qt.AlignCenter)
            self.lang_tree.setVisible(True)
        else:
            if not hasattr(self, '_rtl_card_w'):
                self._rtl_card_w = 400
            
            self.gm_lay.setAlignment(Qt.Alignment(0))
            self.gm_cards.rtl_card.setVisible(True)
        
        anim = QVariantAnimation(self)
        anim.setDuration(450)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setStartValue(0.0 if forward else 1.0)
        anim.setEndValue(1.0 if forward else 0.0)
        
        def update_morph(val):
            inv_val = 1.0 - val
            # shrink rtl card width
            self.gm_cards.rtl_card.setMaximumWidth(int(self._rtl_card_w * inv_val))
            self.gm_cards.rtl_card.setMinimumWidth(0)
            
            # grow lang_tree height (assuming ~150px is enough, say 200 to be safe)
            self.lang_tree.setMaximumHeight(int(200 * val))
            
        anim.valueChanged.connect(update_morph)
        
        def finish_morph():
            if not forward:
                self.lang_tree.setVisible(False)
                self.lang_tree.setMaximumHeight(0)
                self.gm_cards.rtl_card.setMaximumWidth(16777215)
            else:
                self.gm_cards.rtl_card.setVisible(False)
                self.lang_tree.setMaximumHeight(16777215)
                
            self._update_nav()
            
        anim.finished.connect(finish_morph)
        self._lang_anims = [anim]
        anim.start()

    # ── Morph animation (Step 4 – Agents) ────────────────────────────────────
    def _morph_step4(self, forward: bool):
        self._is_agent_morphed = forward

        if forward:
            self._single_card_w = self.agent_cards.single_card.width()
            self.agent_lay.setAlignment(Qt.AlignCenter)
            self.agent_config.setVisible(True)
        else:
            if not hasattr(self, '_single_card_w'):
                self._single_card_w = 400
            self.agent_lay.setAlignment(Qt.Alignment(0))
            self.agent_cards.single_card.setVisible(True)

        anim = QVariantAnimation(self)
        anim.setDuration(450)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setStartValue(0.0 if forward else 1.0)
        anim.setEndValue(1.0 if forward else 0.0)

        def update_morph(val):
            inv_val = 1.0 - val
            self.agent_cards.single_card.setMaximumWidth(int(self._single_card_w * inv_val))
            self.agent_cards.single_card.setMinimumWidth(0)
            self.agent_config.setMaximumHeight(int(200 * val))

        anim.valueChanged.connect(update_morph)

        def finish_morph():
            if not forward:
                self.agent_config.setVisible(False)
                self.agent_config.setMaximumHeight(0)
                self.agent_cards.single_card.setMaximumWidth(16777215)
            else:
                self.agent_cards.single_card.setVisible(False)
                self.agent_config.setMaximumHeight(16777215)
            self._update_nav()

        anim.finished.connect(finish_morph)
        self._agent_anims.append(anim)
        anim.start()

    # ── Morph animation (Step 4 – Interfaces) ────────────────────────────────
    def _morph_step4_interfaces(self, forward: bool):
        """Reveal the multi-agent interface-name inputs with a stable height morph."""
        self._is_agent_interfaces_morphed = forward

        if forward:
            def clear_layout(layout):
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.layout():
                        clear_layout(item.layout())
                        item.layout().deleteLater()

            clear_layout(self.agent_interfaces_lay)
            active_count = self.active_spin.value()
            passive_count = self.passive_spin.value()
            self._active_interface_inputs = []
            self._passive_interface_inputs = []

            input_style = """
                QLineEdit {
                    background:#0d111b; border:1px solid #303b52; border-radius:9px;
                    color:#e2e8f0; font-size:13px; font-family:'Segoe UI'; padding:7px 12px;
                }
                QLineEdit:hover { border-color:#64748b; background:#111827; }
                QLineEdit:focus { border-color:#818cf8; background:#131b2a; }
            """

            active_col = QVBoxLayout()
            active_col.setSpacing(9)
            passive_col = QVBoxLayout()
            passive_col.setSpacing(9)

            def add_section(column, title, subtitle, count, prefix, accent, fields):
                header = QLabel(title)
                header.setAlignment(Qt.AlignCenter)
                header.setStyleSheet(
                    f"font-size:13px; font-weight:800; color:{accent}; "
                    "font-family:'Segoe UI'; letter-spacing:1px;")
                column.addWidget(header)

                note = QLabel(subtitle)
                note.setAlignment(Qt.AlignCenter)
                note.setStyleSheet("font-size:10px; color:#71809a; font-family:'Segoe UI';")
                column.addWidget(note)
                column.addSpacing(4)

                for index in range(count):
                    inp = QLineEdit()
                    inp.setObjectName("port_input")
                    inp.setPlaceholderText(f"{prefix}_agent_{index}_if")
                    inp.setFixedHeight(44)
                    inp.setStyleSheet(input_style)
                    column.addWidget(inp)
                    fields.append(inp)

                column.addStretch(1)

            add_section(
                active_col,
                f"{active_count} ACTIVE AGENT{'S' if active_count != 1 else ''} INTERFACE{'S' if active_count != 1 else ''}",
                "Name the driver and monitor interfaces",
                active_count, "active", "#34d399", self._active_interface_inputs)
            add_section(
                passive_col,
                f"{passive_count} PASSIVE AGENT{'S' if passive_count != 1 else ''} INTERFACE{'S' if passive_count != 1 else ''}",
                "Name the monitor-only interfaces",
                passive_count, "passive", "#c4b5fd", self._passive_interface_inputs)

            self.agent_interfaces_lay.addLayout(active_col)
            self.agent_interfaces_lay.addLayout(passive_col)
            self._agent_cards_h = max(self.agent_cards.height(), 320)
            self.agent_interfaces_scroll.setVisible(True)
            self.agent_interfaces_scroll.setMaximumHeight(0)
        if forward:
            # ── حساب الارتفاع الحالي للـ diagram قبل ما نلمسه ──
            diag = self.agent_cards.multi_card.diagram
            self._diag_h = diag.height() if diag.height() > 0 else 400
            
            # نحسب الارتفاع اللي محتاجينه بالظبط بدل 310 الثابتة
            target_h = self.agent_interfaces_config.sizeHint().height() + 20
            self._scroll_target_h = max(310, target_h)

        else:
            if not hasattr(self, '_agent_cards_h'):
                self._agent_cards_h = 320
            self.agent_cards.setVisible(True)
            self.agent_cards.setMinimumHeight(0)
            self.agent_cards.setMaximumHeight(0)

        anim = QVariantAnimation(self)
        anim.setDuration(350)
        anim.setEasingCurve(QEasingCurve.Linear)
        anim.setStartValue(0.0 if forward else 1.0)
        anim.setEndValue(1.0 if forward else 0.0)

        def update_morph(value):
            progress = float(value)
            # 1. الـ agent_cards بيتقلص تدريجيًا (مع الرسمة جوّاه)
            self.agent_cards.setMaximumHeight(max(0, int(self._agent_cards_h * (1.0 - progress))))
            # 2. الرسمة نفسها بتتقلص بنفس الـ progress عشان متقفلش فجأة
            if forward:
                self.agent_cards.multi_card.diagram.setMaximumHeight(
                    max(0, int(self._diag_h * (1.0 - progress))))
            # 3. الـ scroll area بتكبر تدريجيًا
            target_h = getattr(self, '_scroll_target_h', 310)
            self.agent_interfaces_scroll.setMaximumHeight(max(0, int(target_h * progress)))

        anim.valueChanged.connect(update_morph)

        def finish_morph():
            if forward:
                # self.agent_cards.setVisible(False)  <-- removed to avoid layout spacing jump
                self.agent_cards.multi_card.diagram.setMaximumHeight(16777215)
                self.agent_interfaces_scroll.setMaximumHeight(16777215)
            else:
                # self.agent_interfaces_scroll.setVisible(False) <-- removed
                self.agent_interfaces_scroll.setMaximumHeight(0)
                self.agent_cards.setMaximumHeight(16777215)
                self.agent_cards.multi_card.diagram.setMaximumHeight(16777215)
                self.agent_cards.multi_card.diagram.setMinimumHeight(400)
            self._update_nav()

        anim.finished.connect(finish_morph)
        self._agent_anims = [anim]
        anim.start()

    # ── Slots ──────────────────────────────────────────────────────────────────
    def _on_browse(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.path_input.text() or os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if folder:
            self.path_input.setText(folder.replace("\\", "/"))

    def _on_generate(self):
        name   = self.project_input.text().strip()
        path   = self.path_input.text().strip()
        dut    = self.dut_input.text().strip()
        golden = self.golden_input.text().strip()
        assertions_en = self.assert_toggle.isChecked()
        coverage_en   = self.cover_toggle.isChecked()
        C_coverage_en = self.C_cover_toggle.isChecked()

        iports, oports = self._collect_port_data()
        seqs   = self.seq_section.get_sequences()

        if not name:
            self._log("\u26a0  Enter a project name.\n", "#f59e0b"); return
        if not path or not os.path.isdir(path):
            self._log("\u26a0  Select a valid output directory.\n", "#f59e0b"); return
        if not dut:
            self._log("\u26a0  Enter the DUT module name (Step 4).\n", "#f59e0b"); return
        if not golden and self.golden_model_type == "RTL":
            self._log("\u26a0  Enter the Golden Model module name (Step 4).\n", "#f59e0b"); return
        if not seqs:
            self._log("\u26a0  Add at least one sequence.\n", "#f59e0b"); return

        self.log_output.clear()
        self._log(
            f"\U0001f680  Project   : {name}\n"
            f"    Output         : {path}\n"
            f"    DUT            : {dut}\n"
            f"    Golden         : {golden}\n"
            f"    Assertions     : {'Enabled' if assertions_en else 'Disabled'}\n"
            f"    Code Coverage  : {'Enabled' if C_coverage_en else 'Disabled'}\n"
            f"    Func Coverage  : {'Enabled' if coverage_en else 'Disabled'}\n"


            f"    Inputs    : {len(iports)} port(s)   Outputs: {len(oports)} port(s)\n"
            f"    Sequences : {', '.join(s[0] for s in seqs)}\n",
            "#6366f1", bold=True)

        self.statusBar().showMessage(f"Running tclsh for '{name}' ...")

        # Build per-interface data for GM_SB
        interfaces = []
        if self.golden_model_type == "SB":
            for title, subtitle, in_sec, out_sec, page in self.port_sections:
                kind = "passive" if "PASSIVE" in title.upper() else "active"
                has_clk = page.clock_toggle.isChecked()
                clk_name = page.clock_input.text().strip() if has_clk else ""
                interfaces.append({
                    "name":         title.replace("Active Agent: ", "").replace("Passive Agent: ", "").replace("Single Agent Interface", "agent").strip(),
                    "kind":         kind,
                    "has_clk":      has_clk,
                    "clk_name":     clk_name,
                    "input_ports":  in_sec.get_ports(),   # without clock
                    "output_ports": out_sec.get_ports(),
                })

        self._runner = TclRunner(
            name, path, iports, oports, seqs, dut, golden,
            assertions_en, coverage_en, C_coverage_en,
            gm_type=self.golden_model_type,
            sb_language=self.sb_language,
            ag_mode=self.agent_mode,
            Num_AC_agent=self.num_active_agents,
            Num_PA_agent=self.num_passive_agents,
            interfaces=interfaces,
            rtl_files=getattr(self, 'rtl_source_files', []),
            ref_files=getattr(self, 'ref_source_files', []) if self.golden_model_type == "RTL" else []
        )
        self._runner.output_ready.connect(self._log)
        self._runner.finished_ok.connect(self._on_ok)
        self._runner.finished_err.connect(self._on_err)
        self._runner.start()

    def _on_ok(self):
        self._log("\n✅  Generation completed successfully!\n", "#22c55e", bold=True)
        self.statusBar().showMessage("Done ✓")
        self.big_generate_btn.setEnabled(True)
        
        # --- SUCCESS ANIMATION ---
        if hasattr(self, '_succ_overlay'):
            try: self._succ_overlay.deleteLater()
            except RuntimeError: pass
            
        from ui.widgets import SuccessOverlay
        self._succ_overlay = SuccessOverlay(self.window())
        self._succ_overlay.start()
        
        self.big_generate_btn.setText("GENERATE⚡UVM")
        
        self._morph_anim = QVariantAnimation(self)
        self._morph_anim.setDuration(800)
        # Blue state (GENERATING...) -> Green state (SUCCESS)
        self._morph_anim.setStartValue(0.0)
        self._morph_anim.setEndValue(1.0)
        
        def _update_morph(v):
            p = float(v)
            # Interpolate Blue (#3b82f6) to Green (#10b981)
            r1 = int(59 + (16 - 59) * p)
            g1 = int(130 + (185 - 130) * p)
            b1 = int(246 + (129 - 246) * p)
            
            # Interpolate Blue (#2563eb) to Green (#059669)
            r2 = int(37 + (5 - 37) * p)
            g2 = int(99 + (150 - 99) * p)
            b2 = int(235 + (105 - 235) * p)
            
            # Border: #60a5fa -> #34d399
            br = int(96 + (52 - 96) * p)
            bg = int(165 + (211 - 165) * p)
            bb = int(250 + (153 - 250) * p)
            
            self.big_generate_btn.setStyleSheet(f"""
                QPushButton#big_generate_btn {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb({r1},{g1},{b1}), stop:1 rgb({r2},{g2},{b2}));
                    color: white;
                    font-size: 32px;
                    font-weight: 900;
                    font-family: 'Segoe UI';
                    border-radius: 45px;
                    border: 2px solid rgb({br},{bg},{bb});
                }}
            """)
            
            gr = int(59 + (16 - 59) * p)
            gg = int(130 + (185 - 130) * p)
            gb = int(246 + (129 - 246) * p)
            self.glow_effect.setColor(QColor(gr, gg, gb, 255))
            
        self._morph_anim.valueChanged.connect(_update_morph)
        self._morph_anim.start()
        
        # Start a smooth reversal perfectly timed with the SuccessOverlay glow fading out (at 1000ms)
        def start_reversal():
            self.big_generate_btn.setText("GENERATE⚡UVM")
            self._revert_anim = QVariantAnimation(self)
            self._revert_anim.setDuration(1000)
            self._revert_anim.setStartValue(0.0)
            self._revert_anim.setEndValue(1.0)
            
            def _update_revert(v):
                p = float(v)
                # Green (#10b981) to Purple (#4f46e5)
                r1 = int(16 + (79 - 16) * p)
                g1 = int(185 + (70 - 185) * p)
                b1 = int(129 + (229 - 129) * p)
                
                # Green (#059669) to Purple (#7c3aed)
                r2 = int(5 + (124 - 5) * p)
                g2 = int(150 + (58 - 150) * p)
                b2 = int(105 + (237 - 105) * p)
                
                # Border: #34d399 to #a78bfa
                br = int(52 + (167 - 52) * p)
                bg = int(211 + (139 - 211) * p)
                bb = int(153 + (250 - 153) * p)
                
                self.big_generate_btn.setStyleSheet(f"""
                    QPushButton#big_generate_btn {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb({r1},{g1},{b1}), stop:1 rgb({r2},{g2},{b2}));
                        color: white;
                        font-size: 32px;
                        font-weight: 900;
                        font-family: 'Segoe UI';
                        border-radius: 45px;
                        border: 2px solid rgb({br},{bg},{bb});
                    }}
                """)
                
                # Glow: Green to Purple (#8b5cf6)
                gr = int(16 + (139 - 16) * p)
                gg = int(185 + (92 - 185) * p)
                gb = int(129 + (246 - 129) * p)
                self.glow_effect.setColor(QColor(gr, gg, gb, 255))
            
            self._revert_anim.valueChanged.connect(_update_revert)
            self._revert_anim.finished.connect(self._restore_btn_state)
            self._revert_anim.start()
            
        def trigger_ai_prompt():
            self._show_ai_prompt()
            
        QTimer.singleShot(1500, trigger_ai_prompt)

    def _on_err(self, err_msg: str):
        self._log(f"\n❌  Generation Failed:\n{err_msg}\n", "#ef4444", bold=True)
        self.statusBar().showMessage("Error!")
        self.big_generate_btn.setEnabled(True)

    def _show_ai_prompt(self):
        # 1. Determine phases dynamically based on UI state
        phases = []
        if getattr(self, 'assert_toggle', None) and self.assert_toggle.isChecked():
            phases.append("Assertions")
        if getattr(self, 'cover_toggle', None) and self.cover_toggle.isChecked():
            phases.append("Coverage")
            
        phases.append("Random Constraints")
        
        # Software reference models — show for ALL software languages (SV, C, PY)
        if getattr(self, 'golden_model_type', None) == "SB" and getattr(self, 'sb_language', None):
            phases.append("Reference Model")
            
        if not phases:
            phases = ["AI Assistant"]
            
        from ui.ai_prompt_overlay import AIPromptOverlay
        self._ai_overlay = AIPromptOverlay(self.window(), phases=phases)

        def on_done():
            self._restore_btn_state()

        self._ai_overlay.ai_accepted.connect(on_done)
        self._ai_overlay.ai_declined.connect(on_done)
        
        # Connect generation and skip signals
        self._ai_overlay.generation_requested.connect(self._on_generation_requested)
        self._ai_overlay.skip_requested.connect(self._on_generation_skipped)

    def _on_generation_skipped(self):
        if hasattr(self, '_ai_overlay') and self._ai_overlay:
            self._ai_overlay.advance_phase()

    def _on_generation_requested(self, api_key: str, model_name: str, user_prompt: str):
        """
        Called when the user submits the prompt bar.
        Routes to the real backend for all AI phases.
        """
        import os
        from PyQt5.QtCore import QTimer

        if not hasattr(self, '_ai_overlay') or not self._ai_overlay:
            return

        current_phase = self._ai_overlay.phases[self._ai_overlay.current_phase_idx]
        
        # 1. Map current phase to task category and target directory
        task_category = ""
        target_subpath = ""
        file_suffix = ""
        
        if current_phase == "Assertions":
            task_category = "assertions"
            target_subpath = os.path.join("verif", "assertions")
            file_suffix = ".sv"
        elif current_phase == "Coverage":
            task_category = "coverage"
            target_subpath = os.path.join("verif", "environment")
            file_suffix = "_coverage.sv"
        elif current_phase == "Random Constraints":
            task_category = "random_constraints"
            target_subpath = os.path.join("verif", "agent")
            file_suffix = "_seq_item.sv"
        elif current_phase == "Reference Model":
            lang = getattr(self, 'sb_language', 'SV')
            if lang == "C":
                task_category = "reference_model_c"
                target_subpath = os.path.join("verif", "reference_model", "c")
                file_suffix = "_reference_model.c"
            elif lang == "PY":
                task_category = "reference_model_py"
                target_subpath = os.path.join("verif", "reference_model", "python")
                file_suffix = "_reference_model.py"
            else:  # SV
                task_category = "reference_model_sv"
                target_subpath = os.path.join("verif", "reference_model")
                file_suffix = "_reference_model.sv"
        else:
            # --- Mock generation for any other unimplemented phases ---
            self._ai_overlay.prompt_bar.set_generating(True)
            def mock_finish():
                if hasattr(self, '_ai_overlay') and self._ai_overlay and hasattr(self._ai_overlay, 'prompt_bar'):
                    self._ai_overlay.prompt_bar.set_result(True, f"Generated {current_phase} Successfully!")
                    QTimer.singleShot(2000, self._ai_overlay.advance_phase)
            QTimer.singleShot(1500, mock_finish)
            return

        # ── Locate project output directory ──────────────────────────────────
        output_dir = self.path_input.text().strip()
        import re as _re
        if _re.match(r'^[A-Za-z]:$', output_dir):
            output_dir = output_dir + os.sep
        project_name = self.project_input.text().strip()
        if not output_dir or not project_name:
            self._ai_overlay.prompt_bar.prompt_submitted.disconnect()
            return

        project_path = os.path.join(output_dir, f"{project_name}_uvm")
        if not os.path.isdir(project_path) or not os.path.exists(os.path.join(project_path, "verif")):
            # Fallback 1: search for _uvm in candidates
            candidates = []
            if os.path.isdir(output_dir):
                candidates = [d for d in os.listdir(output_dir) if d.endswith("_uvm") and d.startswith(project_name)]
                candidates.sort(key=lambda d: os.path.getmtime(os.path.join(output_dir, d)), reverse=True)
            if candidates:
                project_path = os.path.join(output_dir, candidates[0])
            else:
                project_path = os.path.join(output_dir, project_name)

        rtl_dir = os.path.join(project_path, "rtl")
        target_dir = os.path.join(project_path, target_subpath)

        # Collect ALL RTL files (.sv / .v) from rtl/
        rtl_files = []
        if os.path.isdir(rtl_dir):
            for fname in sorted(os.listdir(rtl_dir)):
                if fname.endswith((".sv", ".v")):
                    rtl_files.append(os.path.join(rtl_dir, fname))

        if not rtl_files:
            if self.rtl_source_files:
                rtl_files = list(self.rtl_source_files)

        if not rtl_files or not any(os.path.exists(f) for f in rtl_files):
            if hasattr(self._ai_overlay, 'prompt_bar'):
                self._ai_overlay.prompt_bar._editor.setPlainText(
                    "⚠ RTL file not found in project. Generate the project first."
                )
            return

        # Find skeleton file
        skeleton_file = None
        if os.path.isdir(target_dir):
            for fname in os.listdir(target_dir):
                if fname.endswith(file_suffix):
                    # Specifically avoid files that might clash, though suffix should be unique enough
                    if current_phase == "Assertions" and "_assertions" not in fname:
                        pass # Sometimes assertions file doesn't have _assertions if it's the only one, so we accept any .sv
                    skeleton_file = os.path.join(target_dir, fname)
                    break

        if not skeleton_file:
            if hasattr(self._ai_overlay, 'prompt_bar'):
                self._ai_overlay.prompt_bar._editor.setPlainText(
                    f"⚠ {current_phase} skeleton not found in {target_dir} (proj: {project_path}). Generate the project first."
                )
            return

        # ── Show "Generating..." state on the prompt bar ──────────────────────
        if hasattr(self._ai_overlay, 'prompt_bar'):
            self._ai_overlay.prompt_bar.set_generating(True)

        # ── Build extra context and style doc for Reference Model ─────────────
        extra_context_files = []
        ref_doc_file = None
        if current_phase == "Reference Model":
            lang = getattr(self, 'sb_language', 'SV')
            import pathlib
            backend_ai_dir = pathlib.Path(BACKEND_AI_DIR)
            if lang == "C":
                ref_doc_file = str(backend_ai_dir / "doc" / "c" / "Wide_ALU_C_reference_model.c")
                # Add the .h header if it exists
                h_file = os.path.join(project_path, "verif", "reference_model", "c",
                                      f"{project_name}_reference_model.h")
                if os.path.exists(h_file):
                    extra_context_files.append(h_file)
            elif lang == "PY":
                ref_doc_file = str(backend_ai_dir / "doc" / "py" / "Wide_ALU_py_reference_model.py")
            else:  # SV
                ref_doc_file = str(backend_ai_dir / "doc" / "sv" / "Wide_ALU_systemverilog_reference_model.sv")

        # ── Run generation in a background thread ─────────────────────────────
        self._gen_worker = _AIGenerationWorker(
            task_category=task_category,
            model_name=model_name,
            api_key=api_key,
            rtl_files=rtl_files,
            skeleton_path=skeleton_file,
            user_prompt=user_prompt,
            extra_context_files=extra_context_files,
            ref_doc_file=ref_doc_file,
        )
        self._gen_worker.finished.connect(
            lambda ok, result: self._on_generation_done(ok, result, skeleton_file)
        )
        self._gen_worker.start()

    def _on_generation_done(self, success: bool, result: str, skeleton_path: str):
        """Called when background generation finishes."""
        prompt_bar = getattr(getattr(self, '_ai_overlay', None), 'prompt_bar', None)

        if success:
            try:
                with open(skeleton_path, "w", encoding="utf-8") as f:
                    f.write(result)
                if prompt_bar:
                    prompt_bar.set_result(True, f"Generated file saved to:\n{skeleton_path}")
                    
                if hasattr(self, '_ai_overlay') and self._ai_overlay:
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(2500, self._ai_overlay.advance_phase)
            except Exception as e:
                if prompt_bar:
                    prompt_bar.set_result(False, f"Generated but failed to save: {e}")
        else:
            if prompt_bar:
                prompt_bar.set_result(False, f"Error:\n{result}")

    def _log(self, text, color="#FFFFFF", bold=False):
        """Helper to append HTML lines to log_output."""
        from PyQt5.QtGui import QTextCursor
        if not hasattr(self, 'log_output'):
            return
        cur = self.log_output.textCursor()
        cur.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cur)
        safe = (text.replace("&","&amp;").replace("<","&lt;")
                    .replace(">","&gt;").replace("\n","<br>"))
        w = "font-weight:700;" if bold else ""
        self.log_output.insertHtml(f'<span style="color:{color};{w}">{safe}</span>')
        self.log_output.ensureCursorVisible()

    def closeEvent(self, event):
        super().closeEvent(event)


class _AIGenerationWorker(object):
    """
    Background thread for AI generation.
    Uses QThread to avoid blocking the UI during LLM calls.
    """
    def __new__(cls, task_category, model_name, api_key, rtl_files, skeleton_path, user_prompt,
                extra_context_files=None, ref_doc_file=None):
        from PyQt5.QtCore import QThread, pyqtSignal as Signal

        class _Worker(QThread):
            finished = Signal(bool, str)

            def __init__(self, task_category, model_name, api_key, rtl_files, skeleton_path, user_prompt,
                         extra_context_files, ref_doc_file):
                super().__init__()
                self.task_category = task_category
                self.model_name = model_name
                self.api_key = api_key
                self.rtl_files = rtl_files if isinstance(rtl_files, list) else [rtl_files]
                self.skeleton_path = skeleton_path
                self.user_prompt = user_prompt
                self.extra_context_files = extra_context_files or []
                self.ref_doc_file = ref_doc_file

            def run(self):
                import sys, os
                from core.config import BACKEND_AI_DIR
                if BACKEND_AI_DIR not in sys.path:
                    sys.path.insert(0, BACKEND_AI_DIR)
                # Also ensure the Backend package root is importable
                backend_root = os.path.dirname(BACKEND_AI_DIR)
                if backend_root not in sys.path:
                    sys.path.insert(0, backend_root)
                try:
                    from Backend.Backend_AI.llm_client import generate_ai_artifact
                    project_files = self.rtl_files + self.extra_context_files
                    result = generate_ai_artifact(
                        task_category=self.task_category,
                        model_name=self.model_name,
                        api_key=self.api_key,
                        project_files=project_files,
                        skeleton_path=self.skeleton_path,
                        user_prompt=self.user_prompt,
                        ref_doc_file=self.ref_doc_file,
                    )
                    self.finished.emit(True, result)
                except Exception as e:
                    self.finished.emit(False, str(e))

        return _Worker(task_category, model_name, api_key, rtl_files, skeleton_path, user_prompt,
                       extra_context_files, ref_doc_file)


