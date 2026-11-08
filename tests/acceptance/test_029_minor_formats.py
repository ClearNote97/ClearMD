"""Feature 029 — e-mail, Rich Text and subtitles (spec/features/029_*/spec.md): real files through
the command line, the Markdown read back."""

from email.message import EmailMessage
from pathlib import Path

import pytest

from clearmd.backend.schemas.formats import FormatId, format_for_extension
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.rtf import rtf_text
from clearmd.backend.services.conversion.subtitles import cues
from clearmd.frontend.cli import main
from clearmd.frontend.presenter.icons import ICONS, icon_of_format
from clearmd.i18n import load_catalog

RTF = (
    rb"{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0 Calibri;}}{\colortbl;\red255\green0\blue0;}"
    rb"{\*\generator Word;}\pard\b Informe\b0\par Caf\'e9 y ma\u241?ana \{ok\}\par}"
)
SRT = (
    "1\n00:00:01,000 --> 00:00:03,000\nHello <i>there</i>\nfriend\n\n"
    "2\n00:01:02,500 --> 00:01:04,000\nBye\n"
)
VTT = "WEBVTT\n\n00:01.000 --> 00:02.000\n<v Ana>Hola</v>\n\n01:02:03.000 --> 01:02:04.000\nAdiós\n"


def result(workdir: Path, name: str) -> str:
    assert main([str(workdir / name), "--quiet"]) == 0
    return (workdir / "ClearMD_Output" / "OutputMD" / Path(name).with_suffix(".md")).read_text()


def test_ac_01_an_email_with_its_headers_text_and_attachment_names(workdir: Path) -> None:
    message = EmailMessage()
    message["Subject"] = "Quarterly report"
    message["From"] = "Ana <ana@example.com>"
    message["To"] = "Beto <beto@example.com>"
    message["Date"] = "Sat, 08 Nov 2026 10:00:00 -0500"
    message.set_content("Hello Beto,\n\nthe report is attached.\n")
    message.add_attachment(
        b"%PDF-1.4 secret", maintype="application", subtype="pdf", filename="q3.pdf"
    )
    (workdir / "mail.eml").write_bytes(bytes(message))
    text = result(workdir, "mail.eml")
    assert text.startswith("# Quarterly report\n")
    assert "- **From:** Ana <ana@example.com>" in text and "- **To:**" in text
    assert "the report is attached." in text
    assert "**Attachments:** q3.pdf" in text and "secret" not in text  # names, never contents


def test_ac_01_an_html_only_email_is_converted(workdir: Path) -> None:
    message = EmailMessage()
    message["Subject"] = "News"
    message.set_content(
        "<html><body><h1>Big</h1><p>Some <b>news</b>.</p></body></html>", subtype="html"
    )
    (workdir / "news.eml").write_bytes(bytes(message))
    text = result(workdir, "news.eml")
    assert "Big" in text and "news" in text and "<p>" not in text


def test_ac_02_rich_text_keeps_the_text_and_drops_the_formatting(workdir: Path) -> None:
    assert rtf_text(RTF) == "Informe\n\nCafé y mañana {ok}"
    (workdir / "doc.rtf").write_bytes(RTF)
    assert "Café y mañana" in result(workdir, "doc.rtf")
    summary = (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text()
    english = load_catalog("en").text_template(NoteKind.FORMATTING_DROPPED.key)
    assert english.split("{")[0].strip()[:20] in summary


def test_ac_03_subtitles_one_line_per_cue_with_its_start(workdir: Path) -> None:
    assert cues(SRT) == [("00:00:01", "Hello there friend"), ("00:01:02", "Bye")]
    assert cues(VTT) == [("00:00:01", "Hola"), ("01:02:03", "Adiós")]
    (workdir / "talk.srt").write_text(SRT, "utf-8")
    assert result(workdir, "talk.srt") == "`00:00:01` Hello there friend\n\n`00:01:02` Bye\n"
    (workdir / "clip.vtt").write_text(VTT, "utf-8")
    assert "`01:02:03` Adiós" in result(workdir, "clip.vtt")


@pytest.mark.parametrize(
    ("extension", "format_id"),
    [
        (".eml", FormatId.EML),
        (".RTF", FormatId.RTF),
        (".srt", FormatId.SRT),
        (".vtt", FormatId.VTT),
    ],
)
def test_ac_04_recognised_with_an_icon(extension: str, format_id: FormatId) -> None:
    assert format_for_extension(extension) is format_id
    assert icon_of_format(format_id) in ICONS


def test_ac_04_a_damaged_file_fails_alone_and_the_help_lists_them(workdir: Path) -> None:
    (workdir / "bad.rtf").write_bytes(b"not rich text at all")
    (workdir / "ok.srt").write_text(SRT, "utf-8")
    assert main([str(workdir / "bad.rtf"), str(workdir / "ok.srt"), "--quiet"]) == 1
    assert (workdir / "ClearMD_Output" / "OutputMD" / "ok.md").is_file()
    for language in ("en", "es"):
        help_text = load_catalog(language).text("gui.help.formats")
        assert ".eml" in help_text and ".rtf" in help_text and ".vtt" in help_text
