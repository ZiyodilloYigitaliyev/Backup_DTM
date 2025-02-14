import uuid
import os
from io import BytesIO
import boto3
from weasyprint import HTML
from dotenv import load_dotenv
from .models import PDFResult

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION_NAME') or 'us-east-1'

def generate_pdf(data):
    image_src = data['image']

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

    # Ro'yxatlarni number bo'yicha tartiblash
    majburiy_results = sorted(majburiy_results, key=lambda x: int(x.get('number', 0)))
    fan1_results = sorted(fan1_results, key=lambda x: int(x.get('number', 0)))
    fan2_results = sorted(fan2_results, key=lambda x: int(x.get('number', 0)))

    def build_results_html(results):
        html = ""
        for test in results:
            raw_status = test.get("status", "")
            status = str(raw_status).lower()
            if status == "true":
                symbol_html = '<img class="result-img" src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/chekvector.png" alt="status">'
            else:
                symbol_html = '<img class="result-img" src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/crossvector.png" alt="status">'
            # Har bir natija uchun elementlarni flex layout orqali bitta qatorda ko'rsatamiz
            html += f"""
            <div class="result">
                <span class="number">{test.get('number')}</span>.
                <span class="option">{test.get('option')}</span>
                {symbol_html}
            </div>
            """
        return html

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

    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @page {{
            size: A5;
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
            color: #000;
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
            color: #000;
            letter-spacing: 0;
        }}

        /* Flex layout: natija elementlari bitta qatorda */
        .result {{
            display: flex;
            align-items: center;
            gap: 4px;
            margin-bottom: 2mm;
            word-break: break-all;
            page-break-inside: avoid;
        }}

        /* Natija rasmining o'lchamlari */
        .result-img {{
            width: 8px !important;
            height: 8px !important;
            display: inline-block;
            vertical-align: middle;
            page-break-inside: avoid;
        }}

        .total {{
            font-weight: bold;
            font-size: 11px;
            margin-top: 5mm;
            text-align: center;
            color: #000;
            letter-spacing: 0;
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
         <div class="image-column">
             <img src="{image_src}" alt="Rasm">
         </div>
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

    # PDF faylini yaratamiz
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()

    # Yaratilgan fayl uchun noyob nom (pdf-results papkasiga saqlanadi)
    random_filename = f"pdf-results/{uuid.uuid4()}.pdf"

    # BytesIO obyektiga aylantiramiz
    pdf_file_obj = BytesIO(pdf_bytes)

    # boto3 S3 clientini yaratamiz
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )

    # PDF faylini S3 bucketga, "pdf-results/" papkasiga yuklaymiz
    s3_client.upload_fileobj(
        pdf_file_obj,
        AWS_STORAGE_BUCKET_NAME,
        random_filename,
        ExtraArgs={'ContentType': 'application/pdf'}
    )

    # Yuklangan faylga URL olish (agar bucket ommaga ochiq bo'lsa)
    pdf_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{random_filename}"

    # PDF URL ni ma'lumotlar bazasiga saqlaymiz
    PDFResult.objects.create(
        user_id=data['id'],
        phone=data['phone'],
        pdf_url=pdf_url
    )

    return pdf_url
# End of snippet