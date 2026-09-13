from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from core.config import get_image_path


class PortRow(QWidget):
    deleted = pyqtSignal(object)

    def __init__(self, name="", bits=1, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.name_edit = QLineEdit(name)
        self.name_edit.setObjectName("port_input")
        self.name_edit.setPlaceholderText("port name")
        self.name_edit.setFixedHeight(20)
        lay.addWidget(self.name_edit, stretch=1)

        self.bits_spin = QSpinBox()
        self.bits_spin.setObjectName("bits_spin")
        self.bits_spin.setRange(1, 1024)
        self.bits_spin.setValue(bits)
        self.bits_spin.setFixedSize(64, 20)
        lay.addWidget(self.bits_spin)

        lbl = QLabel("bit")
        lbl.setObjectName("bit_lbl")
        lay.addWidget(lbl)

        btn = QPushButton("✕")
        btn.setObjectName("del_btn")
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.deleted.emit(self))
        lay.addWidget(btn)

    def get_port(self):
        return self.name_edit.text().strip(), self.bits_spin.value()

    def set_enabled_all(self, v):
        self.name_edit.setEnabled(v)
        self.bits_spin.setEnabled(v)


class PortSection(QWidget):
    def __init__(self, title, defaults=None, parent=None):
        super().__init__(parent)
        self._rows = []
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(4)

        lbl = QLabel(title)
        lbl.setObjectName("field_label")
        main.addWidget(lbl)

        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(4)
        main.addWidget(self.rows_widget)

        main.addStretch(1)

        add_btn = QPushButton("＋  Add Port")
        add_btn.setObjectName("add_btn")
        add_btn.setFixedHeight(32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_row())
        main.addWidget(add_btn)

        for name, bits in (defaults or []):
            self.add_row(name, bits)

    def add_row(self, name="", bits=1):
        row = PortRow(name, bits)
        row.deleted.connect(self._del_row)
        self._rows.append(row)
        self.rows_layout.addWidget(row)

    def _del_row(self, row):
        self._rows.remove(row)
        self.rows_layout.removeWidget(row)
        row.deleteLater()

    def get_ports(self):
        return [r.get_port() for r in self._rows if r.get_port()[0]]

    def set_enabled_all(self, v):
        for r in self._rows:
            r.set_enabled_all(v)


# ─────────────────────────────────────────────────────────────────────────────
# Sequence row with up/down arrow buttons for reordering
# ─────────────────────────────────────────────────────────────────────────────
class SeqRow(QWidget):
    deleted    = pyqtSignal(object)
    move_up    = pyqtSignal(object)
    move_down  = pyqtSignal(object)

    _UP_ICON   = get_image_path("triangle_up.png")
    _DOWN_ICON = get_image_path("triangle_down.png")

    # Shared stylesheet for the arrow buttons
    _ARROW_SS = (
        "QPushButton {{ background: #1a1d27; border: 1px solid #2a2d3e;"
        " border-radius: 5px; padding: 0; }}"
        "QPushButton:hover {{ background: #2a2d3e; border-color: #6366f1; }}"
        "QPushButton:pressed {{ background: #6366f1; }}"
    )

    def __init__(self, name="", iterations=1, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # ── Up / Down arrow buttons (stacked vertically) ──────────────────────
        arrows_col = QVBoxLayout()
        arrows_col.setContentsMargins(0, 0, 0, 0)
        arrows_col.setSpacing(2)

        self.up_btn = QPushButton()
        self.up_btn.setFixedSize(22, 14)
        self.up_btn.setCursor(Qt.PointingHandCursor)
        self.up_btn.setToolTip("Move up")
        self.up_btn.setStyleSheet(
            f"QPushButton {{ background: #1a1d27; border: 1px solid #2a2d3e;"
            f" border-radius: 4px; padding: 0;"
            f" image: url({self._UP_ICON}); }}"
            f"QPushButton:hover {{ background: #2a2d3e; border-color: #6366f1; }}"
            f"QPushButton:pressed {{ background: #6366f1; }}"
        )
        self.up_btn.clicked.connect(lambda: self.move_up.emit(self))

        self.down_btn = QPushButton()
        self.down_btn.setFixedSize(22, 14)
        self.down_btn.setCursor(Qt.PointingHandCursor)
        self.down_btn.setToolTip("Move down")
        self.down_btn.setStyleSheet(
            f"QPushButton {{ background: #1a1d27; border: 1px solid #2a2d3e;"
            f" border-radius: 4px; padding: 0;"
            f" image: url({self._DOWN_ICON}); }}"
            f"QPushButton:hover {{ background: #2a2d3e; border-color: #6366f1; }}"
            f"QPushButton:pressed {{ background: #6366f1; }}"
        )
        self.down_btn.clicked.connect(lambda: self.move_down.emit(self))

        arrows_col.addWidget(self.up_btn)
        arrows_col.addWidget(self.down_btn)
        lay.addLayout(arrows_col)

        # ── Name field ────────────────────────────────────────────────────────
        self.name_edit = QLineEdit(name)
        self.name_edit.setObjectName("port_input")
        self.name_edit.setPlaceholderText("Sequence name  (e.g. Reset)")
        self.name_edit.setFixedHeight(32)

        def _replace_spaces(text):
            if ' ' in text:
                fixed = text.replace(' ', '_')
                pos = self.name_edit.cursorPosition()
                spaces_before = text[:pos].count(' ')
                self.name_edit.blockSignals(True)
                self.name_edit.setText(fixed)
                self.name_edit.setCursorPosition(pos + spaces_before)
                self.name_edit.blockSignals(False)

        self.name_edit.textEdited.connect(_replace_spaces)
        lay.addWidget(self.name_edit, stretch=1)

        # ── Iterations field ──────────────────────────────────────────────────
        self.iter_edit = QLineEdit(f"{iterations:,}")
        self.iter_edit.setObjectName("bits_spin")
        self.iter_edit.setFixedSize(300, 32)

        def format_edit(text):
            tc = text.replace(',', '')
            if tc.isdigit():
                formatted = f"{int(tc):,}"
                self.iter_edit.blockSignals(True)
                self.iter_edit.setText(formatted)
                self.iter_edit.blockSignals(False)
                self.iter_edit.setCursorPosition(len(formatted))
            elif tc == "":
                self.iter_edit.blockSignals(True)
                self.iter_edit.setText("")
                self.iter_edit.blockSignals(False)

        self.iter_edit.textEdited.connect(format_edit)
        lay.addWidget(self.iter_edit)

        lbl = QLabel("iters")
        lbl.setObjectName("bit_lbl")
        lay.addWidget(lbl)

        # ── Delete button ─────────────────────────────────────────────────────
        del_btn = QPushButton("✕")
        del_btn.setObjectName("del_btn")
        del_btn.setFixedSize(32, 32)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.deleted.emit(self))
        lay.addWidget(del_btn)

    def get_sequence(self):
        val_str = self.iter_edit.text().replace(',', '')
        val = int(val_str) if val_str.isdigit() else 1
        return self.name_edit.text().strip(), val

    def set_enabled_all(self, v):
        self.name_edit.setEnabled(v)
        self.iter_edit.setEnabled(v)


class SeqSection(QWidget):
    def __init__(self, defaults=None, parent=None):
        super().__init__(parent)
        self._rows = []
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(4)

        # ── Header row ────────────────────────────────────────────────────────
        header_lay = QHBoxLayout()
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(8)

        # Spacer matching the arrows column width (22 px + 6 px spacing)
        dummy_arrows = QWidget()
        dummy_arrows.setFixedWidth(28)
        header_lay.addWidget(dummy_arrows)

        lbl_seq = QLabel("SEQUENCES (Ordered)")
        lbl_seq.setObjectName("seq_header_label")
        header_lay.addWidget(lbl_seq, stretch=1)

        lbl_iter = QLabel("Num of ITERATIONS")
        lbl_iter.setObjectName("seq_header_label")
        lbl_iter.setFixedWidth(300)
        lbl_iter.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_lay.addWidget(lbl_iter)

        dummy_iters = QLabel("iters")
        dummy_iters.setObjectName("bit_lbl")
        dummy_iters.setStyleSheet("color: transparent;")
        header_lay.addWidget(dummy_iters)

        dummy_btn = QWidget()
        dummy_btn.setFixedSize(32, 32)
        header_lay.addWidget(dummy_btn)

        main.addLayout(header_lay)

        # ── Rows container ────────────────────────────────────────────────────
        self.rows_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(4)
        main.addWidget(self.rows_widget)

        # ── Add button ────────────────────────────────────────────────────────
        add_btn = QPushButton("＋  Add Sequence")
        add_btn.setObjectName("add_btn")
        add_btn.setFixedHeight(32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_row())
        main.addWidget(add_btn)

        for item in (defaults or []):
            if isinstance(item, (tuple, list)):
                self.add_row(item[0], item[1])
            else:
                self.add_row(item)

    # ── Public API ────────────────────────────────────────────────────────────
    def add_row(self, name="", iterations=1):
        row = SeqRow(name, iterations)
        row.deleted.connect(self._del_row)
        row.move_up.connect(self._move_up)
        row.move_down.connect(self._move_down)
        self._rows.append(row)
        self.rows_layout.addWidget(row)
        self._refresh_arrows()

    def get_sequences(self):
        return [r.get_sequence() for r in self._rows if r.get_sequence()[0]]

    def set_enabled_all(self, v):
        for r in self._rows:
            r.set_enabled_all(v)

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _del_row(self, row):
        self._rows.remove(row)
        self.rows_layout.removeWidget(row)
        row.deleteLater()
        self._refresh_arrows()

    def _move_up(self, row):
        idx = self._rows.index(row)
        if idx == 0:
            return
        # Swap in list
        self._rows[idx], self._rows[idx - 1] = self._rows[idx - 1], self._rows[idx]
        # Swap in layout: remove both then re-insert in new order
        self.rows_layout.removeWidget(self._rows[idx])      # was idx-1, now idx
        self.rows_layout.removeWidget(self._rows[idx - 1])  # was idx,   now idx-1
        self.rows_layout.insertWidget(idx - 1, self._rows[idx - 1])
        self.rows_layout.insertWidget(idx,     self._rows[idx])
        self._refresh_arrows()

    def _move_down(self, row):
        idx = self._rows.index(row)
        if idx == len(self._rows) - 1:
            return
        # Swap in list
        self._rows[idx], self._rows[idx + 1] = self._rows[idx + 1], self._rows[idx]
        # Swap in layout
        self.rows_layout.removeWidget(self._rows[idx])      # was idx+1, now idx
        self.rows_layout.removeWidget(self._rows[idx + 1])  # was idx,   now idx+1
        self.rows_layout.insertWidget(idx,     self._rows[idx])
        self.rows_layout.insertWidget(idx + 1, self._rows[idx + 1])
        self._refresh_arrows()

    def _refresh_arrows(self):
        """Disable up arrow on first row, down arrow on last row."""
        for i, row in enumerate(self._rows):
            row.up_btn.setEnabled(i > 0)
            row.down_btn.setEnabled(i < len(self._rows) - 1)
            # Dim disabled arrows visually
            dim = "opacity: 0.3;" if not row.up_btn.isEnabled() else ""
            row.up_btn.setStyleSheet(
                f"QPushButton {{ background: #1a1d27; border: 1px solid #2a2d3e;"
                f" border-radius: 4px; padding: 0;"
                f" image: url({SeqRow._UP_ICON}); {dim} }}"
                f"QPushButton:hover {{ background: #2a2d3e; border-color: #6366f1; }}"
                f"QPushButton:pressed {{ background: #6366f1; }}"
            )
            dim2 = "opacity: 0.3;" if not row.down_btn.isEnabled() else ""
            row.down_btn.setStyleSheet(
                f"QPushButton {{ background: #1a1d27; border: 1px solid #2a2d3e;"
                f" border-radius: 4px; padding: 0;"
                f" image: url({SeqRow._DOWN_ICON}); {dim2} }}"
                f"QPushButton:hover {{ background: #2a2d3e; border-color: #6366f1; }}"
                f"QPushButton:pressed {{ background: #6366f1; }}"
            )
