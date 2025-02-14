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

    # Kategoriya bo‘yicha natijalarni ajratamiz
    majburiy_results = []
    fan1_results = []
    fan2_results = []

    # (Agar kerak bo'lsa, umumiy natija uchun hisoblash saqlanib qoladi)
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

    # Natijalarni raqam bo‘yicha tartiblash
    majburiy_results.sort(key=lambda x: int(x.get('number', 0)))
    fan1_results.sort(key=lambda x: int(x.get('number', 0)))
    fan2_results.sort(key=lambda x: int(x.get('number', 0)))

    def build_results_html(results):
        html = ""
        for test in results:
            status = str(test.get("status", "")).lower()
            if status == "true":
                symbol = '<img src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/chekvector.png" alt="True" style="width:12px;height:12px;vertical-align:text-top;">'
            else:
                symbol = '<img src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/crossvector.png" alt="False" style="width:12px;height:12px;vertical-align:text-top;">'
            html += f'<div class="result" style="margin:3px 0; font-size:14px;"><strong>{test.get("number")}.</strong> {test.get("option")} {symbol}</div>'
        return html

    def build_category_html(results):
        if not results:
            return ""
        # Endi kategoriya nomi ham chiqarilmaydi, faqat natijalar ko'rsatiladi
        html = '<div class="category-column" style="width:32%; box-sizing:border-box;">'
        html += build_results_html(results)
        html += '</div>'
        return html

    cat_columns = []
    if majburiy_results:
        cat_columns.append(build_category_html(majburiy_results))
    if fan1_results:
        cat_columns.append(build_category_html(fan1_results))
    if fan2_results:
        cat_columns.append(build_category_html(fan2_results))

    # Kategoriya ustunlari orasidagi oraliqni belgilash
    categories_html = '<div class="categories" style="display:flex; gap:5px; flex-wrap: wrap;">' + "".join(cat_columns) + '</div>'

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
          color: #333;
          margin: 0;
          padding: 0;
          background: #f9f9f9;
        }}
        .header {{
          position: relative;
          text-align: center;
          padding: 8px;
          background: #e0e0e0;
          border-bottom: 1px solid #ccc;
        }}

        .header img{{
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          height: 50px;
          filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.3));
        }}
        .footer {{
          text-align: center;
          padding: 8px;
          background: #e0e0e0;
          border-top: 1px solid #ccc;
          position: fixed;
          bottom: 0;
          width: 100%;
        }}
        .content {{
          display: flex;
          justify-content: space-between;
          box-sizing: border-box;
          margin-top: 10px;
          margin-bottom: 20px;
          gap: 10px;
        }}
        .left {{
          width: 59%;
          padding: 5px;
          text-align: left;
          margin-right:15px;
        }}
        .left img {{
          max-width: 100%;
          height: auto;
          object-fit: cover;
          box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        .right {{
          width: 40%;
          padding: 5px;
        }}
        .categories {{
          display: flex;
          gap: 5px;
          flex-wrap: wrap;
        }}
        .category-column {{
          padding: 5px;
          border-radius: 3px;
        }}
        .result {{
          margin: 3px 0;
          font-size: 14px;
        }}
        .result img {{
          width: 10px;
          height: 10px; 
          vertical-align: text-top;
        }}
      </style>
    </head>
    <body>
      <div class="header" ">
          <img src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/logo-titul.png" alt="Logo">
          <div>
            <h2>ID: {data['id']}</h2>
            <p>Telefon: {data['phone']}</p>
          </div>
        </div>
      <div class="content">
         <div class="left">
           <img src="{image_src}" alt="Rasm">
         </div>
         <div class="right">
           {categories_html}
         </div>
      </div>
      <div class="footer">
         <h3>Umumiy natija: {overall_total:.1f}</h3>
      </div>
    </body>
    </html>
    """

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
