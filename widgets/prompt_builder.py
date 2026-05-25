import os
import json
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QTabBar,
    QPushButton, QTextEdit, QLabel, QGroupBox, QDialog, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QFont, QIcon
from config import tr, settings
from .flow_layout import FlowLayout


TAGS_DIR = os.path.join(os.path.dirname(__file__), "..", "tags")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts_history.json")
HISTORY_MAX = 20
FAVORITES_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts_favorites.json")
PRESETS_DIR = os.path.join(TAGS_DIR, "presets")


class PromptBuilderPanel(QWidget):
    prompt_ready = pyqtSignal(str)
    neg_prompt_ready = pyqtSignal(str)

    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self._engine = engine
        self._categories = []
        self._selected = []
        self._neg_selected = []
        self._random_selected = []
        self._tag_btns = {}
        self._tag_btns_neg = {}
        self._emb_page_idx = None
        self._presets = []
        self._preset_btns = {}
        self._active_preset = None
        self._load_tags()
        self._load_presets()

        self._watcher = QFileSystemWatcher(self)
        if os.path.isdir(TAGS_DIR):
            self._watcher.addPath(TAGS_DIR)
        if os.path.isdir(PRESETS_DIR):
            self._watcher.addPath(PRESETS_DIR)
        self._watcher.directoryChanged.connect(self.refresh_tags)

        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(15, 10, 15, 10)
        main_l.setSpacing(8)

        self._tab_bar = QTabBar()
        self._stack = QStackedWidget()
        self._build_tag_pages()

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

        # Style Presets group box
        self._preset_group = QGroupBox(tr("pb_presets"))
        self._preset_group.setStyleSheet(
            "QGroupBox { color: #aaa; font-size: 11px; font-weight: bold; "
            "border: 1px solid #333; border-radius: 6px; margin-top: 6px; "
            "padding: 12px 6px 6px 6px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        preset_l = QVBoxLayout(self._preset_group)
        preset_l.setContentsMargins(4, 4, 4, 4)
        preset_l.setSpacing(4)
        self._preset_flow = FlowLayout()
        self._preset_flow.setSpacing(4)
        preset_l.addLayout(self._preset_flow)
        self._build_preset_ui()
        self._preset_group.setVisible(bool(self._presets))
        main_l.addWidget(self._preset_group)

        preview_row = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        lbl_pos = QLabel(tr("pb_preview"))
        lbl_pos.setStyleSheet("color: #aaa; font-size: 11px;")
        left_col.addWidget(lbl_pos)
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFixedHeight(70)
        self._preview.setStyleSheet("background: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: #ccc; padding: 6px;")
        left_col.addWidget(self._preview)
        preview_row.addLayout(left_col)

        right_col = QVBoxLayout()
        right_col.setSpacing(2)
        lbl_neg = QLabel(tr("pb_neg_preview"))
        lbl_neg.setStyleSheet("color: #e06060; font-size: 11px;")
        right_col.addWidget(lbl_neg)
        self._neg_preview = QTextEdit()
        self._neg_preview.setReadOnly(True)
        self._neg_preview.setFixedHeight(70)
        self._neg_preview.setStyleSheet("background: #1a1a1a; border: 1px solid #8b3a3a; border-radius: 4px; color: #e06060; padding: 6px;")
        self._neg_preview.setPlaceholderText(tr("pb_neg_empty"))
        right_col.addWidget(self._neg_preview)
        preview_row.addLayout(right_col)

        main_l.addLayout(preview_row)

        btn_row = QHBoxLayout()
        self._btn_history = QPushButton(tr("pb_history"))
        self._btn_history.setObjectName("SecondaryBtn")
        self._btn_history.clicked.connect(self._show_history)
        self._btn_fav = QPushButton(tr("pb_favorites"))
        self._btn_fav.setObjectName("SecondaryBtn")
        self._btn_fav.clicked.connect(self._show_favorites)
        self._btn_fav_save = QPushButton(tr("pb_fav_save"))
        self._btn_fav_save.setObjectName("SecondaryBtn")
        self._btn_fav_save.clicked.connect(self._save_favorite_dialog)
        self._btn_clear = QPushButton(tr("pb_clear"))
        self._btn_clear.setObjectName("SecondaryBtn")
        self._btn_clear.clicked.connect(self._clear_all)
        self._btn_random = QPushButton("\U0001F3B2 " + tr("pb_random"))
        self._btn_random.setObjectName("SecondaryBtn")
        self._btn_random.clicked.connect(self._randomize)
        self._btn_copy = QPushButton(tr("pb_copy"))
        self._btn_copy.setObjectName("GenerateBtn")
        self._btn_copy.setFixedHeight(40)
        self._btn_copy.clicked.connect(self._copy_to_t2i)
        btn_row.addWidget(self._btn_history)
        btn_row.addWidget(self._btn_fav)
        btn_row.addWidget(self._btn_fav_save)
        btn_row.addWidget(self._btn_clear)
        btn_row.addWidget(self._btn_random)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_copy)
        main_l.addLayout(btn_row)

    # ---------- tag loading ----------

    def _load_tags(self):
        self._categories = []
        self._neg_categories = []
        if not os.path.isdir(TAGS_DIR):
            return

        builtin_order = ["quality.json", "style.json", "lighting.json", "artists.json"]
        loaded = {}
        neg_loaded = []
        user_files = []

        for fname in os.listdir(TAGS_DIR):
            if not fname.endswith(".json"):
                continue
            if fname == "presets.json":
                continue
            path = os.path.join(TAGS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("type") == "negative":
                neg_loaded.append(data)
            elif fname in builtin_order:
                loaded[fname] = data
            else:
                user_files.append((fname, data))

        for fname in builtin_order:
            if fname in loaded:
                self._categories.append(loaded[fname])

        self._neg_categories = neg_loaded

        user_files.sort(key=lambda x: x[0])
        for fname, data in user_files:
            self._categories.append(data)

    # ---------- preset loading ----------

    def _load_presets(self):
        self._presets = []
        if not os.path.isdir(PRESETS_DIR):
            return
        for fname in sorted(os.listdir(PRESETS_DIR)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(PRESETS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "name" in data and "tags" in data:
                    self._presets.append(data)
            except Exception:
                pass

    # ---------- UI builders ----------

    def _clear_stack_pages(self):
        while self._stack.count() > 0:
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()
        while self._tab_bar.count() > 0:
            self._tab_bar.removeTab(0)

    def _build_tag_pages(self):
        self._clear_stack_pages()
        for cat in self._categories:
            self._tab_bar.addTab(cat["label"])
            page = QWidget()
            flow = FlowLayout(page)
            flow.setSpacing(6)
            for tag in cat["tags"]:
                btn = QPushButton(tag)
                btn.setCheckable(True)
                btn.setStyleSheet(
                    "QPushButton { padding: 4px 10px; border: 1px solid #444; "
                    "border-radius: 4px; background: #2a2a2a; color: #ccc; font-size: 11px; } "
                    "QPushButton:checked { background: #3a6ea5; color: white; border-color: #5a8ec5; }"
                )
                btn.clicked.connect(lambda _, t=tag: self._toggle_tag(t))
                flow.addWidget(btn)
                self._tag_btns[tag] = btn
            page.setLayout(flow)
            self._stack.addWidget(page)

        for cat in self._neg_categories:
            self._tab_bar.addTab(cat["label"])
            page = QWidget()
            flow = FlowLayout(page)
            flow.setSpacing(6)
            for tag in cat["tags"]:
                btn = QPushButton(tag)
                btn.setCheckable(True)
                btn.setStyleSheet(
                    "QPushButton { padding: 4px 10px; border: 1px solid #8b3a3a; "
                    "border-radius: 4px; background: #2a1515; color: #e06060; font-size: 11px; } "
                    "QPushButton:checked { background: #8b3a3a; color: white; border-color: #c06060; }"
                )
                btn.clicked.connect(lambda _, t=tag: self._toggle_neg_tag(t))
                flow.addWidget(btn)
                self._tag_btns_neg[tag] = btn
            page.setLayout(flow)
            self._stack.addWidget(page)

    def _build_preset_ui(self):
        for i in reversed(range(self._preset_flow.count())):
            w = self._preset_flow.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._preset_btns.clear()

        for p in self._presets:
            name = p.get("name", "?")
            icon = p.get("icon", "")
            btn = QPushButton(f"{icon} {name}" if icon else name)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { padding: 4px 10px; border: 1px solid #555; "
                "border-radius: 4px; background: #2a2a2a; color: #ccc; font-size: 11px; } "
                "QPushButton:checked { background: #3a6ea5; color: white; border-color: #5a8ec5; }"
            )
            btn.clicked.connect(lambda _, pdata=p: self._toggle_preset(pdata))
            self._preset_flow.addWidget(btn)
            self._preset_btns[name] = btn

    # ---------- preset logic ----------

    def _toggle_preset(self, pdata):
        name = pdata.get("name", "?")
        btn = self._preset_btns.get(name)

        # Same preset clicked — just deselect
        if self._active_preset == name:
            for t in pdata.get("tags", []):
                if t in self._selected:
                    self._selected.remove(t)
                    if t in self._random_selected:
                        self._random_selected.remove(t)
                    try:
                        self._tag_btns[t].setChecked(False)
                    except (KeyError, RuntimeError):
                        pass
            self._active_preset = None
            if btn:
                btn.setChecked(False)
            self._update_preset_states()
            self._update_preview()
            return

        # Deselect previous preset
        if self._active_preset:
            old = next((p for p in self._presets if p.get("name") == self._active_preset), None)
            if old:
                for t in old.get("tags", []):
                    if t in self._selected:
                        self._selected.remove(t)
                        if t in self._random_selected:
                            self._random_selected.remove(t)
                        try:
                            self._tag_btns[t].setChecked(False)
                        except (KeyError, RuntimeError):
                            pass
            old_btn = self._preset_btns.get(self._active_preset)
            if old_btn:
                old_btn.setChecked(False)

        # Select new preset
        for t in pdata.get("tags", []):
            if t not in self._selected:
                self._selected.append(t)
                try:
                    self._tag_btns[t].setChecked(True)
                except (KeyError, RuntimeError):
                    pass
        self._active_preset = name
        if btn:
            btn.setChecked(True)
        self._update_preset_states()
        self._update_preview()

    def _update_preset_states(self):
        for p in self._presets:
            name = p.get("name", "?")
            btn = self._preset_btns.get(name)
            if not btn:
                continue
            btn.setChecked(name == self._active_preset)

    # ---------- refresh on file change ----------

    def refresh_tags(self):
        old_tag_set = set(self._tag_btns.keys())
        old_neg_tag_set = set(self._tag_btns_neg.keys())
        self._tag_btns.clear()
        self._tag_btns_neg.clear()
        self._load_tags()
        self._build_tag_pages()

        self._stack.addWidget(self._emb_page)
        self._emb_tab_idx = self._tab_bar.addTab(tr("pb_embeddings"))
        self._tab_bar.setTabToolTip(self._emb_tab_idx, tr("pb_embeddings_tip"))
        self._tab_bar.setTabEnabled(self._emb_tab_idx, False)
        self.refresh_embeddings()

        all_tags = set(self._tag_btns.keys())
        all_neg_tags = set(self._tag_btns_neg.keys())
        self._selected = [t for t in self._selected if t in all_tags]
        self._random_selected = [t for t in self._random_selected if t in all_tags]
        self._neg_selected = [t for t in self._neg_selected if t in all_neg_tags]
        for t in self._selected:
            if t in self._tag_btns:
                self._tag_btns[t].setChecked(True)
        for t in self._neg_selected:
            if t in self._tag_btns_neg:
                self._tag_btns_neg[t].setChecked(True)
        self._update_preview()
        self._neg_preview.setPlainText(", ".join(self._neg_selected))

        self._load_presets()
        self._active_preset = None
        self._build_preset_ui()
        self._update_preset_states()
        self._preset_group.setVisible(bool(self._presets))

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
            btn.setStyleSheet(
                "QPushButton { padding: 4px 10px; border: 1px solid #444; "
                "border-radius: 4px; background: #2a2a2a; color: #ccc; font-size: 11px; } "
                "QPushButton:checked { background: #7a4a9e; color: white; border-color: #9a6abe; }"
            )
            btn.clicked.connect(lambda _, t=name: self._toggle_tag(t))
            self._emb_flow.addWidget(btn)
            self._tag_btns[name] = btn

    # ---------- tag toggle logic ----------

    def _toggle_tag(self, tag):
        if tag in self._selected:
            self._selected.remove(tag)
            if tag in self._random_selected:
                self._random_selected.remove(tag)
            self._tag_btns[tag].setChecked(False)
        else:
            self._selected.append(tag)
            self._tag_btns[tag].setChecked(True)
        self._update_preset_states()
        self._update_preview()

    def _toggle_neg_tag(self, tag):
        if tag in self._neg_selected:
            self._neg_selected.remove(tag)
            self._tag_btns_neg[tag].setChecked(False)
        else:
            self._neg_selected.append(tag)
            self._tag_btns_neg[tag].setChecked(True)
        self._neg_preview.setPlainText(", ".join(self._neg_selected))

    def _update_preview(self):
        self._preview.setPlainText(", ".join(self._selected))

    def _clear_all(self):
        self._selected.clear()
        self._random_selected.clear()
        self._active_preset = None
        for btn in list(self._tag_btns.values()):
            try:
                btn.setChecked(False)
            except RuntimeError:
                pass
        self._preview.clear()
        self._neg_selected.clear()
        for btn in list(self._tag_btns_neg.values()):
            try:
                btn.setChecked(False)
            except RuntimeError:
                pass
        self._neg_preview.clear()
        self._update_preset_states()

    def _randomize(self):
        for t in list(self._random_selected):
            if t in self._selected:
                self._selected.remove(t)
            try:
                self._tag_btns[t].setChecked(False)
            except (KeyError, RuntimeError):
                pass
        self._random_selected.clear()

        count = int(settings.get("PromptBuilder", "random_tags_count", fallback="1"))
        for cat in self._categories:
            cat_tags = cat["tags"]
            chosen = random.sample(cat_tags, min(count, len(cat_tags)))
            for t in chosen:
                self._selected.append(t)
                self._random_selected.append(t)
                try:
                    self._tag_btns[t].setChecked(True)
                except (KeyError, RuntimeError):
                    pass
        self._update_preset_states()
        self._update_preview()

    def _copy_to_t2i(self):
        text = self._preview.toPlainText().strip()
        if text:
            self._save_to_history(self._selected.copy(), text, self._neg_selected.copy())
            self.prompt_ready.emit(text)
        neg_text = self._neg_preview.toPlainText().strip()
        if neg_text:
            self.neg_prompt_ready.emit(neg_text)

    # ---------- history ----------

    def _history_path(self):
        return HISTORY_PATH

    def _load_history(self):
        path = self._history_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_to_history(self, tags, prompt, neg_tags=None):
        history = self._load_history()
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "prompt": prompt,
            "tags": tags,
            "negative_tags": neg_tags if neg_tags is not None else [],
        }
        history.insert(0, entry)
        history = history[:HISTORY_MAX]
        try:
            with open(self._history_path(), "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _set_tags(self, tag_names, neg_tag_names=None):
        self._clear_all()
        for t in tag_names:
            if t in self._tag_btns:
                self._toggle_tag(t)
        if neg_tag_names:
            for t in neg_tag_names:
                if t in self._tag_btns_neg:
                    self._toggle_neg_tag(t)

    def _show_history(self):
        history = self._load_history()
        if not history:
            dlg = QDialog(self)
            dlg.setWindowTitle(tr("pb_history"))
            dlg.setMinimumSize(400, 200)
            l = QVBoxLayout(dlg)
            lbl = QLabel(tr("pb_history_empty"))
            lbl.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            dlg.exec()
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("pb_history"))
        dlg.setMinimumSize(500, 350)
        l = QVBoxLayout(dlg)

        lst = QListWidget()
        lst.setStyleSheet(
            "QListWidget { background: #1a1a1a; border: 1px solid #333; border-radius: 4px; } "
            "QListWidget::item { color: #ccc; padding: 8px; border-bottom: 1px solid #333; } "
            "QListWidget::item:hover { background: #2a2a2a; }"
        )
        for entry in history:
            ts = entry.get("timestamp", "")
            prompt = entry.get("prompt", "")
            tags = entry.get("tags", [])
            neg_tags = entry.get("negative_tags", [])
            neg_text = ", ".join(neg_tags)
            display = f"{ts}  |  {prompt}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, tags)
            item.setData(Qt.ItemDataRole.UserRole + 1, prompt)
            item.setData(Qt.ItemDataRole.UserRole + 2, neg_tags)
            item.setData(Qt.ItemDataRole.UserRole + 3, neg_text)
            item.setToolTip(prompt)
            lst.addItem(item)

        l.addWidget(lst)

        btn_row = QHBoxLayout()

        btn_load = QPushButton(tr("pb_history_load"))
        btn_load.setObjectName("SecondaryBtn")
        btn_load.setEnabled(False)

        btn_copy = QPushButton(tr("pb_copy"))
        btn_copy.setObjectName("SecondaryBtn")
        btn_copy.setEnabled(False)

        def apply_load():
            item = lst.currentItem()
            if item:
                self._set_tags(
                    item.data(Qt.ItemDataRole.UserRole),
                    item.data(Qt.ItemDataRole.UserRole + 2),
                )
                dlg.accept()

        def apply_copy():
            item = lst.currentItem()
            if item:
                text = item.data(Qt.ItemDataRole.UserRole + 1)
                if text:
                    self.prompt_ready.emit(text)
                neg_text = item.data(Qt.ItemDataRole.UserRole + 3)
                if neg_text:
                    self.neg_prompt_ready.emit(neg_text)
                dlg.accept()

        def on_selection():
            enabled = bool(lst.currentItem())
            btn_load.setEnabled(enabled)
            btn_copy.setEnabled(enabled)

        lst.currentItemChanged.connect(on_selection)
        lst.itemDoubleClicked.connect(apply_load)
        btn_load.clicked.connect(apply_load)
        btn_copy.clicked.connect(apply_copy)
        btn_row.addWidget(btn_load)
        btn_row.addStretch()
        btn_row.addWidget(btn_copy)
        l.addLayout(btn_row)

        dlg.exec()

    # ---------- favorites ----------

    def _favorites_path(self):
        return FAVORITES_PATH

    def _load_favorites(self):
        path = self._favorites_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_favorites(self, favs):
        try:
            with open(self._favorites_path(), "w", encoding="utf-8") as f:
                json.dump(favs, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _save_favorite_dialog(self):
        text = self._preview.toPlainText().strip()
        if not text:
            return
        name, ok = QInputDialog.getText(self, tr("pb_fav_save"), tr("pb_fav_name"))
        if not ok or not name.strip():
            return
        name = name.strip()
        favs = self._load_favorites()
        neg_text = self._neg_preview.toPlainText().strip()
        favs.append(
            {
                "name": name,
                "prompt": text,
                "tags": self._selected.copy(),
                "negative_tags": self._neg_selected.copy(),
            }
        )
        self._save_favorites(favs)
        QMessageBox.information(self, tr("pb_fav_save"), tr("pb_fav_saved"))

    def _show_favorites(self):
        favs = self._load_favorites()
        if not favs:
            dlg = QDialog(self)
            dlg.setWindowTitle(tr("pb_favorites"))
            dlg.setMinimumSize(400, 200)
            l = QVBoxLayout(dlg)
            lbl = QLabel(tr("pb_fav_empty"))
            lbl.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            dlg.exec()
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("pb_favorites"))
        dlg.setMinimumSize(550, 400)
        l = QVBoxLayout(dlg)

        lst = QListWidget()
        lst.setStyleSheet(
            "QListWidget { background: #1a1a1a; border: 1px solid #333; border-radius: 4px; } "
            "QListWidget::item { color: #ccc; padding: 8px; border-bottom: 1px solid #333; } "
            "QListWidget::item:hover { background: #2a2a2a; }"
        )
        for fav in favs:
            name = fav.get("name", "")
            prompt = fav.get("prompt", "")
            tags = fav.get("tags", [])
            neg_tags = fav.get("negative_tags", [])
            neg_text = ", ".join(neg_tags)
            display = f"{name}  |  {prompt}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, tags)
            item.setData(Qt.ItemDataRole.UserRole + 1, prompt)
            item.setData(Qt.ItemDataRole.UserRole + 2, favs.index(fav))
            item.setData(Qt.ItemDataRole.UserRole + 3, neg_tags)
            item.setData(Qt.ItemDataRole.UserRole + 4, neg_text)
            item.setToolTip(prompt)
            lst.addItem(item)

        l.addWidget(lst)

        btn_row = QHBoxLayout()

        btn_load = QPushButton(tr("pb_fav_load"))
        btn_load.setObjectName("SecondaryBtn")
        btn_load.setEnabled(False)

        btn_copy = QPushButton(tr("pb_copy"))
        btn_copy.setObjectName("SecondaryBtn")
        btn_copy.setEnabled(False)

        btn_delete = QPushButton(tr("pb_fav_delete"))
        btn_delete.setObjectName("SecondaryBtn")
        btn_delete.setEnabled(False)

        def on_selection():
            enabled = bool(lst.currentItem())
            btn_load.setEnabled(enabled)
            btn_copy.setEnabled(enabled)
            btn_delete.setEnabled(enabled)

        def apply_load():
            item = lst.currentItem()
            if item:
                self._set_tags(
                    item.data(Qt.ItemDataRole.UserRole),
                    item.data(Qt.ItemDataRole.UserRole + 3),
                )
                dlg.accept()

        def apply_copy():
            item = lst.currentItem()
            if item:
                text = item.data(Qt.ItemDataRole.UserRole + 1)
                if text:
                    self.prompt_ready.emit(text)
                neg_text = item.data(Qt.ItemDataRole.UserRole + 4)
                if neg_text:
                    self.neg_prompt_ready.emit(neg_text)
                dlg.accept()

        def apply_delete():
            item = lst.currentItem()
            if item:
                idx = item.data(Qt.ItemDataRole.UserRole + 2)
                favs.pop(idx)
                self._save_favorites(favs)
                dlg.accept()

        lst.currentItemChanged.connect(on_selection)
        lst.itemDoubleClicked.connect(apply_load)
        btn_load.clicked.connect(apply_load)
        btn_copy.clicked.connect(apply_copy)
        btn_delete.clicked.connect(apply_delete)
        btn_row.addWidget(btn_load)
        btn_row.addWidget(btn_copy)
        btn_row.addStretch()
        btn_row.addWidget(btn_delete)
        l.addLayout(btn_row)

        dlg.exec()
