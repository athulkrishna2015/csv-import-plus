# -*- coding: utf-8 -*-

import os
from aqt import mw
from aqt.utils import openLink
from aqt.qt import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPixmap,
    Qt,
)
from aqt.webview import AnkiWebView

class SupportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = parent
        self.setup_ui()
        self.load_supporter_state()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        instr = QLabel(
            "If you find this addon useful, consider supporting the development through the following methods:<br><br>"
            "Check out the <a href='https://github.com/athulkrishna2015/csv-import-plus#changelog'>Changelog</a> for recent updates."
        )
        instr.setWordWrap(True)
        instr.setOpenExternalLinks(True)
        instr.setTextFormat(Qt.TextFormat.RichText)
        instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instr)
        
        # Ko-fi Button
        kofi_btn = QPushButton("Support on Ko-fi")
        kofi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        kofi_btn.clicked.connect(lambda: openLink("https://ko-fi.com/D1D01W6NQT"))
        kofi_btn.setStyleSheet("background-color: #29abe0; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        layout.addWidget(kofi_btn)

        # Scroll area for QR codes
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.qr_list = QVBoxLayout(scroll_content)
        self.qr_list.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.qr_list.setSpacing(30)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Ko-fi Widget (Embedded Script)
        self.support_webview = AnkiWebView(self)
        self.support_webview.setFixedHeight(40)
        kofi_html = f"""
        <html>
        <head>
        <style>
          body {{ background-color: transparent; margin: 0; padding: 0; overflow: hidden; }}
        </style>
        <script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script>
        <script type='text/javascript'>
          kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'D1D01W6NQT');
          kofiwidget2.draw();
        </script>
        </head>
        <body></body>
        </html>
        """
        self.support_webview.setHtml(kofi_html)
        layout.addWidget(self.support_webview)

        base_path = os.path.dirname(os.path.dirname(__file__))

        def add_qr(name, address, filename):
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title = QLabel(f"<b>{name}</b>")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(title)

            qr_label = QLabel()
            qr_path = os.path.join(base_path, "Support", filename)
            pixmap = QPixmap(qr_path)
            if not pixmap.isNull():
                qr_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                qr_label.setText("Image not found")
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(qr_label)

            addr_row = QHBoxLayout()
            addr_label = QLineEdit(address)
            addr_label.setReadOnly(True)
            addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            addr_label.setStyleSheet("background: transparent; border: none;")
            
            copy_btn = QPushButton("Copy")
            copy_btn.setFixedWidth(60)
            copy_btn.clicked.connect(lambda _, a=address: QApplication.clipboard().setText(a))
            
            addr_row.addWidget(addr_label, 1)
            addr_row.addWidget(copy_btn)
            vbox.addLayout(addr_row)

            self.qr_list.addWidget(container)

        add_qr("UPI", "athulkrishnasv2015-2@okhdfcbank", "UPI.jpg")
        add_qr("BTC", "bc1qrrek3m7sr33qujjrktj949wav6mehdsk057cfx", "BTC.jpg")
        add_qr("ETH", "0xce6899e4903EcB08bE5Be65E44549fadC3F45D27", "ETH.jpg")

        # Supporter Opt-out
        layout.addSpacing(20)
        self.supporter_check = QCheckBox("I have supported this addon (Hide automatic update welcome)")
        self.supporter_check.setToolTip("Checking this will prevent the Support tab from opening automatically after future updates.")
        self.supporter_check.toggled.connect(self.on_supporter_check_toggled)
        layout.addWidget(self.supporter_check, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

    def load_supporter_state(self):
        addon_id = mw.addonManager.addonFromModule("addon") # or __name__.split('.')[0]
        if not addon_id:
            return
        meta = mw.addonManager.addonMeta(addon_id)
        self.supporter_check.blockSignals(True)
        self.supporter_check.setChecked(meta.get("supporter_opt_out", False))
        self.supporter_check.blockSignals(False)

    def on_supporter_check_toggled(self, checked):
        addon_id = mw.addonManager.addonFromModule("addon")
        if not addon_id:
            return
        meta = mw.addonManager.addonMeta(addon_id)
        meta["supporter_opt_out"] = checked
        mw.addonManager.writeAddonMeta(addon_id, meta)
