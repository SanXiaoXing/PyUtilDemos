from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter


class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self._tag = QTextCharFormat()
        self._tag.setForeground(QColor("#a5b4fc"))
        self._tag.setFontWeight(QFont.DemiBold)

        self._attr_name = QTextCharFormat()
        self._attr_name.setForeground(QColor("#fbbf24"))

        self._attr_value = QTextCharFormat()
        self._attr_value.setForeground(QColor("#34d399"))

        self._punct = QTextCharFormat()
        self._punct.setForeground(QColor("#93a5d8"))

        self._rules = [
            (QRegExp(r"</?[\w:\-\.]+"), self._tag),
            (QRegExp(r"[\w:\-\.]+(?=\=)"), self._attr_name),
            (QRegExp(r"\"[^\"]*\""), self._attr_value),
            (QRegExp(r"[<>/=]"), self._punct),
        ]

    def highlightBlock(self, text: str) -> None:
        for rx, fmt in self._rules:
            i = rx.indexIn(text, 0)
            while i >= 0:
                length = rx.matchedLength()
                if length > 0:
                    self.setFormat(i, length, fmt)
                i = rx.indexIn(text, i + max(1, length))

