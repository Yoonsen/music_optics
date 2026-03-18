import os
import json
import shutil
import subprocess
import tempfile
import zipfile
import base64
import urllib.request
import urllib.parse
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


DEFAULT_AUDIVERIS = "/Applications/Audiveris.app/Contents/MacOS/Audiveris"
PREVIEW_HEIGHT = 640


def audiveris_exists(audiveris_bin: str) -> bool:
    if Path(audiveris_bin).exists():
        return True
    return shutil.which(audiveris_bin) is not None


def detect_tessdata_prefix() -> str | None:
    env_value = os.getenv("TESSDATA_PREFIX", "").strip()
    if env_value and Path(env_value).exists():
        return env_value

    candidates = [
        str(Path.home() / "tessdata-legacy"),  # Local fallback with legacy-compatible models
        "/opt/homebrew/share/tessdata",  # macOS Homebrew (Apple Silicon)
        "/usr/local/share/tessdata",     # macOS Homebrew (Intel) / custom
        "/usr/share/tesseract-ocr/5/tessdata",  # Ubuntu/Debian
        "/usr/share/tessdata",  # Some Linux distros
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def resolve_nb_manifest_url(user_input: str) -> str:
    value = user_input.strip()
    if not value:
        raise ValueError("Tom verdi.")

    # Full manifest URL
    if value.startswith("http") and "/manifest" in value:
        return value

    # NB item URL: https://www.nb.no/items/<sesamid>?page=5
    if value.startswith("http") and "nb.no/items/" in value:
        parsed = urllib.parse.urlparse(value)
        parts = [p for p in parsed.path.split("/") if p]
        if "items" in parts:
            i = parts.index("items")
            if i + 1 < len(parts):
                sesamid = parts[i + 1]
                return f"https://api.nb.no/catalog/v3/iiif/{sesamid}/manifest"

    # URN URL, extract URN payload
    if value.startswith("http") and "URN:NBN:" in value:
        urn = value.split("URN:NBN:", 1)[1]
        urn = "URN:NBN:" + urn.split()[0].strip().rstrip("/")
        return f"https://api.nb.no/catalog/v3/iiif/{urllib.parse.quote(urn, safe=':')}/manifest"

    # Raw URN
    if value.startswith("URN:NBN:"):
        return f"https://api.nb.no/catalog/v3/iiif/{urllib.parse.quote(value, safe=':')}/manifest"

    # Assume sesamid-like id
    if re.fullmatch(r"[A-Za-z0-9_-]{16,}", value):
        return f"https://api.nb.no/catalog/v3/iiif/{value}/manifest"

    raise ValueError("Ukjent format. Bruk URN, sesamid eller full manifest-URL.")


def extract_nb_requested_page(user_input: str) -> int | None:
    value = user_input.strip()
    if not (value.startswith("http") and "nb.no/items/" in value):
        return None
    try:
        parsed = urllib.parse.urlparse(value)
        params = urllib.parse.parse_qs(parsed.query)
        raw_page = params.get("page", [None])[0]
        if raw_page is None:
            return None
        page = int(raw_page)
        return page if page > 0 else None
    except Exception:  # noqa: BLE001
        return None


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        content = resp.read()
    return json.loads(content.decode("utf-8"))


def extract_canvas_pages(manifest: dict) -> list[dict]:
    pages: list[dict] = []
    items = manifest.get("items", [])
    for idx, canvas in enumerate(items, start=1):
        canvas_items = canvas.get("items", [])
        ann_items = canvas_items[0].get("items", []) if canvas_items else []
        if not ann_items:
            continue
        body = ann_items[0].get("body", {})
        image_url = body.get("id")
        if not image_url:
            continue

        label_obj = canvas.get("label", {})
        label = "-"
        if isinstance(label_obj, dict):
            for _, values in label_obj.items():
                if values:
                    label = str(values[0]).strip()
                    break
        elif isinstance(label_obj, str):
            label = label_obj

        thumb_url = image_url
        services = body.get("service", [])
        if isinstance(services, list) and services:
            service_id = services[0].get("id")
            if service_id:
                thumb_url = f"{service_id}/full/0,240/0/native.jpg"

        pages.append(
            {
                "index": idx,
                "label": label or "-",
                "image_url": image_url,
                "thumb_url": thumb_url,
            }
        )
    return pages


def download_to_path(url: str, path: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as resp:
        path.write_bytes(resp.read())


def get_pdf_page_count(pdf_path: Path) -> int:
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF mangler. Installer med: pip install pymupdf"
        )

    doc = fitz.open(pdf_path)
    try:
        return doc.page_count
    finally:
        doc.close()


def render_pdf_page_to_png(pdf_path: Path, png_path: Path, page_number: int) -> None:
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF mangler. Installer med: pip install pymupdf"
        )

    doc = fitz.open(pdf_path)
    try:
        # page_number is 1-based in UI
        page_idx = page_number - 1
        if page_idx < 0 or page_idx >= doc.page_count:
            raise ValueError(f"Ugyldig sidenummer {page_number}.")
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=300)
        pix.save(str(png_path))
    finally:
        doc.close()


def run_audiveris(
    audiveris_bin: str,
    input_image: Path,
    out_dir: Path,
    ocr_language_spec: str | None = None,
    tessdata_prefix: str | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        audiveris_bin,
        "-batch",
    ]
    if ocr_language_spec:
        cmd.extend(
            [
                "-constant",
                f"org.audiveris.omr.text.Language.defaultSpecification={ocr_language_spec}",
            ]
        )
    cmd.extend(
        [
        "-export",
        "-output",
        str(out_dir),
        str(input_image),
        ]
    )
    run_env = os.environ.copy()
    if tessdata_prefix:
        run_env["TESSDATA_PREFIX"] = tessdata_prefix
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, check=False, env=run_env
    )


def run_audiveris_export_from_omr(
    audiveris_bin: str,
    input_omr: Path,
    out_dir: Path,
    ocr_language_spec: str | None = None,
    tessdata_prefix: str | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        audiveris_bin,
        "-batch",
    ]
    if ocr_language_spec:
        cmd.extend(
            [
                "-constant",
                f"org.audiveris.omr.text.Language.defaultSpecification={ocr_language_spec}",
            ]
        )
    cmd.extend(
        [
        "-export",
        "-output",
        str(out_dir),
        str(input_omr),
        ]
    )
    run_env = os.environ.copy()
    if tessdata_prefix:
        run_env["TESSDATA_PREFIX"] = tessdata_prefix
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, check=False, env=run_env
    )


def find_output_score(out_dir: Path) -> Path | None:
    score_files = sorted(
        [
            p
            for p in out_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".mxl", ".xml", ".musicxml"}
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return score_files[0] if score_files else None


def find_output_omr(out_dir: Path) -> Path | None:
    omr_files = sorted(
        [p for p in out_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".omr"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return omr_files[0] if omr_files else None


def list_output_files(out_dir: Path) -> list[str]:
    files = [p for p in out_dir.rglob("*") if p.is_file()]
    files.sort(key=lambda p: str(p))
    return [str(p.relative_to(out_dir)) for p in files]


def list_all_files(root_dir: Path) -> list[str]:
    files = [p for p in root_dir.rglob("*") if p.is_file()]
    files.sort(key=lambda p: str(p))
    return [str(p.relative_to(root_dir)) for p in files]


def normalize_uploaded_image_to_png(src_path: Path, dst_png_path: Path) -> None:
    with Image.open(src_path) as img:
        rgb = img.convert("RGB")
        rgb.save(dst_png_path, format="PNG")


def upscale_image(src_path: Path, dst_path: Path, scale: float) -> None:
    with Image.open(src_path) as img:
        width, height = img.size
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
        upscaled.save(dst_path, format="PNG")


def has_low_resolution_warning(stdout_text: str) -> bool:
    text = stdout_text.lower()
    return (
        "too low interline value" in text
        or "resolution is too low" in text
        or "sheet flagged as invalid" in text
    )


def extract_musicxml_text(mxl_bytes: bytes) -> str:
    with zipfile.ZipFile(BytesIO(mxl_bytes), "r") as zf:
        xml_candidates = [
            name for name in zf.namelist()
            if name.lower().endswith(".xml") and not name.startswith("META-INF/")
        ]
        if not xml_candidates:
            raise RuntimeError("Fant ingen MusicXML-fil inni .mxl-arkivet.")

        main_xml = xml_candidates[0]
        return zf.read(main_xml).decode("utf-8", errors="replace")


def convert_score_to_midi(score_bytes: bytes, suffix: str) -> bytes | None:
    try:
        from music21 import converter
    except ImportError:
        return None

    with tempfile.TemporaryDirectory(prefix="music_optics_midi_") as tmp:
        tmp_dir = Path(tmp)
        input_path = tmp_dir / f"score{suffix}"
        midi_path = tmp_dir / "score.mid"
        input_path.write_bytes(score_bytes)
        score = converter.parse(str(input_path))
        score.write("midi", fp=str(midi_path))
        return midi_path.read_bytes()


def render_musicxml_preview(xml_text: str, height: int = PREVIEW_HEIGHT) -> None:
    # Render notes in-browser with OpenSheetMusicDisplay for quick visual validation.
    xml_json = json.dumps(xml_text)
    html = f"""
    <div id="score" style="border:1px solid #ddd; border-radius: 8px; padding: 8px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.2/build/opensheetmusicdisplay.min.js"></script>
    <script>
      const xml = {xml_json};
      const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score", {{
        autoResize: true,
        drawingParameters: "default"
      }});
      osmd.load(xml).then(() => osmd.render()).catch((e) => {{
        const el = document.getElementById("score");
        el.innerHTML = "<p style='color:#b00020;font-family:monospace;'>Klarte ikke vise notebilde: " + e + "</p>";
      }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


def render_pdf_preview(pdf_bytes: bytes, height: int = 620) -> None:
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    html = f"""
    <object
      data="data:application/pdf;base64,{encoded}#toolbar=1&navpanes=1&scrollbar=1"
      type="application/pdf"
      width="100%"
      height="{height}"
      style="border:1px solid #ddd; border-radius:8px;"
    >
      <p>PDF-forhandsvisning er ikke tilgjengelig i denne nettleseren.</p>
    </object>
    """
    components.html(html, height=height + 10, scrolling=True)


def render_image_preview(image_path: Path, height: int = PREVIEW_HEIGHT) -> None:
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    html = f"""
    <div style="height:{height}px; border:1px solid #ddd; border-radius:8px; overflow:auto; display:flex; align-items:flex-start; justify-content:center; background:#fff;">
      <img src="data:image/png;base64,{encoded}" style="max-width:100%; height:auto; display:block;" />
    </div>
    """
    components.html(html, height=height + 10, scrolling=False)


def main() -> None:
    st.set_page_config(page_title="Music Optics OMR", layout="wide")
    st.title("Music Optics - OMR demo")
    st.write("Last opp en noteside og generer `MusicXML/MXL` lokalt med Audiveris.")

    env_audiveris = os.getenv("AUDIVERIS_BIN", DEFAULT_AUDIVERIS)
    audiveris_bin = st.text_input("Audiveris binary", value=env_audiveris)
    ocr_language_spec = st.text_input(
        "OCR-språk (Tesseract, pluss-separert)",
        value="nor+eng",
        help="Eksempel: nor+eng eller nor+dan+eng",
    ).strip()
    tessdata_prefix = detect_tessdata_prefix()
    if tessdata_prefix:
        st.caption(f"TESSDATA_PREFIX brukt: {tessdata_prefix}")
    else:
        st.caption("Fant ikke tessdata automatisk. Sett ev. miljøvariabelen TESSDATA_PREFIX.")

    source_mode = st.radio(
        "Kilde",
        options=["Lokal fil", "NB IIIF-manifest"],
        horizontal=True,
    )

    selected_pdf_page = 1
    uploaded = None
    selected_canvas_page: dict | None = None
    source_ready = False
    source_caption = ""

    control_col_1, control_col_2, control_col_3 = st.columns([2, 1, 1])

    if source_mode == "Lokal fil":
        with control_col_1:
            uploaded = st.file_uploader(
                "Browse file",
                type=["png", "jpg", "jpeg", "pdf"],
                accept_multiple_files=False,
            )

        if uploaded is not None and uploaded.name.lower().endswith(".pdf"):
            try:
                with tempfile.TemporaryDirectory(prefix="music_optics_pdfmeta_") as meta_tmp:
                    meta_pdf = Path(meta_tmp) / uploaded.name
                    meta_pdf.write_bytes(uploaded.getvalue())
                    page_count = get_pdf_page_count(meta_pdf)
                options = list(range(1, page_count + 1))
                selected_pdf_page = control_col_2.selectbox(
                    "Velg side i PDF for konvertering",
                    options=options,
                    index=0,
                )
                control_col_3.caption(f"PDF: {page_count} sider")
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Klarte ikke lese antall sider i PDF: {exc}")
        else:
            control_col_2.caption("Sidevalg vises for PDF.")
            control_col_3.caption("")

        if uploaded is not None and uploaded.type.startswith("image/"):
            st.image(uploaded, caption=f"Input: {uploaded.name}", width="stretch")

        source_ready = uploaded is not None
        if uploaded is not None:
            source_caption = uploaded.name

    else:
        with control_col_1:
            manifest_input = st.text_input(
                "URN / sesamid / manifest-URL",
                placeholder="f.eks. URN:NBN:no-nb_digibok_2014012027005",
            ).strip()

        pages: list[dict] = []
        if manifest_input:
            try:
                manifest_url = resolve_nb_manifest_url(manifest_input)
                manifest = fetch_json(manifest_url)
                pages = extract_canvas_pages(manifest)
                label = manifest.get("label", {})
                title = ""
                if isinstance(label, dict):
                    for _, values in label.items():
                        if values:
                            title = str(values[0]).strip()
                            break
                if title:
                    st.caption(f"Manifest: {title}")
                st.caption(f"Manifest-URL: {manifest_url}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Klarte ikke hente/lese manifest: {exc}")

        if pages:
            options = [f"Side {p['index']} ({p['label']})" for p in pages]
            default_index = 0
            requested_page = extract_nb_requested_page(manifest_input)
            if requested_page is not None:
                default_index = max(0, min(len(options) - 1, requested_page - 1))
            selected_label = control_col_2.selectbox("Velg side", options=options, index=default_index)
            selected_idx = options.index(selected_label)
            selected_canvas_page = pages[selected_idx]
            control_col_3.caption(f"Totalt {len(pages)} sider")

            with st.expander("Vis miniatyrer", expanded=False):
                cols = st.columns(4)
                for i, page in enumerate(pages):
                    with cols[i % 4]:
                        st.image(page["thumb_url"], caption=f"Side {page['index']}", width="stretch")
        else:
            control_col_2.caption("Sidevalg vises når manifest er lastet.")
            control_col_3.caption("")

        source_ready = selected_canvas_page is not None
        if selected_canvas_page is not None:
            source_caption = f"NB side {selected_canvas_page['index']} ({selected_canvas_page['label']})"

    if st.button("Konverter til MXL", type="primary", disabled=not source_ready):
        if not audiveris_exists(audiveris_bin):
            st.error(
                "Fant ikke Audiveris-binary. Sett korrekt sti i feltet over, "
                "eller via miljo variabelen AUDIVERIS_BIN."
            )
            return

        if not source_ready:
            st.warning("Velg en kilde for konvertering.")
            return

        with tempfile.TemporaryDirectory(prefix="music_optics_") as tmp:
            tmp_dir = Path(tmp)
            in_dir = tmp_dir / "in"
            out_dir = tmp_dir / "out"
            in_dir.mkdir()
            out_dir.mkdir()

            upload_path: Path | None = None
            if source_mode == "Lokal fil" and uploaded is not None:
                upload_path = in_dir / uploaded.name
                upload_path.write_bytes(uploaded.getvalue())

                if upload_path.suffix.lower() == ".pdf":
                    work_img = in_dir / f"{upload_path.stem}_page{selected_pdf_page}.png"
                    try:
                        render_pdf_page_to_png(upload_path, work_img, selected_pdf_page)
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Klarte ikke lese PDF: {exc}")
                        return
                else:
                    work_img = in_dir / "input.png"
                    try:
                        normalize_uploaded_image_to_png(upload_path, work_img)
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Klarte ikke lese bildefilen: {exc}")
                        return
            else:
                try:
                    if not selected_canvas_page:
                        st.error("Ingen side valgt fra manifest.")
                        return
                    downloaded_img = in_dir / f"nb_page_{selected_canvas_page['index']}.jpg"
                    work_img = in_dir / f"nb_page_{selected_canvas_page['index']}.png"
                    download_to_path(selected_canvas_page["image_url"], downloaded_img)
                    normalize_uploaded_image_to_png(downloaded_img, work_img)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Klarte ikke laste ned valgt side: {exc}")
                    return

            with st.spinner("Kjorer Audiveris..."):
                started = datetime.now()
                try:
                    result = run_audiveris(
                        audiveris_bin,
                        work_img,
                        out_dir,
                        ocr_language_spec or None,
                        tessdata_prefix,
                    )
                except subprocess.TimeoutExpired:
                    st.error("Audiveris timet ut etter 300 sekunder.")
                    return

            elapsed = (datetime.now() - started).total_seconds()
            st.caption(f"Ferdig pa {elapsed:.1f} sekunder")

            retry_result = None
            if has_low_resolution_warning(result.stdout):
                retry_img = in_dir / "input_upscaled_x3.png"
                try:
                    upscale_image(work_img, retry_img, scale=3.0)
                    with st.spinner("Lav opplosning oppdaget. Prover pa nytt med oppskalert bilde (x3)..."):
                        retry_result = run_audiveris(
                            audiveris_bin,
                            retry_img,
                            out_dir,
                            ocr_language_spec or None,
                            tessdata_prefix,
                        )
                    if retry_result.returncode == 0:
                        st.info("Ekstra forsok med oppskalert bilde er gjennomfort.")
                        result = retry_result
                except Exception as exc:  # noqa: BLE001
                    st.warning(f"Klarte ikke retry med oppskalert bilde: {exc}")

            if result.returncode != 0:
                st.error("Audiveris feilet.")
                if result.stdout:
                    st.text_area("STDOUT", result.stdout, height=200)
                if result.stderr:
                    st.text_area("STDERR", result.stderr, height=200)
                if retry_result is not None and retry_result.stdout:
                    st.text_area("STDOUT (retry oppskalering)", retry_result.stdout, height=200)
                if retry_result is not None and retry_result.stderr:
                    st.text_area("STDERR (retry oppskalering)", retry_result.stderr, height=160)
                return

            score_file = find_output_score(out_dir)
            if score_file is None:
                omr_file = find_output_omr(out_dir)
                fallback_result = None

                if omr_file is not None:
                    st.info("Fant .omr, prover en ekstra eksport fra OMR-filen...")
                    try:
                        fallback_result = run_audiveris_export_from_omr(
                            audiveris_bin,
                            omr_file,
                            out_dir,
                            ocr_language_spec or None,
                            tessdata_prefix,
                        )
                    except subprocess.TimeoutExpired:
                        st.warning("Ekstra eksport fra .omr timet ut etter 300 sekunder.")
                    score_file = find_output_score(out_dir)

            if score_file is None:
                st.error("Fant ingen score-fil (.mxl/.xml/.musicxml) i output-mappen.")
                st.caption(f"Audiveris return code (runde 1): {result.returncode}")
                if fallback_result is not None:
                    st.caption(
                        f"Audiveris return code (runde 2 fra .omr): {fallback_result.returncode}"
                    )
                produced = list_output_files(out_dir)
                if produced:
                    st.write("Filer produsert av Audiveris:")
                    st.code("\n".join(produced))
                else:
                    st.write("Audiveris produserte ingen filer i output-mappen.")
                all_tmp = list_all_files(tmp_dir)
                if all_tmp:
                    st.write("Alle filer i arbeidsmappen (debug):")
                    st.code("\n".join(all_tmp))
                if result.stdout:
                    st.text_area("STDOUT", result.stdout, height=200)
                if result.stderr:
                    st.text_area("STDERR", result.stderr, height=200)
                if retry_result is not None and retry_result.stdout:
                    st.text_area("STDOUT (retry oppskalering)", retry_result.stdout, height=200)
                if retry_result is not None and retry_result.stderr:
                    st.text_area("STDERR (retry oppskalering)", retry_result.stderr, height=160)
                if fallback_result is not None and fallback_result.stdout:
                    st.text_area("STDOUT (runde 2 fra .omr)", fallback_result.stdout, height=200)
                if fallback_result is not None and fallback_result.stderr:
                    st.text_area("STDERR (runde 2 fra .omr)", fallback_result.stderr, height=160)

                omr_file = find_output_omr(out_dir)
                if omr_file is not None:
                    st.download_button(
                        label="Last ned OMR-prosjekt (.omr) for manuell inspeksjon",
                        data=omr_file.read_bytes(),
                        file_name=omr_file.name,
                        mime="application/octet-stream",
                    )
                return

            score_bytes = score_file.read_bytes()
            st.success(f"Konvertering fullfort: {score_file.name}")
            st.download_button(
                label="Last ned resultatfil",
                data=score_bytes,
                file_name=score_file.name,
                mime="application/octet-stream",
            )

            xml_text: str | None = None
            try:
                if score_file.suffix.lower() == ".mxl":
                    xml_text = extract_musicxml_text(score_bytes)
                else:
                    xml_text = score_bytes.decode("utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Klarte ikke lage visning av score: {exc}")

            left_col, right_col = st.columns([1, 1])
            with left_col:
                st.subheader("Kilde")
                render_image_preview(work_img, height=PREVIEW_HEIGHT)
                st.caption(f"Arbeidsbilde: {work_img.name} ({source_caption})")
                if upload_path is not None and upload_path.suffix.lower() == ".pdf" and uploaded is not None:
                    with st.expander("Vis original PDF (scroll)", expanded=False):
                        render_pdf_preview(uploaded.getvalue(), height=PREVIEW_HEIGHT)

            with right_col:
                st.subheader("MXL-visning")
                if xml_text:
                    render_musicxml_preview(xml_text, height=PREVIEW_HEIGHT)
                else:
                    st.info("Ingen visning tilgjengelig for denne output-filen.")

            if xml_text:
                with st.expander("Vis MusicXML (raw)"):
                    st.download_button(
                        label="Last ned MusicXML (.xml)",
                        data=xml_text.encode("utf-8"),
                        file_name=f"{score_file.stem}.xml",
                        mime="application/xml",
                    )
                    st.text_area("MusicXML", xml_text, height=320)

            midi_bytes = convert_score_to_midi(score_bytes, score_file.suffix.lower())
            if midi_bytes is not None:
                st.download_button(
                    label="Last ned MIDI (for avspilling)",
                    data=midi_bytes,
                    file_name=f"{score_file.stem}.mid",
                    mime="audio/midi",
                )
            else:
                st.caption("MIDI-konvertering er valgfri. Installer `music21` for MID-eksport.")

            with st.expander("Vis kjorelogg"):
                st.text_area("STDOUT", result.stdout or "(tom)", height=220)
                st.text_area("STDERR", result.stderr or "(tom)", height=160)


if __name__ == "__main__":
    main()
