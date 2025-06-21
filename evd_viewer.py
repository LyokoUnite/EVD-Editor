#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, struct, os
from collections import OrderedDict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QMenu, QAction,
    QInputDialog, QMessageBox, QVBoxLayout, QWidget, QPushButton
)
from PyQt5.QtCore import Qt

# Type tags
TYPE_LIST   = b'\x35\x85\xba\xb7'
TYPE_STRING = b'\x38\x65\xc1\x17'
TYPE_FLOAT  = b'\x85\x5d\xc4\xa6'
TYPE_BOOL   = b'\x3D\x95\x94\xC8'

# Globals for unpack()
file = None
chunk_count = 0
data_count  = 0

def unpack():
    global file, chunk_count, data_count
    chunk_count += 1

    # 1) read chunk header
    num_entries = int.from_bytes(file.read(4), 'little')
    entries_off = int.from_bytes(file.read(4), 'little')
    data_count += num_entries
    # 2) seek to entries table
    file.seek(entries_off - 4, os.SEEK_CUR)

    data = OrderedDict()
    meta = {}

    for _ in range(num_entries):
        hdr    = file.tell()
        name_ptr = int.from_bytes(file.read(4), 'little')
        variable_name = None
        if name_ptr:
            file.seek(hdr + name_ptr)
            raw = file.read(200).split(b'\x00',1)[0]
            variable_name = raw.decode('utf-8','ignore')
            file.seek(hdr + 4)

        _hash = file.read(4).hex()
        tag   = file.read(4)
        val_off = file.tell()

        if tag == TYPE_LIST:
            # recurse
            rel = int.from_bytes(file.read(4), 'little') - 4
            file.seek(rel, os.SEEK_CUR)
            child_data, child_meta = unpack()
            file.seek(hdr + 0x10, os.SEEK_SET)
            key = variable_name or hex(val_off)
            data[key] = child_data
            meta[key] = child_meta

        elif tag == TYPE_STRING:
            # read the 4-byte pointer
            ptr    = int.from_bytes(file.read(4), 'little')
            # compute real string offset
            str_off = val_off + ptr
            # read zero-terminated string
            file.seek(str_off, os.SEEK_SET)
            raw = file.read(200).split(b'\x00',1)[0]
            value = raw.decode('utf-8','ignore')
            # rewind to next entry
            file.seek(hdr + 0x10, os.SEEK_SET)
            key = variable_name or hex(val_off)
            data[key] = value
            meta[key] = (str_off, tag, value)

        elif tag == TYPE_FLOAT:
            value = struct.unpack('<f', file.read(4))[0]
            key = variable_name or hex(val_off)
            data[key] = value
            meta[key] = (val_off, tag, value)

        elif tag == TYPE_BOOL:
            value = bool(int.from_bytes(file.read(4), 'little'))
            key = variable_name or hex(val_off)
            data[key] = value
            meta[key] = (val_off, tag, value)

        else:
            # unknown: skip its 4 bytes
            file.read(4)

    return data, meta

def parse_evd(path):
    global file, chunk_count, data_count
    file = open(path, 'rb')
    header = file.read()
    if not (header.startswith(b'FBKK') and len(header) > 0x40):
        raise ValueError("Not a valid GR2 .evd file")
    file.seek(0x30, os.SEEK_SET)
    chunk_count = data_count = 0
    data, meta = unpack()
    file.close()
    return data, meta

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GR2 .evd Editor")
        self.resize(800,600)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Attribute","Value"])
        self.tree.setEditTriggers(QTreeWidget.AllEditTriggers)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)

        # Buttons
        self.open_btn = QPushButton("Open EVD")
        self.save_btn = QPushButton("Save EVD")
        self.open_btn.clicked.connect(self.open_evd)
        self.save_btn.clicked.connect(self.save_evd)

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.save_btn)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # State
        self.current_path  = None
        self.cached_binary = None
        self.data, self.meta = None, None

    def open_evd(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open .evd", "", "EVD Files (*.evd)")
        if not path:
            return
        try:
            with open(path,'rb') as f:
                self.cached_binary = bytearray(f.read())
            self.current_path = path
            self.data, self.meta = parse_evd(path)
            self.populate(self.data, self.tree.invisibleRootItem())
            self.tree.expandAll()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def populate(self, data, parent):
        parent.takeChildren()
        for key, val in data.items():
            if isinstance(val, dict):
                item = QTreeWidgetItem([key,""])
                item.setFlags(item.flags()|Qt.ItemIsEditable)
                parent.addChild(item)
                self.populate(val, item)
            else:
                item = QTreeWidgetItem([key, str(val)])
                item.setFlags(item.flags()|Qt.ItemIsEditable)
                parent.addChild(item)

    def on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        add = QAction("Add Entry", self)
        rm  = QAction("Delete Entry", self)
        add.triggered.connect(lambda: self.add_entry(item))
        rm.triggered.connect(lambda: self.remove_entry(item))
        menu.addAction(add)
        menu.addAction(rm)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def add_entry(self, item):
        key, ok = QInputDialog.getText(self, "Add Key", "Name:")
        if not ok or not key: return
        val, ok = QInputDialog.getText(self, "Add Value", "Value:")
        if not ok: return
        child = QTreeWidgetItem([key, val])
        child.setFlags(child.flags()|Qt.ItemIsEditable)
        item.addChild(child)
        item.setExpanded(True)

    def remove_entry(self, item):
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.removeChild(item)

    def save_evd(self):
        if not self.current_path or self.data is None:
            QMessageBox.warning(self, "Error", "No file loaded.")
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save .evd", self.current_path, "EVD Files (*.evd)")
        if not out:
            return
        try:
            edited = self.tree_to_dict(self.tree.invisibleRootItem())
            self.apply_patch(self.cached_binary, self.data, self.meta, edited)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out,'wb') as f:
                f.write(self.cached_binary)
            QMessageBox.information(self, "Saved", out)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def tree_to_dict(self, parent):
        result = OrderedDict()
        for i in range(parent.childCount()):
            c = parent.child(i)
            key = c.text(0)
            if c.childCount():
                result[key] = self.tree_to_dict(c)
            else:
                txt = c.text(1)
                if txt.lower() in ("true","false"):
                    result[key] = txt.lower()=="true"
                else:
                    try: result[key] = float(txt)
                    except: result[key] = txt
        return result

    def apply_patch(self, buf, orig, meta, edited):
        for key, orig_val in orig.items():
            if isinstance(orig_val, dict):
                self.apply_patch(buf, orig_val, meta[key], edited.get(key, {}))
            else:
                new = edited.get(key)
                if new is None or new == orig_val:
                    continue
                off, tag, old = meta[key]
                if tag == TYPE_STRING:
                    bs = str(new).encode('utf-8') + b'\x00'
                    buf[off:off+len(bs)] = bs
                elif tag == TYPE_FLOAT:
                    buf[off:off+4] = struct.pack('<f', float(new))
                elif tag == TYPE_BOOL:
                    buf[off:off+4] = (b'\x01\x00\x00\x00' if new else b'\x00\x00\x00\x00')
                else:
                    try:
                        n = int(new, 16)
                        buf[off:off+4] = n.to_bytes(4, 'little')
                    except:
                        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
