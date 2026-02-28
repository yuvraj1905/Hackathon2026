import logging

logger = logging.getLogger(__name__)

_WEASYPRINT_INSTALL_HINT = (
    "WeasyPrint system libraries are missing. "
    "Install them with Homebrew and restart the server:\n"
    "  brew install pango cairo gdk-pixbuf\n"
    "See https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#macos"
)


class ProposalPDFService:
    """Convert a rendered HTML proposal into PDF bytes using WeasyPrint."""

    def generate_pdf(self, html: str) -> bytes:
        """
        Convert HTML string to a PDF document.

        WeasyPrint is imported lazily so that missing system libraries
        (Pango, Cairo) do not prevent the server from starting — they are
        only required when this method is actually called.

        Args:
            html: Fully rendered HTML string (from proposal_renderer).

        Returns:
            Raw PDF bytes suitable for streaming in an HTTP response.

        Raises:
            RuntimeError: if WeasyPrint's native libraries are not installed.
        """
        try:
            from weasyprint import HTML  # noqa: PLC0415
        except OSError as exc:
            raise RuntimeError(_WEASYPRINT_INSTALL_HINT) from exc

        logger.info("Generating PDF from HTML (%d chars)...", len(html))
        pdf_bytes: bytes = HTML(string=html).write_pdf()
        logger.info("PDF generated: %d bytes", len(pdf_bytes))
        return pdf_bytes
