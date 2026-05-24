import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer, QThread
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtGui import QPixmap, QDesktopServices
from config import settings, tr


class UrlDownloaderTab(QWidget):
    """URL-based model downloader — paste a link, see info, download."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parsed = None
        self._info = None
        self._selected_file_idx = 0
        self._analyze_timer = QTimer()
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.timeout.connect(self.do_analyze)
        self.placeholder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self._search_thread = None
        self.init_ui()
        self._show_search_results(False)

    def init_ui(self):
        l = QVBoxLayout(self)

        # ── Search section ──
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("dl_search_models"))
        self.search_input.returnPressed.connect(self.do_search_results)
        search_row.addWidget(self.search_input, 1)
        self.btn_search = QPushButton("🔍 " + tr("dl_search"))
        self.btn_search.setObjectName("SecondaryBtn")
        self.btn_search.setFixedWidth(100)
        self.btn_search.clicked.connect(self.do_search_results)
        search_row.addWidget(self.btn_search)
        l.addLayout(search_row)

        self.search_results = QTreeWidget()
        self.search_results.setHeaderLabels([
            tr("dl_name"), tr("dl_source"), tr("dl_architecture"),
            tr("dl_type"), tr("dl_author")
        ])
        self.search_results.setColumnWidth(0, 180)
        self.search_results.setColumnWidth(1, 60)
        self.search_results.setColumnWidth(2, 70)
        self.search_results.setColumnWidth(3, 70)
        self.search_results.setAlternatingRowColors(True)
        self.search_results.setRootIsDecorated(False)
        self.search_results.itemClicked.connect(self._on_result_clicked)
        self.search_results.setMinimumHeight(100)
        l.addWidget(self.search_results, 1)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        l.addWidget(sep)

        # ── URL input ──
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(tr("dl_url_placeholder"))
        self.url_input.textChanged.connect(self._on_url_changed)
        url_row.addWidget(self.url_input, 1)
        self.btn_analyze = QPushButton(tr("dl_btn_analyze"))
        self.btn_analyze.setObjectName("SecondaryBtn")
        self.btn_analyze.setFixedWidth(100)
        self.btn_analyze.clicked.connect(self.do_analyze)
        url_row.addWidget(self.btn_analyze)
        l.addLayout(url_row)

        # ── Info group ──
        self.info_group = QGroupBox(tr("dl_model_info"))
        info_l = QVBoxLayout(self.info_group)

        info_top = QHBoxLayout()
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(80, 80)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        info_top.addWidget(self.thumb_label)

        info_fields = QVBoxLayout()
        self.lbl_name = QLabel(); self.lbl_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_author = QLabel(); self.lbl_author.setStyleSheet("color: #888;")
        self.lbl_meta = QLabel(); self.lbl_meta.setStyleSheet("color: #aaa;")
        info_fields.addWidget(self.lbl_name)
        info_fields.addWidget(self.lbl_author)
        info_fields.addWidget(self.lbl_meta)
        info_top.addLayout(info_fields, 1)

        self.btn_open_url = QPushButton(tr("dl_open_browser"))
        self.btn_open_url.setFixedWidth(100)
        self.btn_open_url.clicked.connect(self._open_in_browser)
        info_top.addWidget(self.btn_open_url)
        info_l.addLayout(info_top)

        # File/version list
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels([
            tr("dl_name"), tr("dl_file_version"), tr("dl_architecture"), tr("dl_size")
        ])
        self.file_tree.setColumnWidth(0, 200)
        self.file_tree.setColumnWidth(1, 100)
        self.file_tree.setColumnWidth(2, 80)
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setMinimumHeight(80)
        self.file_tree.itemClicked.connect(self._on_file_clicked)
        info_l.addWidget(self.file_tree, 1)

        self.info_group.hide()
        l.addWidget(self.info_group, 1)

        # Download
        dl_row = QHBoxLayout()
        self.btn_download = QPushButton(tr("dl_btn_download"))
        self.btn_download.setObjectName("GenerateBtn")
        self.btn_download.setFixedHeight(40)
        self.btn_download.clicked.connect(self.start_download)
        self.btn_download.setEnabled(False)
        dl_row.addWidget(self.btn_download)

        self.dl_progress = QProgressBar()
        self.dl_progress.setFixedHeight(20)
        self.dl_progress.hide()
        dl_row.addWidget(self.dl_progress, 1)
        l.addLayout(dl_row)

        self.dl_status = QLabel(tr("dl_url_hint"))
        self.dl_status.setStyleSheet("color: #888; font-size: 11px;")
        l.addWidget(self.dl_status)

        l.addStretch()

    def _on_url_changed(self, text):
        self.info_group.hide()
        self.btn_download.setEnabled(False)
        self.dl_status.setText(tr("dl_url_hint"))
        self.thumb_label.clear()
        self._analyze_timer.start(600)

    def _show_search_results(self, visible):
        self.search_results.setVisible(visible)

    def do_search_results(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.search_results.clear()
        self.btn_search.setEnabled(False)
        self.search_results.setHeaderLabel(tr("dl_searching"))

        class _SearchThread(QThread):
            finished = pyqtSignal(list)
            def run(self):
                from models_registry import search_source, reset_page
                token = settings.get('Integration', 'hf_token')
                api_key = settings.get('Integration', 'civitai_api_key')
                all_results = []
                for src in ["CivitAI", "HuggingFace"]:
                    reset_page(src)
                    results, _ = search_source(src, query, token, api_key, None)
                    for r in results:
                        r["_source_label"] = src
                    all_results.extend(results)
                self.finished.emit(all_results)

        self._search_thread = _SearchThread()
        self._search_thread.finished.connect(self._on_search_done)
        self._search_thread.start()

    def _on_search_done(self, results):
        self.btn_search.setEnabled(True)
        self.search_results.clear()
        self._show_search_results(True)
        if not results:
            self.search_results.setHeaderLabel(tr("dl_search_no_results"))
            return
        self.search_results.setHeaderLabels([
            tr("dl_name"), tr("dl_source"), tr("dl_architecture"),
            tr("dl_type"), tr("dl_author")
        ])
        for r in results:
            src = r.get("_source_label", r.get("source", "?"))
            arch = r.get("architecture", "?")
            mtype = r.get("model_type", "Checkpoint")
            author = r.get("author", "")
            item = QTreeWidgetItem([r.get("name", "?"), src, arch, mtype, author])
            item.setData(0, Qt.ItemDataRole.UserRole, r)
            self.search_results.addTopLevelItem(item)
        self.search_results.resizeColumnToContents(2)
        self.dl_status.setText(tr("dl_results_found").format(n=len(results)))

    def _on_result_clicked(self, item, column):
        r = item.data(0, Qt.ItemDataRole.UserRole)
        if not r:
            return
        src = r.get("source", "")
        repo_id = r.get("repo_id", "")
        if src == "civitai":
            url = f"https://civitai.com/models/{repo_id}"
        else:
            url = f"https://huggingface.co/{repo_id}"
        self.url_input.setText(url)
        self._show_search_results(False)
        self.do_analyze()

    def do_analyze(self):
        url = self.url_input.text().strip()
        if not url:
            return
        from url_downloader import parse_url, fetch_model_info
        parsed = parse_url(url)
        if not parsed:
            self.dl_status.setText(tr("dl_url_invalid"))
            return
        self.dl_status.setText(tr("dl_analyzing"))
        self.btn_analyze.setEnabled(False)
        self._parsed = parsed
        info = fetch_model_info(parsed)
        self.btn_analyze.setEnabled(True)
        if not info:
            self.dl_status.setText(tr("dl_url_fetch_error"))
            return
        self._info = info
        self._show_info(info)

    def _show_info(self, info):
        self.lbl_name.setText(info.get("name", "?"))
        self.lbl_author.setText(f"{info.get('author', '?')}  |  {info.get('source', '?')}")
        arch = info.get("architecture", "?")
        mt = info.get("model_type", "?")
        cat = info.get("category", "").replace("models_", "")
        n_files = len(info.get("files", []))
        self.lbl_meta.setText(f"{mt}  |  {arch}  |  {cat}  |  {tr('dl_file_count').format(n=n_files)}")

        # Thumbnail — clear before loading new
        self.thumb_label.clear()
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            self._load_thumb(thumb_url)

        # File list
        self.file_tree.clear()
        for i, f in enumerate(info.get("files", [])):
            fn = f.get("name", "?")
            vn = f.get("version_name", "")
            arch_f = f.get("architecture", "")
            sz = f.get("size", 0)
            size_str = f"{sz//1024} MB" if sz else ""
            item = QTreeWidgetItem([fn, vn, arch_f, size_str])
            item.setData(0, Qt.ItemDataRole.UserRole, i)
            item.setToolTip(0, fn)
            self.file_tree.addTopLevelItem(item)

        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)
        self.file_tree.resizeColumnToContents(3)
        if self.file_tree.topLevelItemCount() > 0:
            self.file_tree.topLevelItem(0).setSelected(True)
        self._selected_file_idx = 0

        self.info_group.show()
        self.btn_download.setEnabled(True)
        self.dl_status.setText(tr("dl_url_ready"))

    def _open_in_browser(self):
        url = self.url_input.text().strip()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _load_thumb(self, url):
        req = QNetworkRequest(QUrl(url))
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        req.setTransferTimeout(5000)
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self._on_thumb_loaded)
        self.nam.get(req)

    def _on_thumb_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pix = QPixmap()
            if pix.loadFromData(data):
                self.thumb_label.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        reply.deleteLater()

    def _on_file_clicked(self, item, column):
        idx = item.data(0, Qt.ItemDataRole.UserRole)
        if idx is not None:
            self._selected_file_idx = idx

    def start_download(self):
        if not self._info or not self._info.get("files"):
            return
        files = self._info["files"]
        idx = self._selected_file_idx
        if idx < 0 or idx >= len(files):
            return
        file_info = files[idx]
        category = self._info.get("category", "models_sd")
        dest_dir = settings.get('Paths', category)
        self.btn_download.setEnabled(False)
        self.dl_progress.setValue(0)
        self.dl_progress.show()
        self.dl_status.setText("Pobieranie...")

        from url_downloader import download_model
        self._download_thread(download_model, file_info, dest_dir)

    def _download_thread(self, download_fn, file_info, dest_dir):
        class _DownloadThread(QThread):
            progress = pyqtSignal(float, str)
            finished = pyqtSignal(bool, str)
            def run(self):
                dest = download_fn(file_info, dest_dir, on_progress=lambda p, m: self.progress.emit(p, m))
                if dest:
                    self.finished.emit(True, dest)
                else:
                    self.finished.emit(False, tr("dl_error"))
        self._worker = _DownloadThread()
        self._worker.progress.connect(self._on_dl_progress)
        self._worker.finished.connect(self._on_dl_finished)
        self._worker.start()

    def _on_dl_progress(self, pct, msg):
        self.dl_progress.setValue(int(pct))
        self.dl_status.setText(msg)

    def _on_dl_finished(self, success, msg):
        self.btn_download.setEnabled(True)
        self.dl_progress.hide()
        if success:
            self.dl_status.setText(tr("dl_done"))
        else:
            self.dl_status.setText(f"{tr('dl_error')}: {msg}")


class ScrapingTab(QWidget):
    """Experimental — search via DDG + API fallback, send URLs to downloader."""
    url_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._last_url = None
        self.init_ui()

    def init_ui(self):
        l = QVBoxLayout(self)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("dl_browse_placeholder"))
        self.search_input.returnPressed.connect(self.do_search)
        search_row.addWidget(self.search_input, 1)
        self.btn_search = QPushButton(tr("dl_browse_btn"))
        self.btn_search.setObjectName("SecondaryBtn")
        self.btn_search.setFixedWidth(120)
        self.btn_search.clicked.connect(self.do_search)
        search_row.addWidget(self.btn_search)
        l.addLayout(search_row)

        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels([
            tr("dl_source"), tr("dl_name"), tr("dl_url")
        ])
        self.result_tree.setColumnWidth(0, 70)
        self.result_tree.setColumnWidth(1, 250)
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemClicked.connect(self._on_item_clicked)
        self.result_tree.itemDoubleClicked.connect(self._send_url)
        l.addWidget(self.result_tree, 1)

        btn_row = QHBoxLayout()
        self.btn_send = QPushButton(tr("dl_browse_send"))
        self.btn_send.setObjectName("GenerateBtn")
        self.btn_send.clicked.connect(self._send_url)
        self.btn_send.setEnabled(False)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_send)
        l.addLayout(btn_row)

        self.status_label = QLabel(tr("dl_url_hint"))
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        l.addWidget(self.status_label)

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.result_tree.clear()
        self.btn_search.setEnabled(False)
        self.btn_send.setEnabled(False)
        self._last_url = None
        self.status_label.setText(tr("dl_searching"))

        class _SearchThread(QThread):
            finished = pyqtSignal(list)
            def run(self):
                from scraper import search_ddg_model
                results = search_ddg_model(query)
                self.finished.emit(results)

        self._worker = _SearchThread()
        self._worker.finished.connect(self._on_search_done)
        self._worker.start()

    def _on_search_done(self, results):
        self.btn_search.setEnabled(True)
        if not results:
            self.status_label.setText(tr("dl_search_no_results"))
            return
        for r in results:
            item = QTreeWidgetItem([r["source"], r["title"], r["url"]])
            item.setToolTip(2, r["url"])
            self.result_tree.addTopLevelItem(item)
        self.status_label.setText(tr("dl_search_results").format(n=len(results)))

    def _on_item_clicked(self, item, column):
        self._last_url = item.text(2)
        self.btn_send.setEnabled(True)

    def _send_url(self):
        if self._last_url:
            self.url_selected.emit(self._last_url)


class ModelDownloaderTab(QWidget):
    """Container: URL-based downloader + experimental scraper tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.url_tab = UrlDownloaderTab()
        self.scrape_tab = ScrapingTab()
        self.scrape_tab.url_selected.connect(self._on_scrape_url)
        self.tab_widget.addTab(self.url_tab, "📥 " + tr("dl_tab_download"))
        self.tab_widget.addTab(self.scrape_tab, "🕷️ " + tr("dl_tab_browse"))
        l.addWidget(self.tab_widget)

    def _on_scrape_url(self, url):
        self.tab_widget.setCurrentWidget(self.url_tab)
        self.url_tab.url_input.setText(url)
        self.url_tab.do_analyze()
