# 📂 File Renamer – Z-Library Cleaner

A Python utility to batch rename files by **deleting or replacing fixed words** (e.g., `(Z-Library)`) from filenames.  
Supports **dry-run previews**, **apply mode**, and basic reporting of how many files were changed.

---

## ✨ Features

- Input any folder path
- Choose whether to **delete** or **replace** a fixed word/phrase in filenames
- Recursive scan of subfolders (`-r`)
- Case-insensitive option (`-i`)
- Dry-run mode (default) – safe preview before changes
- Apply mode (`--apply`) – actually rename files
- Reports: total files checked, matched, changed, skipped

---

## 🚀 Usage

### 1. Run in dry-run mode (preview only)

```bash
python3 rename_zlibrary_2025-08-19.py ~/Downloads -r -p "(Z-Library)" --loose -i
```

### 2. Actually rename files

```bash
python3 rename_zlibrary_2025-08-19.py ~/Downloads -r -p "(Z-Library)" --loose -i --apply
```

### 🔑 Options
- `-r` → recursive into subfolders  
- `-p` → phrase/pattern to delete or replace  
- `--apply` → actually rename files (omit for dry-run)  
- `-i` → ignore case  
- `--loose` → match Unicode hyphens/spaces variants (Z-Library filenames)  

---

## 📝 Example

If you have:

```
Book Title (Z-Library).pdf
Another Book (Z-Library).epub
```

➡ Running with **delete mode**:

```
Book Title.pdf
Another Book.epub
```

➡ Running with **replace mode** (replace with [Clean]):

```
Book Title [Clean].pdf
Another Book [Clean].epub
```

---

## ⚙️ Development

Clone the repo:

```bash
git clone https://github.com/XiaodiDennis/file_renamer_2025-08-19.git
cd file_renamer_2025-08-19
```

(Optional) Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Run the script as shown above.

---

## 📌 Notes

- By default, this tool runs in **dry-run mode** so you don’t accidentally rename files.  
- Use `--apply` only when you’re sure.  
- Works on **macOS, Linux, Windows** with Python 3.8+.  

---

## 📄 License

MIT License © 2025 XiaodiDennis
