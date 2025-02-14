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
            status = str(test.get("status", "")).lower()
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

    # Sahifani yonma-yon bo'luvchi tartibda tashkil etamiz
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
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            color: #333;
        }}
        .header, .footer {{
            text-align: center;
            padding: 10px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
        }}
        .container {{
            display: flex;
            height: calc(100vh - 80px);
        }}
        .image-column {{
            width: 60%;
            padding: 10px;
            box-sizing: border-box;
            border-right: 1px solid #ccc;
        }}
        .image-column img {{
            width: 100%;
            height: auto;
            object-fit: contain;
        }}
        .results-container {{
            width: 40%;
            padding: 10px;
            box-sizing: border-box;
            overflow-y: auto;
        }}
        .category-column {{
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}
        .category-column h4 {{
            margin: 0 0 5px;
            font-size: 16px;
            color: #0056b3;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }}
        .result {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 14px;
            page-break-inside: avoid;
        }}
        .number {{
            font-weight: bold;
            margin-right: 5px;
        }}
        .option {{
            flex: 1;
        }}
        .result-img {{
            width: 12px;
            height: 12px;
        }}
        .total {{
            font-weight: bold;
            text-align: right;
            margin-top: 10px;
            font-size: 16px;
        }}
      </style>
    </head>
    <body>
       <div class="header">
           <h2>ID: {data['id']}</h2>
           <p>Telefon: {data['phone']}</p>
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
