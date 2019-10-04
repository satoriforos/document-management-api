from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from reportlab.lib.units import mm
from reportlab.lib.units import inch

class PdfCollager:

    font_folder = 'fonts/'

    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        TTFSearchPath = (
            BASE_DIR + "/" + self.font_folder,
            '/usr/lib/X11/fonts/TrueType/',
            '/usr/share/fonts/truetype',
            '/usr/share/fonts',             #Linux, Fedora
            '/usr/share/fonts/dejavu',      #Linux, Fedora
            #mac os X - from
            #http://developer.apple.com/technotes/tn/tn2024.html
            '~/Library/Fonts',
            '/Library/Fonts',
            '/Network/Library/Fonts',
            '/System/Library/Fonts',
        )

    def open_pdf_from_data(self, data):
        io_data = io.BytesIO()
        io_data.write(data)
        pdf = PdfFileReader(io_data)
        return pdf

    def register_font(self, font_name, font_filename):
        pdfmetrics.registerFont(TTFont(font_name, font_filename))

    def add_text_to_page(
        self,
        pdf,
        text,
        x,
        y,
        page_number=0,
        font_name=None,
        font_size=None
    ):
        requests = []
        requests.append({
            "text": text,
            "x": x,
            "y": y,
            "page_number": page_number,
            "font_name": font_name,
            "font_size": font_size
        })
        return self.add_texts_to_pages(pdf, requests)

    def add_texts_to_pages(pdf, requests):

        for request in requests:
            page_number = request["page_number"]
            font_name = request["font_name"]
            font_size = request["font_size"]
            x = request["x"]
            y = request["y"]
            text = request["text"]

            page_size_inches = pdf.pages[page_number].mediaBox
            packet = io.BytesIO()
            # create a new PDF with Reportlab
            c = canvas.Canvas(
                packet,
                pagesize=(page_size_inches[2] * inch, page_size_inches[3] * inch)
            )
            if font_name is not None and font_size is not None:
                c.setFont(font_name, font_size)
            c.drawString(x, y, text)
            c.save()

            # move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PdfFileReader(packet)

            # read your existence PDF
            output = PdfFileWriter()

            # add the "watermark" (which is the new pdf) on the existing page
            page = pdf.getPage(page_number)
            page.mergePage(new_pdf.getPage(0))

            output.addPage(page)

        pdf_bytes = output.stream.getvalue()
        return pdf_bytes
