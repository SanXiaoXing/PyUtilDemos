import sys

from PyQt5.QtWidgets import QApplication

from src.components.XmlEditorPro.widget import XmlEditorProWidget


def main() -> None:
    app = QApplication(sys.argv)
    w = XmlEditorProWidget()
    w.resize(1400, 860)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

