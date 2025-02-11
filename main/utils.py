import uuid
import os
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage  # Import qo'shildi
from dotenv import load_dotenv
from .models import PDFResult

# .env faylini yuklash (Eslatma: S3 sozlamalari odatda Django settings.py da bo'lishi lozim)
load_dotenv()

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')


def generate_pdf(data):
    # Rasmni URL orqali olamiz
    image_src = data['image']

    # Test natijalarini kategoriyalar bo‘yicha ajratamiz va ball hisoblaymiz
    majburiy_results = []
    fan1_results = []
    fan2_results = []
    majburiy_total = 0.0
    fan1_total = 0.0
    fan2_total = 0.0

    for test in data["results"]:
        category = test.get("category", "")
        status = str(test.get("status", "")).lower()
        if category.startswith("Majburiy_fan"):
            majburiy_results.append(test)
            if status == "true":
                majburiy_total += 1.1
        elif category.startswith("Fan_1"):
            fan1_results.append(test)
            if status == "true":
                fan1_total += 3.1
        elif category.startswith("Fan_2"):
            fan2_results.append(test)
            if status == "true":
                fan2_total += 2.1

    overall_total = majburiy_total + fan1_total + fan2_total

    # Natijalarni HTML formatida shakllantiramiz
    def build_results_html(results):
        html = ""
        for test in results:
            status = str(test.get("status", "")).lower()
            if status == "true":
                symbol_html = '<span style="color: green;">✅</span>'
            else:
                symbol_html = '<span style="color: red;">❌</span>'
            html += f"<div class='result'>{test.get('number')}. {test.get('option')} {symbol_html}</div>"
        return html

    # Har bir kategoriya uchun natijalar ustunini yaratamiz
    columns_html = ""
    if majburiy_results:
        majburiy_html = build_results_html(majburiy_results)
        columns_html += f"""
         <div class="result-column">
             {majburiy_html}
             <div class="total">Jami: {majburiy_total:.1f}</div>
         </div>
        """
    if fan1_results:
        fan1_html = build_results_html(fan1_results)
        columns_html += f"""
         <div class="result-column">
             {fan1_html}
             <div class="total">Jami: {fan1_total:.1f}</div>
         </div>
        """
    if fan2_results:
        fan2_html = build_results_html(fan2_results)
        columns_html += f"""
         <div class="result-column">
             {fan2_html}
             <div class="total">Jami: {fan2_total:.1f}</div>
         </div>
        """

    # HTML shabloni: 1-ustunda rasm, 2-ustunda natijalar
    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @page {{
            size: A4;
            margin: 10mm;
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 10mm;
        }}
        .header h2, .header p {{
            margin: 0;
            padding: 0;
        }}
        .container {{
            display: flex;
            width: 100%;
        }}
        .image-column {{
            width: 60%;
            padding: 2mm;
            box-sizing: border-box;
        }}
        .image-column img {{
            width: 100%;
            max-height: 600px;
            object-fit: contain;
        }}
        .results-container {{
            display: flex;
            flex: 1;
            padding: 2mm;
            box-sizing: border-box;
            gap: 2mm;
        }}
        .result-column {{
            flex: 1;
            font-size: 10px;
            line-height: 1;
            padding: 2mm;
            box-sizing: border-box;
        }}
        .result {{
            margin-bottom: 2mm;
            word-break: break-all;
        }}
        .total {{
            font-weight: bold;
            font-size: 11px;
            margin-top: 5mm;
            text-align: center;
        }}
      </style>
    </head>
    <body>
      <div class="header">
          <h2>ID: {data['id']}</h2>
          <p>Telefon: {data['phone']}</p>
          <hr>
      </div>
      <div class="container">
         <!-- 1-ustun: Rasm -->
         <div class="image-column">
             <img src="{image_src}" alt="Rasm">
         </div>
         <!-- 2-ustun: Natijalar -->
         <div class="results-container">
             {columns_html}
         </div>
      </div>
      <div class="header" style="margin-top: 10mm;">
          <h3>Umumiy natija: {overall_total:.1f}</h3>
      </div>
    </body>
    </html>
    """

    # WeasyPrint yordamida PDF hosil qilamiz
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()

    # PDF faylni S3 bucket-ga yuklaymiz
    random_filename = f"{uuid.uuid4()}.pdf"
    default_storage.save(random_filename, ContentFile(pdf_bytes))
    pdf_url = default_storage.url(random_filename)

    # PDFResult modeliga PDF URL ni saqlaymiz
    pdf_result = PDFResult.objects.create(
        user_id=data['id'],
        phone=data['phone'],
        pdf_url=pdf_url
    )
    return pdf_url
# End of generate_pdf function