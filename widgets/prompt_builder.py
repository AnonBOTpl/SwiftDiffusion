import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QTabBar, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import tr
from .flow_layout import FlowLayout


TAGS_DIR = os.path.join(os.path.dirname(__file__), "..", "tags")


class PromptBuilderPanel(QWidget):
    prompt_ready = pyqtSignal(str)

    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self._engine = engine
        self._categories = []
        self._selected = []
        self._tag_btns = {}
        self._emb_page_idx = None
        self._load_tags()

        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(15, 10, 15, 10)
        main_l.setSpacing(8)

        self._tab_bar = QTabBar()
        self._stack = QStackedWidget()
        for cat in self._categories:
            idx = self._tab_bar.addTab(cat["label"])
            page = QWidget()
            flow = FlowLayout(page)
            flow.setSpacing(6)
            for tag in cat["tags"]:
                btn = QPushButton(tag)
                btn.setCheckable(True)
                btn.setStyleSheet("QPushButton { padding: 4px 10px; border: 1px solid #444; border-radius: 4px; background: #2a2a2a; color: #ccc; font-size: 11px; } QPushButton:checked { background: #3a6ea5; color: white; border-color: #5a8ec5; }")
                btn.clicked.connect(lambda _, t=tag: self._toggle_tag(t))
                flow.addWidget(btn)
                self._tag_btns[tag] = btn
            page.setLayout(flow)
            self._stack.addWidget(page)

        self._emb_page = QWidget()
        self._emb_flow = FlowLayout(self._emb_page)
        self._emb_flow.setSpacing(6)
        self._emb_flow.setContentsMargins(10, 10, 10, 10)
        self._emb_page.setLayout(self._emb_flow)
        self._stack.addWidget(self._emb_page)
        self._emb_tab_idx = self._tab_bar.addTab(tr("pb_embeddings"))
        self._tab_bar.setTabToolTip(self._emb_tab_idx, tr("pb_embeddings_tip"))
        self._tab_bar.setTabEnabled(self._emb_tab_idx, False)

        self._tab_bar.currentChanged.connect(self._stack.setCurrentIndex)
        self.refresh_embeddings()

        cat_row = QHBoxLayout()
        cat_row.addWidget(self._tab_bar)
        cat_row.addStretch()
        main_l.addLayout(cat_row)
        main_l.addWidget(self._stack, 1)

        preview_lbl = QLabel(tr("pb_preview"))
        preview_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        main_l.addWidget(preview_lbl)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFixedHeight(80)
        self._preview.setStyleSheet("background: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: #ccc; padding: 6px;")
        main_l.addWidget(self._preview)

        btn_row = QHBoxLayout()
        self._btn_clear = QPushButton(tr("pb_clear"))
        self._btn_clear.setObjectName("SecondaryBtn")
        self._btn_clear.clicked.connect(self._clear_all)
        self._btn_copy = QPushButton(tr("pb_copy"))
        self._btn_copy.setObjectName("GenerateBtn")
        self._btn_copy.setFixedHeight(40)
        self._btn_copy.clicked.connect(self._copy_to_t2i)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_copy)
        main_l.addLayout(btn_row)

    def _load_tags(self):
        if not os.path.isdir(TAGS_DIR):
            return
        for fname in sorted(os.listdir(TAGS_DIR)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(TAGS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._categories.append(data)
            except Exception:
                pass

    def refresh_embeddings(self):
        for w in reversed(range(self._emb_flow.count())):
            item = self._emb_flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        names = self._engine.get_embeddings() if self._engine else []
        self._tab_bar.setTabText(self._emb_tab_idx, tr("pb_embeddings"))
        self._tab_bar.setTabEnabled(self._emb_tab_idx, True)
        if not names:
            lbl = QLabel(tr("pb_embeddings_empty"))
            lbl.setStyleSheet("color: #666; font-size: 11px; padding: 20px;")
            self._emb_flow.addWidget(lbl)
            return

        for name in names:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet("QPushButton { padding: 4px 10px; border: 1px solid #444; border-radius: 4px; background: #2a2a2a; color: #ccc; font-size: 11px; } QPushButton:checked { background: #7a4a9e; color: white; border-color: #9a6abe; }")
            btn.clicked.connect(lambda _, t=name: self._toggle_tag(t))
            self._emb_flow.addWidget(btn)
            self._tag_btns[name] = btn

    def _toggle_tag(self, tag):
        if tag in self._selected:
            self._selected.remove(tag)
            self._tag_btns[tag].setChecked(False)
        else:
            self._selected.append(tag)
            self._tag_btns[tag].setChecked(True)
        self._update_preview()

    def _update_preview(self):
        self._preview.setPlainText(", ".join(self._selected))

    def _clear_all(self):
        self._selected.clear()
        for btn in self._tag_btns.values():
            btn.setChecked(False)
        self._preview.clear()

    def _copy_to_t2i(self):
        text = self._preview.toPlainText().strip()
        if text:
            self.prompt_ready.emit(text)
