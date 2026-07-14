"""
Converts uploaded files into Quill Delta JSON so they can be opened directly
in the same rich-text editor used for regular documents.

Scope (intentionally limited — see README):
  - .txt  -> each line becomes a plain paragraph
  - .md   -> each line becomes a paragraph; '# ', '## ', '### ' headings are
             mapped to Quill header levels 1-3. No other Markdown syntax
             (bold/italic/links/lists) is parsed — this is a deliberate scope
             cut, not an oversight.
  - .docx -> each paragraph's plain text is extracted via python-docx.
             Bold/italic run-level formatting inside a .docx is NOT preserved
             (would require walking runs and mapping styles) — only
             paragraph text and heading styles are kept.
"""
import json
import io
import docx

ALLOWED_EXTENSIONS = {"txt", "md", "docx"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2MB cap, generous for text-based docs


class UnsupportedFileType(Exception):
    pass


def get_extension(filename):
    if "." not in filename:
        return None
    return filename.rsplit(".", 1)[1].lower()


def file_to_delta(filename, file_bytes):
    """Returns (title, delta_json_string) for a supported file, or raises
    UnsupportedFileType."""
    ext = get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(
            f"'.{ext}' is not supported. Allowed types: .txt, .md, .docx"
        )

    title = filename.rsplit(".", 1)[0][:200] or "Imported Document"

    if ext == "txt":
        ops = _text_to_ops(file_bytes.decode("utf-8", errors="replace"))
    elif ext == "md":
        ops = _markdown_to_ops(file_bytes.decode("utf-8", errors="replace"))
    else:  # docx
        ops = _docx_to_ops(file_bytes)

    return title, json.dumps({"ops": ops})


def _text_to_ops(text):
    ops = []
    for line in text.splitlines() or [""]:
        ops.append({"insert": line + "\n"})
    return ops


def _markdown_to_ops(text):
    ops = []
    for line in text.splitlines() or [""]:
        stripped = line.lstrip("#").strip()
        heading_level = len(line) - len(line.lstrip("#"))
        if 1 <= heading_level <= 3 and line.startswith("#"):
            ops.append({"insert": stripped + "\n", "attributes": {"header": heading_level}})
        else:
            ops.append({"insert": line + "\n"})
    return ops


def _docx_to_ops(file_bytes):
    document = docx.Document(io.BytesIO(file_bytes))
    ops = []
    for para in document.paragraphs:
        text = para.text or ""
        style = (para.style.name or "").lower()
        if style.startswith("heading"):
            try:
                level = min(int(style.split()[-1]), 3)
            except ValueError:
                level = 1
            ops.append({"insert": text + "\n", "attributes": {"header": level}})
        else:
            ops.append({"insert": text + "\n"})
    if not ops:
        ops = [{"insert": "\n"}]
    return ops