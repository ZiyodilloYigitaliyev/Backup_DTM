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

    # Natijalarni kategoriya bo‘yicha ajratish va jami hisoblash
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

    # Ro'yxatlarni tartiblash
    majburiy_results = sorted(majburiy_results, key=lambda x: int(x.get('number', 0)))
    fan1_results = sorted(fan1_results, key=lambda x: int(x.get('number', 0)))
    fan2_results = sorted(fan2_results, key=lambda x: int(x.get('number', 0)))

    def build_results_html(results):
        html = ""
        for test in results:
            raw_status = test.get("status", "")
            status = str(raw_status).lower()
            if status == "true":
                symbol_html = (
                    '<div class="result-img-container">'
                    '<img class="result-img" src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/chekvector.png" alt="status">'
                    '</div>'
                )
            else:
                symbol_html = (
                    '<div class="result-img-container">'
                    '<img class="result-img" src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/crossvector.png" alt="status">'
                    '</div>'
                )
            html += f"""
            <div class="result">
                <span class="number">{test.get('number')}</span>.
                <span class="option">{test.get('option')}</span>
                {symbol_html}
            </div>
            """
        return html

    def build_category_html(title, results, total):
        if not results:
            return ""
        category_html = f'<div class="category-column"><h4>{title}</h4>'
        category_html += build_results_html(results)
        category_html += f'<div class="total">Jami: {total:.1f}</div></div>'
        return category_html

    columns_html = ""
    columns_html += build_category_html("Majburiy fan", majburiy_results, majburiy_total)
    columns_html += build_category_html("Fan 1", fan1_results, fan1_total)
    columns_html += build_category_html("Fan 2", fan2_results, fan2_total)

    # Sahifani grid bilan tashkil qilamiz: header, asosiy kontent va footer (hammasi bitta sahifada)
    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @page {{
            size: A4;
            margin: 10mm;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif; /* O'zgartiring */
            color: #333; /* Matn rangi */
        }}
        .header {{
            text-align: center;
            font-size: 12pt; /* Kattaroq sarlavha */
            padding: 5mm;
            background-color: #f0f0f0; /* Sarlavha fon rangi */
            border-bottom: 2px solid #ccc; /* Pastki chiziq */
        }}
        .footer {{
            text-align: center;
            font-size: 10pt;
            padding: 5mm;
            border-top: 1px solid #ccc; /* Yuqori chiziq */
        }}
        .container {{
            display: flex;
            align-items: stretch;
            height: calc(100% - 50mm); /* Header va footer balandligini hisobga olish */
        }}
        .image-column {{
            width: 40%;
            padding: 5mm;
            box-sizing: border-box;
            height: 100%;
            background-color: #fafafa; /* Rasm ustuni fon rangi */
            border-right: 1px solid #ccc; /* O'ng chiziq */
        }}
        .results-container {{
            width: 60%;
            padding: 5mm;
            box-sizing: border-box;
            overflow: hidden;
        }}
        .category-column {{
            margin-bottom: 10mm; /* Kategoriyalar orasidagi bo'sh joy */
            page-break-inside: avoid;
        }}
        .category-column h4 {{
            margin: 0;
            font-size: 11pt; /* Kattaroq sarlavha */
            text-align: left;
            color: #0056b3; /* Sarlavha rangi */
            border-bottom: 1px solid #ccc; /* Pastki chiziq */
            padding-bottom: 2mm; /* Pastki bo'sh joy */
        }}
        .result {{
            display: flex;
            align-items: center;
            gap: 5mm; /* Elementlar orasidagi bo'sh joy */
            font-size: 9pt; /* Kattaroq matn */
            margin: 2mm 0; /* Elementlar orasidagi bo'sh joy */
            page-break-inside: avoid;
        }}
        .number {{
            font-weight: bold;
        }}
        .option {{
            flex: 1;
        }}
        .result-img {{
            width: 8px; /* Katta ikonka */
            height: 8px; /* Katta ikonka */
            display: inline-block;
        }}
        .total {{
            font-weight: bold;
            font-size: 10pt; /* Kattaroq jami */
            text-align: right;
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
       <div class="footer">
           <h3>Umumiy natija: {overall_total:.1f}</h3>
       </div>
    </body>
    </html>
    """

    # PDF yaratish
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()
    random_filename = f"pdf-results/{uuid.uuid4()}.pdf"
    pdf_file_obj = BytesIO(pdf_bytes)

    s3_client = boto3.client(
         's3',
         aws_access_key_id=AWS_ACCESS_KEY_ID,
         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
         region_name=AWS_S3_REGION_NAME
    )

    s3_client.upload_fileobj(
         pdf_file_obj,
         AWS_STORAGE_BUCKET_NAME,
         random_filename,
         ExtraArgs={'ContentType': 'application/pdf'}
    )

    pdf_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{random_filename}"

    PDFResult.objects.create(
         user_id=data['id'],
         phone=data['phone'],
         pdf_url=pdf_url
    )

    return pdf_url
