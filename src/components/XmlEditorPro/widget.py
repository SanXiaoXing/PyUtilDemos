import xml.etree.ElementTree as ET
from typing import List, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
)

from .styles import QSS
from .toast import ToastManager
from .xml_highlighter import XmlHighlighter
from .xml_model import clone_element, element_text_preview, format_xml, parse_xml_text


class AddNodeDialog(QDialog):
    def __init__(self, title: str, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        name_label = QLabel("节点名称")
        name_label.setObjectName("PanelTitle")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入节点名称")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        text_label = QLabel("文本内容（可选）")
        text_label.setObjectName("PanelTitle")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入文本内容")
        layout.addWidget(text_label)
        layout.addWidget(self.text_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return self.name_input.text().strip(), self.text_input.text()


class ImportXmlDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("导入 XML")
        self.setModal(True)
        self.resize(760, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        tip = QLabel("粘贴 XML 内容")
        tip.setObjectName("PanelTitle")
        layout.addWidget(tip)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("请粘贴 XML 内容…")
        font = QFont("SF Mono")
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        layout.addWidget(self.editor, 1)

        buttons_row = QHBoxLayout()
        self.open_file_btn = QPushButton("从文件导入")
        buttons_row.addWidget(self.open_file_btn)
        buttons_row.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("导入")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons_row.addWidget(buttons)
        layout.addLayout(buttons_row)

        self.open_file_btn.clicked.connect(self._open_file)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 XML 文件", "", "XML (*.xml);;All Files (*)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.editor.setPlainText(f.read())

    def xml_text(self) -> str:
        return self.editor.toPlainText()


class AttributesTable(QTableWidget):
    def __init__(self, parent: QWidget):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["属性名", "属性值"])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setAlternatingRowColors(False)
        self._block = False
        self.itemChanged.connect(self._on_item_changed)
        self._on_change = None

    def set_on_change(self, fn):
        self._on_change = fn

    def set_attributes(self, attrs: dict) -> None:
        self._block = True
        self.setRowCount(0)
        for k, v in (attrs or {}).items():
            r = self.rowCount()
            self.insertRow(r)
            self.setItem(r, 0, QTableWidgetItem(str(k)))
            self.setItem(r, 1, QTableWidgetItem(str(v)))
        self._block = False

    def attributes(self) -> dict:
        out = {}
        for r in range(self.rowCount()):
            k_item = self.item(r, 0)
            v_item = self.item(r, 1)
            k = (k_item.text() if k_item else "").strip()
            v = v_item.text() if v_item else ""
            if k:
                out[k] = v
        return out

    def add_row(self) -> None:
        self._block = True
        r = self.rowCount()
        self.insertRow(r)
        self.setItem(r, 0, QTableWidgetItem(""))
        self.setItem(r, 1, QTableWidgetItem(""))
        self._block = False
        self.setCurrentCell(r, 0)
        self.editItem(self.item(r, 0))
        if self._on_change:
            self._on_change()

    def remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self.selectedIndexes()}, reverse=True)
        if not rows:
            return
        self._block = True
        for r in rows:
            self.removeRow(r)
        self._block = False
        if self._on_change:
            self._on_change()

    def _on_item_changed(self) -> None:
        if self._block:
            return
        if self._on_change:
            self._on_change()

def _iter_children(element: ET.Element) -> List[ET.Element]:
    return list(element)


def _contains(ancestor: ET.Element, maybe_desc: ET.Element) -> bool:
    for child in _iter_children(ancestor):
        if child is maybe_desc:
            return True
        if _contains(child, maybe_desc):
            return True
    return False


def _find_parent(target: ET.Element, roots: List[ET.Element]) -> Optional[ET.Element]:
    for root in roots:
        if root is target:
            return None
        for parent in root.iter():
            for child in list(parent):
                if child is target:
                    return parent
    return None


class XmlTreeWidgetPro(QTreeWidget):
    def __init__(self, parent: QWidget, toast: ToastManager, get_roots, set_roots, on_select, on_moved):
        super().__init__(parent)
        self._toast = toast
        self._get_roots = get_roots
        self._set_roots = set_roots
        self._on_select = on_select
        self._on_moved = on_moved
        self._dragged_element = None

        self.setHeaderHidden(True)
        self.setIndentation(18)
        self.setAnimated(True)
        self.setIconSize(QSize(22, 22))
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.SingleSelection)
        self.itemSelectionChanged.connect(self._selection_changed)

    def startDrag(self, supportedActions):
        items = self.selectedItems()
        if items:
            self._dragged_element = items[0].data(0, Qt.UserRole)
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        target_item = self.itemAt(event.pos())
        if not target_item or self._dragged_element is None:
            super().dropEvent(event)
            return

        target_element = target_item.data(0, Qt.UserRole)
        dragged = self._dragged_element
        self._dragged_element = None

        if dragged is None or target_element is None:
            event.ignore()
            return
        if dragged is target_element:
            event.ignore()
            return

        roots = self._get_roots()
        if _contains(dragged, target_element):
            self._toast.show("不能将节点移动到其子节点下", "error")
            event.ignore()
            return

        parent = _find_parent(dragged, roots)
        if parent is None:
            roots = [r for r in roots if r is not dragged]
        else:
            parent.remove(dragged)

        target_element.append(dragged)
        self._set_roots(roots)
        event.accept()
        self._toast.show("节点移动成功", "success")
        self._on_moved(dragged)

    def _selection_changed(self):
        items = self.selectedItems()
        element = items[0].data(0, Qt.UserRole) if items else None
        self._on_select(element)


class XmlEditorProWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XML 编辑器")
        self._roots: List[ET.Element] = []
        self._selected: Optional[ET.Element] = None
        self._clipboard_node: Optional[ET.Element] = None
        self._signals_blocked = False

        self._toast = ToastManager(self)
        self._build_ui()
        self._apply_style()
        self._wire_shortcuts()
        self._refresh_all()

    def _apply_style(self) -> None:
        self.setStyleSheet(QSS)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._toast.on_parent_resized()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(74)
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(18, 14, 18, 14)
        header_l.setSpacing(12)

        logo_icon = QLabel("XML")
        logo_icon.setObjectName("LogoIcon")
        header_l.addWidget(logo_icon, 0, Qt.AlignVCenter)

        logo_text = QLabel("编辑器")
        logo_text.setObjectName("LogoText")
        header_l.addWidget(logo_text, 0, Qt.AlignVCenter)

        header_l.addStretch(1)

        self.btn_import = QPushButton("导入")
        self.btn_import.clicked.connect(self._import_xml)
        header_l.addWidget(self.btn_import)

        self.btn_download = QPushButton("下载")
        self.btn_download.setObjectName("SuccessButton")
        self.btn_download.clicked.connect(self._save_xml)
        header_l.addWidget(self.btn_download)

        self.btn_copy = QPushButton("复制XML")
        self.btn_copy.setObjectName("PrimaryButton")
        self.btn_copy.clicked.connect(self._copy_xml)
        header_l.addWidget(self.btn_copy)

        root.addWidget(header)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        root.addWidget(self.splitter, 1)

        self.panel_tree = self._make_panel("节点树", right=False)
        self.splitter.addWidget(self.panel_tree)

        self.panel_editor = self._make_panel("", right=False, header=False)
        self.splitter.addWidget(self.panel_editor)

        self.panel_output = self._make_panel("XML 输出", right=True)
        self.splitter.addWidget(self.panel_output)

        self.splitter.setSizes([320, 640, 420])

        self._build_tree_panel()
        self._build_editor_panel()
        self._build_output_panel()

    def _make_panel(self, title: str, right: bool, header: bool = True) -> QFrame:
        panel = QFrame()
        panel.setObjectName("PanelRight" if right else "Panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        if header:
            header_bar = QFrame()
            header_bar.setObjectName("PanelHeader")
            header_l = QHBoxLayout(header_bar)
            header_l.setContentsMargins(16, 12, 16, 12)
            header_l.setSpacing(10)
            t = QLabel(title)
            t.setObjectName("PanelTitle")
            header_l.addWidget(t)
            header_l.addStretch(1)
            lay.addWidget(header_bar)
            panel._header_bar = header_bar
            panel._header_layout = header_l
        content = QWidget()
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(12, 12, 12, 12)
        content_l.setSpacing(12)
        lay.addWidget(content, 1)
        panel._content = content
        panel._content_layout = content_l
        return panel

    def _build_tree_panel(self) -> None:
        hl = self.panel_tree._header_layout
        self.btn_add_root = QPushButton("添加根节点")
        self.btn_add_root.setObjectName("PrimaryButton")
        self.btn_add_root.clicked.connect(self._add_root)
        hl.addWidget(self.btn_add_root)

        content = self.panel_tree._content_layout
        self.empty_tree = self._make_empty("🌳", "暂无节点", "点击上方按钮添加根节点")
        content.addWidget(self.empty_tree, 1)
        self.tree = XmlTreeWidgetPro(
            self.panel_tree._content,
            toast=self._toast,
            get_roots=lambda: self._roots,
            set_roots=self._set_roots,
            on_select=self._select_element,
            on_moved=self._after_structure_change,
        )
        content.addWidget(self.tree, 1)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_menu)

    def _build_editor_panel(self) -> None:
        content = self.panel_editor._content_layout
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)

        self.props_page = QWidget()
        self.preview_page = QWidget()

        self.tabs.addTab(self.props_page, "属性编辑")
        self.tabs.addTab(self.preview_page, "XML预览")
        content.addWidget(self.tabs, 1)

        self._build_properties_page()
        self._build_preview_page()

    def _build_properties_page(self) -> None:
        lay = QVBoxLayout(self.props_page)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(12)

        self.empty_props = self._make_empty("📝", "选择节点开始编辑", "从左侧节点树中选择一个节点进行编辑")
        lay.addWidget(self.empty_props, 1)

        self.props = QWidget()
        form = QVBoxLayout(self.props)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        name_label = QLabel("节点名称")
        name_label.setObjectName("PanelTitle")
        self.edit_name = QLineEdit()
        self.edit_name.textEdited.connect(self._on_name_changed)
        form.addWidget(name_label)
        form.addWidget(self.edit_name)

        text_label = QLabel("文本内容")
        text_label.setObjectName("PanelTitle")
        self.edit_text = QPlainTextEdit()
        self.edit_text.textChanged.connect(self._on_text_changed)
        form.addWidget(text_label)
        form.addWidget(self.edit_text, 1)

        attrs_header = QHBoxLayout()
        attrs_label = QLabel("属性列表")
        attrs_label.setObjectName("PanelTitle")
        attrs_header.addWidget(attrs_label)
        attrs_header.addStretch(1)
        self.btn_add_attr = QPushButton("添加属性")
        self.btn_add_attr.clicked.connect(lambda: self.attrs.add_row())
        attrs_header.addWidget(self.btn_add_attr)
        self.btn_remove_attr = QPushButton("删除属性")
        self.btn_remove_attr.clicked.connect(lambda: self.attrs.remove_selected())
        attrs_header.addWidget(self.btn_remove_attr)
        form.addLayout(attrs_header)

        self.attrs = AttributesTable(self.props)
        self.attrs.set_on_change(self._on_attrs_changed)
        form.addWidget(self.attrs, 1)

        actions = QHBoxLayout()
        self.btn_add_child = QPushButton("添加子节点")
        self.btn_add_child.clicked.connect(self._add_child)
        actions.addWidget(self.btn_add_child)

        self.btn_copy_node = QPushButton("复制节点")
        self.btn_copy_node.clicked.connect(self._copy_node)
        actions.addWidget(self.btn_copy_node)

        self.btn_dup_node = QPushButton("复制到同级")
        self.btn_dup_node.clicked.connect(self._duplicate_node)
        actions.addWidget(self.btn_dup_node)

        self.btn_del_node = QPushButton("删除节点")
        self.btn_del_node.setObjectName("DangerButton")
        self.btn_del_node.clicked.connect(self._delete_node)
        actions.addWidget(self.btn_del_node)

        form.addLayout(actions)

        lay.addWidget(self.props, 2)
        self.props.hide()

    def _build_preview_page(self) -> None:
        lay = QVBoxLayout(self.preview_page)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(10)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("暂无内容")
        font = QFont("SF Mono")
        font.setStyleHint(QFont.Monospace)
        self.preview.setFont(font)
        XmlHighlighter(self.preview.document())
        lay.addWidget(self.preview, 1)

    def _build_output_panel(self) -> None:
        hl = self.panel_output._header_layout
        self.btn_format = QPushButton("格式化")
        self.btn_format.clicked.connect(self._refresh_xml_views)
        hl.addWidget(self.btn_format)

        content = self.panel_output._content_layout
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("暂无内容")
        font = QFont("SF Mono")
        font.setStyleHint(QFont.Monospace)
        self.output.setFont(font)
        XmlHighlighter(self.output.document())
        content.addWidget(self.output, 1)

    def _make_empty(self, icon: str, title: str, text: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)
        lay.addStretch(1)
        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignHCenter)
        ic.setStyleSheet("font-size: 42px; color: #8e8e93;")
        lay.addWidget(ic)
        tt = QLabel(title)
        tt.setAlignment(Qt.AlignHCenter)
        tt.setStyleSheet("font-size: 16px; font-weight: 800; color: #1d1d1f;")
        lay.addWidget(tt)
        tx = QLabel(text)
        tx.setWordWrap(True)
        tx.setAlignment(Qt.AlignHCenter)
        tx.setStyleSheet("color: #6e6e73;")
        lay.addWidget(tx)
        lay.addStretch(2)
        return w

    def _make_node_icon(self, ch: str) -> QIcon:
        size = 22
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)

        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QColor("#0a84ff"))
        grad.setColorAt(1.0, QColor("#64d2ff"))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, size, size, 7, 7)

        p.setPen(QColor("#ffffff"))
        f = QFont(self.font().family(), 9, QFont.Bold)
        p.setFont(f)
        p.drawText(pm.rect(), Qt.AlignCenter, (ch or "?")[:1].upper())
        p.end()
        return QIcon(pm)

    def _wire_shortcuts(self) -> None:
        QShortcut(QKeySequence("Esc"), self, activated=self._close_overlays)
        QShortcut(QKeySequence.Copy, self, activated=self._copy_node)
        QShortcut(QKeySequence.Paste, self, activated=self._paste_node)
        QShortcut(QKeySequence.Delete, self, activated=self._delete_node)

    def _close_overlays(self) -> None:
        self.tree.clearSelection()

    def _set_roots(self, roots: List[ET.Element]) -> None:
        self._roots = roots

    def _refresh_all(self) -> None:
        self.rebuild_tree(select=None)
        self._refresh_xml_views()
        self._sync_properties()

    def _after_structure_change(self, select: Optional[ET.Element]) -> None:
        self.rebuild_tree(select=select)
        self._refresh_xml_views()

    def rebuild_tree(self, select: Optional[ET.Element]) -> None:
        if not self._roots:
            self.tree.hide()
            self.empty_tree.show()
        else:
            self.empty_tree.hide()
            self.tree.show()

        self.tree.blockSignals(True)
        self.tree.clear()

        def add_item(parent_item: Optional[QTreeWidgetItem], el: ET.Element):
            text_preview = element_text_preview(el)
            attrs_preview = str(len(el.attrib)) if el.attrib else ""
            label = el.tag or ""
            item = QTreeWidgetItem([label])
            item.setIcon(0, self._make_node_icon(label[:1] if label else "?"))
            item.setData(0, Qt.UserRole, el)
            item.setToolTip(0, f"{label}{('  ' + text_preview) if text_preview else ''}{('  @' + attrs_preview) if attrs_preview else ''}")
            if parent_item is None:
                self.tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            for child in list(el):
                add_item(item, child)
            return item

        wanted_item = None
        for root_el in self._roots:
            top = add_item(None, root_el)
            if select is not None and root_el is select:
                wanted_item = top

        if select is not None and wanted_item is None:
            it = self._find_item_for_element(select)
            wanted_item = it

        self.tree.expandAll()
        if wanted_item is not None:
            self.tree.setCurrentItem(wanted_item)
        self.tree.blockSignals(False)

    def _find_item_for_element(self, element: ET.Element) -> Optional[QTreeWidgetItem]:
        def walk(item: QTreeWidgetItem):
            if item.data(0, Qt.UserRole) is element:
                return item
            for i in range(item.childCount()):
                found = walk(item.child(i))
                if found is not None:
                    return found
            return None

        for i in range(self.tree.topLevelItemCount()):
            found = walk(self.tree.topLevelItem(i))
            if found is not None:
                return found
        return None

    def _select_element(self, element: Optional[ET.Element]) -> None:
        self._selected = element
        self._sync_properties()

    def _sync_properties(self) -> None:
        if self._selected is None:
            self.props.hide()
            self.empty_props.show()
            return
        self.empty_props.hide()
        self.props.show()

        self._signals_blocked = True
        self.edit_name.setText(self._selected.tag or "")
        self.edit_text.setPlainText(self._selected.text or "")
        self.attrs.set_attributes(dict(self._selected.attrib))
        self._signals_blocked = False

    def _on_name_changed(self, text: str) -> None:
        if self._signals_blocked or self._selected is None:
            return
        name = (text or "").strip()
        if not name:
            return
        self._selected.tag = name
        item = self.tree.currentItem()
        if item:
            item.setText(0, name)
        self._refresh_xml_views()

    def _on_text_changed(self) -> None:
        if self._signals_blocked or self._selected is None:
            return
        txt = self.edit_text.toPlainText()
        self._selected.text = txt if txt.strip() else ""
        self._refresh_xml_views()

    def _on_attrs_changed(self) -> None:
        if self._signals_blocked or self._selected is None:
            return
        self._selected.attrib.clear()
        self._selected.attrib.update(self.attrs.attributes())
        self._refresh_xml_views()

    def _current_xml_text(self) -> str:
        if not self._roots:
            return ""
        if len(self._roots) == 1:
            return format_xml(self._roots[0])
        rendered = [format_xml(r) for r in self._roots]
        header = '<?xml version="1.0" encoding="UTF-8"?>'
        body = []
        for i, text in enumerate(rendered):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("<?xml"):
                lines = lines[1:]
            if i == 0:
                body.append(header)
            body.append("\n".join(lines).strip())
        return "\n".join([b for b in body if b])

    def _refresh_xml_views(self) -> None:
        if not self._roots:
            self.output.setPlainText("")
            self.preview.setPlainText("")
            return
        xml = self._current_xml_text()
        self.output.setPlainText(xml)
        self.preview.setPlainText(xml)

    def _add_root(self) -> None:
        dlg = AddNodeDialog("添加根节点", self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, text = dlg.values()
        if not name:
            self._toast.show("请输入节点名称", "error")
            return
        el = ET.Element(name)
        if text.strip():
            el.text = text
        self._roots.append(el)
        self.rebuild_tree(select=el)
        self._toast.show("节点添加成功", "success")
        self._refresh_xml_views()

    def _add_child(self) -> None:
        if self._selected is None:
            self._toast.show("请选择一个节点", "error")
            return
        dlg = AddNodeDialog("添加子节点", self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, text = dlg.values()
        if not name:
            self._toast.show("请输入节点名称", "error")
            return
        el = ET.Element(name)
        if text.strip():
            el.text = text
        self._selected.append(el)
        self.rebuild_tree(select=el)
        self._toast.show("节点添加成功", "success")
        self._refresh_xml_views()

    def _delete_node(self) -> None:
        if self._selected is None:
            return
        ret = QMessageBox.question(self, "删除节点", "确定删除选中节点及其子节点？")
        if ret != QMessageBox.Yes:
            return
        parent = _find_parent(self._selected, self._roots)
        deleted = self._selected
        if parent is None:
            self._roots = [r for r in self._roots if r is not deleted]
        else:
            parent.remove(deleted)
        self._selected = None
        self.rebuild_tree(select=None)
        self._sync_properties()
        self._refresh_xml_views()
        self._toast.show("节点已删除", "success")

    def _copy_node(self) -> None:
        if self._selected is None:
            return
        self._clipboard_node = clone_element(self._selected)
        self._toast.show("节点已复制", "success")

    def _paste_node(self) -> None:
        if self._selected is None:
            self._toast.show("请选择一个节点", "error")
            return
        if self._clipboard_node is None:
            self._toast.show("没有已复制的节点", "error")
            return
        new_node = clone_element(self._clipboard_node)
        self._selected.append(new_node)
        self.rebuild_tree(select=new_node)
        self._refresh_xml_views()
        self._toast.show("节点已粘贴", "success")

    def _duplicate_node(self) -> None:
        if self._selected is None:
            return
        parent = _find_parent(self._selected, self._roots)
        new_node = clone_element(self._selected)
        if parent is None:
            idx = next((i for i, r in enumerate(self._roots) if r is self._selected), len(self._roots) - 1)
            self._roots.insert(idx + 1, new_node)
        else:
            children = list(parent)
            idx = next((i for i, c in enumerate(children) if c is self._selected), len(children) - 1)
            parent.insert(idx + 1, new_node)
        self.rebuild_tree(select=new_node)
        self._refresh_xml_views()
        self._toast.show("节点已复制", "success")

    def _show_tree_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        el = item.data(0, Qt.UserRole)
        self._selected = el
        self._sync_properties()

        menu = QMenu(self)
        act_add = menu.addAction("添加子节点")
        act_copy = menu.addAction("复制节点")
        act_paste = menu.addAction("粘贴节点")
        act_dup = menu.addAction("复制到同级")
        menu.addSeparator()
        act_del = menu.addAction("删除节点")

        act = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if act == act_add:
            self._add_child()
        elif act == act_copy:
            self._copy_node()
        elif act == act_paste:
            self._paste_node()
        elif act == act_dup:
            self._duplicate_node()
        elif act == act_del:
            self._delete_node()

    def _import_xml(self) -> None:
        dlg = ImportXmlDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        txt = dlg.xml_text().strip()
        if not txt:
            self._toast.show("请输入XML内容", "error")
            return
        try:
            root = parse_xml_text(txt)
        except Exception as e:
            self._toast.show(f"XML 格式错误: {e}", "error")
            return

        self._roots = [root]
        self._selected = None
        self.rebuild_tree(select=None)
        self._sync_properties()
        self._refresh_xml_views()
        self._toast.show("XML 导入成功", "success")

    def _copy_xml(self) -> None:
        xml = self._current_xml_text()
        if not xml.strip():
            self._toast.show("暂无XML内容", "error")
            return
        QApplication.clipboard().setText(xml)
        self._toast.show("XML 已复制到剪贴板", "success")

    def _save_xml(self) -> None:
        xml = self._current_xml_text()
        if not xml.strip():
            self._toast.show("暂无XML内容", "error")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存 XML", "document.xml", "XML (*.xml);;All Files (*)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        self._toast.show("XML 文件已保存", "success")
