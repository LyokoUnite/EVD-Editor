# Gravity Rush 2 .evd Editor

A lightweight PyQt5-based GUI tool for browsing, editing, and exporting Japan Studio's Gravity Rush 2 `.evd` files.

---

## Features

- **Open & Parse**  
  Reads the game’s native `FBKK` chunked format from any `.evd` file.  

- **Tree-View Browsing**  
  Displays nested entries in a two-column tree:  
  - **Attribute** (key)  
  - **Value** (string, float, bool)  
  Container (list) nodes show no value, only their children.

- **In-Place Editing**  
  - Double-click any attribute or value to edit.  
  - Right-click menu to **Add** or **Delete** entries at any level.

- **Lossless Export**  
  - Patches only the bytes you changed, preserving the rest of the original file exactly.  
  - Supports editing of strings, floats, booleans, and raw hex fields.

- **Zero Dependencies**  
  Apart from PyQt5 and Python 3.6+, no extra libraries required.

Research & Reverse-Engineering
Special thanks to illusion and null for their invaluable research data on the GR2 .evd format.
