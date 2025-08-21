#!/usr/bin/env python3
import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

# Character classes to handle Z-Library variability
HYPHENS_CLASS = r"\-\u2010\u2011\u2012\u2013\u2014\u2212\uFE63\uFF0D"  # -, ‐, -, ‒, –, —, −, ︳, －
SPACES_CLASS  = r"\s\u00A0\u202F"  # ASCII space, NBSP, narrow NBSP

def normalize_spaces(name: str) -> str:
    """Tidy up spaces created by deletions/replacements."""
    # collapse many kinds of spaces to a regular space for cleanliness
    name = re.sub(f"[{SPACES_CLASS}]+", " ", name)
    name = re.sub(r"\s{2,}", " ", name)
    name = re.sub(r"\s+\.", ".", name)  # "name .pdf" -> "name.pdf"
    return name.strip()

def build_pattern(phrase: str, ignore_case: bool, loose: bool) -> re.Pattern:
    """
    Build a regex that matches the phrase.
    - If loose=True, treat hyphen variants and space variants as equivalent.
    - Otherwise, match the phrase literally.
    """
    flags = re.IGNORECASE if ignore_case else 0

    if not loose:
        return re.compile(re.escape(phrase), flags)

    # Normalize the phrase to NFKC for consistent characters
    p = unicodedata.normalize("NFKC", phrase)

    # Replace simple hyphen and spaces inside the phrase with tolerant classes
    # Example: "(Z-Library)" -> r"\(Z[<hyphens> ]Library\)"
    out = []
    for ch in p:
        if ch in "-\u2010\u2011\u2012\u2013\u2014\u2212\uFE63\uFF0D":
            out.append(f"[{HYPHENS_CLASS}]")
        elif ch.isspace() or ch in "\u00A0\u202F":
            out.append(f"[{SPACES_CLASS}]")
        else:
            out.append(re.escape(ch))
    # Also tolerate extra spaces around the phrase boundaries
    pattern_str = "".join(out)
    # e.g. allow "(Z-Library)" with or without surrounding spaces
    return re.compile(pattern_str, flags)

def propose_new_name(name: str, pattern: re.Pattern, mode: str, replacement: str) -> str:
    """Return a new filename after applying delete/replace via pattern."""
    new = pattern.sub("" if mode == "delete" else replacement, name)
    return normalize_spaces(new)

def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    it = root.rglob("*") if recursive else root.glob("*")
    for p in it:
        if p.is_file():
            yield p

def collect_changes(root: Path, recursive: bool, pattern: re.Pattern, mode: str, replacement: str
                   ) -> Tuple[List[Tuple[Path, Path]], int]:
    changes: List[Tuple[Path, Path]] = []
    total_checked = 0
    for p in iter_files(root, recursive):
        total_checked += 1
        new_name = propose_new_name(p.name, pattern, mode, replacement)
        if new_name != p.name:
            changes.append((p, p.with_name(new_name)))
    return changes, total_checked

def is_dangerous_root(target: Path, home: Path) -> bool:
    try:
        resolved = target.resolve()
    except Exception:
        return False
    return resolved == Path("/") or resolved == home

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete or replace a phrase in filenames (dry-run by default).")
    parser.add_argument("target", nargs="?", help="Directory to scan. If omitted, you will be prompted.")
    parser.add_argument("-p", "--phrase", help="The phrase to delete or replace (literal text).")
    parser.add_argument("--mode", choices=["delete", "replace"], help="Delete or replace the phrase.")
    parser.add_argument("--replacement", default="", help="Replacement text (used only with replace).")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive match.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recurse into subfolders.")
    parser.add_argument("--apply", action="store_true", help="Actually rename files (default is dry-run).")
    parser.add_argument("--force", action="store_true", help="Allow running on '/' or your home directory.")
    parser.add_argument("--loose", action="store_true",
                        help="Tolerant match: treat hyphen/space variants as equal (useful for Z-Library).")
    parser.add_argument("--list-matches", action="store_true",
                        help="List matching filenames before rename (helps verify matching).")
    return parser.parse_args(sys.argv[1:] if argv is None else argv)

def prompt_if_missing(args: argparse.Namespace) -> None:
    if not args.target:
        while True:
            s = input("Enter the directory to scan: ").strip()
            p = Path(s).expanduser()
            if p.exists() and p.is_dir():
                args.target = str(p)
                break
            print(f"Not a valid directory: {p}")
    if not args.phrase:
        while True:
            s = input("Enter the phrase to delete/replace (e.g., (Z-Library)): ").strip()
            if s:
                args.phrase = s
                break
            print("Phrase cannot be empty.")
    if not args.mode:
        m = input("Mode? delete or replace [delete]: ").strip().lower() or "delete"
        while m not in ("delete", "replace"):
            m = input("Please type 'delete' or 'replace': ").strip().lower()
        args.mode = m
    if args.mode == "replace" and args.replacement == "":
        args.replacement = input("Enter replacement text: ")
    # optional: loose + ignore-case prompts could be added interactively if you want

def main() -> None:
    args = parse_args()
    prompt_if_missing(args)

    root = Path(args.target).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Error: {root} is not a directory.")
        sys.exit(1)

    home = Path.home().resolve()
    if is_dangerous_root(root, home) and not args.force:
        print(f"Refusing to run on {root} without --force.")
        sys.exit(2)

    pattern = build_pattern(args.phrase, args.ignore_case, args.loose)

    # Preview matches if requested
    if args.list_matches:
        matched_any = False
        for p in iter_files(root, args.recursive):
            if pattern.search(p.name):
                print(f"[MATCH] {p.name}")
                matched_any = True
        if not matched_any:
            print("No filenames matched the pattern.")
        # still continue to dry-run / rename as usual

    changes, total_checked = collect_changes(root, args.recursive, pattern, args.mode, args.replacement)

    print(f"Scanned {total_checked} file(s) under: {root}")
    if not changes:
        print(f"No filenames contained the phrase (with current options). Try --loose and/or -i.")
        return

    collisions = 0
    errors = 0
    renamed = 0

    if not args.apply:
        print("Mode: DRY-RUN (no changes). Use --apply to perform renames.\n")

    for src, dst in changes:
        if dst.exists() and dst != src:
            print(f"[SKIP] Target exists: {dst.name}  (from: {src.name})")
            collisions += 1
            continue

        if args.apply:
            try:
                src.rename(dst)
                print(f"[RENAME] {src.name} -> {dst.name}")
                renamed += 1
            except Exception as e:
                print(f"[ERROR] {src.name}: {e}")
                errors += 1
        else:
            print(f"[DRY-RUN] {src.name} -> {dst.name}")

    print("\nSummary:")
    changed_if_apply = renamed if args.apply else (len(changes) - collisions)
    print(f"  Checked files:      {total_checked}")
    print(f"  Matched filenames:  {len(changes)}")
    print(f"  Changed (this run): {changed_if_apply}")
    print(f"  Collisions skipped: {collisions}")
    print(f"  Errors:             {errors}")
    if not args.apply:
        print("\nThis was a dry run. Add --apply to perform the renames.")

if __name__ == "__main__":
    main()
