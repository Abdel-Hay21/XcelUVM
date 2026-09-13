import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from PyQt5.QtGui import QPalette, QColor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = QPalette()
    for role, col in [
        (QPalette.Window,          "#0f1117"),
        (QPalette.WindowText,      "#e2e8f0"),
        (QPalette.Base,            "#070a10"),
        (QPalette.AlternateBase,   "#1a1d27"),
        (QPalette.Text,            "#e2e8f0"),
        (QPalette.Button,          "#1a1d27"),
        (QPalette.ButtonText,      "#e2e8f0"),
        (QPalette.Highlight,       "#6366f1"),
        (QPalette.HighlightedText, "#ffffff"),
    ]:
        pal.setColor(role, QColor(col))
    app.setPalette(pal)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
