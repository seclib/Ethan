"""RAG Extractors — Extraction de texte depuis des fichiers binaires.

La source de vérité binaire reste le FileStore Core ; ce module ne fait que
convertir le contenu binaire en texte indexable (PDF, DOCX, texte).

Aucune dépendance dure :
- DOCX : parsing stdlib (zipfile + xml) — toujours disponible.
- PDF  : ``pypdf`` utilisé s'il est installé (meilleure qualité), sinon un
  extracteur minimaliste stdlib (zlib + parsing des opérateurs texte) prend
  le relais. Si les deux échouent, une ``ValueError`` explicite est levée.
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from xml.etree import ElementTree

logger = logging.getLogger(__name__)

_PDF_EXTENSIONS = (".pdf",)
_DOCX_EXTENSIONS = (".docx",)
_PDF_CONTENT_TYPES = ("application/pdf",)
_DOCX_CONTENT_TYPES = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)


def extract_text(raw: bytes, filename: str = "", content_type: str = "") -> str:
    """Extrait le texte d'un fichier binaire.

    Le dispatch se fait sur l'extension puis le content_type. Les fichiers
    texte (ou de type inconnu) sont retournés tels quels (le décodage UTF-8
    reste géré par l'appelant).

    Raises:
        ValueError: si le format est binaire non supporté ou si l'extraction
            échoue (message explicite pour l'utilisateur final).
    """
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    is_pdf = name.endswith(_PDF_EXTENSIONS) or ctype in _PDF_CONTENT_TYPES
    is_docx = name.endswith(_DOCX_EXTENSIONS) or ctype in _DOCX_CONTENT_TYPES

    if is_pdf:
        return _extract_pdf(raw)
    if is_docx:
        return _extract_docx(raw)
    # Fichiers texte / type inconnu : pas d'extraction nécessaire.
    return ""


def _extract_pdf(raw: bytes) -> str:
    """Extrait le texte d'un PDF (pypdf si disponible, sinon fallback stdlib)."""
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]

        reader = PdfReader(io.BytesIO(raw))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())
        text = "\n\n".join(pages).strip()
        if text:
            return text
        logger.warning("PDF extraction via pypdf a produit un texte vide — fallback stdlib")
    except ImportError:
        logger.info("pypdf non installé — extraction PDF via le fallback stdlib")
    except Exception as exc:
        logger.warning("pypdf a échoué (%s) — fallback stdlib", exc)

    text = _extract_pdf_stdlib(raw)
    if not text:
        raise ValueError(
            "Impossible d'extraire le texte de ce PDF (pypdf non installé ou "
            "PDF non supporté). Installez pypdf : pip install pypdf"
        )
    return text


def _extract_pdf_stdlib(raw: bytes) -> str:
    """Extracteur PDF minimaliste (stdlib uniquement).

    Décompresse les streams FlateDecode et récupère les chaînes littérales
    passées aux opérateurs de texte PDF (Tj / TJ). Fonctionne sur les PDF
    texte simples ; les PDF scannés (images) ne produisent rien — le module
    remonte alors une erreur explicite.
    """
    texts: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.DOTALL):
        blob = match.group(1).rstrip(b"\r\n")
        try:
            import zlib

            blob = zlib.decompress(blob)
        except Exception:
            pass  # stream non compressé : on tente le parsing tel quel
        if b"Tj" not in blob and b"TJ" not in blob:
            continue
        page_chunks: list[str] = []
        # Chaînes littérales (…)
        for literal in re.finditer(rb"\((?:\\.|[^\\()])*\)", blob):
            token = literal.group(0)[1:-1]
            token = _unescape_pdf_string(token)
            if token:
                page_chunks.append(token)
        if page_chunks:
            texts.append(" ".join(page_chunks))
    return "\n\n".join(t.strip() for t in texts if t.strip())


def _unescape_pdf_string(token: bytes) -> str:
    """Décode une chaîne littérale PDF (échappements + octets latin-1)."""
    token = token.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
    return token.decode("latin-1", errors="replace")


def _extract_docx(raw: bytes) -> str:
    """Extrait le texte d'un DOCX (OOXML) via la stdlib.

    Les paragraphes (``<w:p>``) deviennent des lignes, les tabulations et
    sauts de ligne Word sont conservés, toutes les autres balises sont
    supprimées.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(
            "Fichier DOCX invalide (archive word/document.xml introuvable)"
        ) from exc

    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise ValueError("Fichier DOCX invalide (XML corrompu)") from exc

    paragraphs: list[str] = []
    for paragraph in root.iter(f"{W}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            tag = node.tag
            if tag == f"{W}t":
                parts.append(node.text or "")
            elif tag == f"{W}tab":
                parts.append("\t")
            elif tag in (f"{W}br", f"{W}cr"):
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


__all__ = ["extract_text"]
