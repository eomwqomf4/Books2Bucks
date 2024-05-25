from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

def fetch_book_price(isbn):
    url = f"https://example.com/search?q={isbn}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    price_element = soup.find('span', class_='book-price')
    if price_element:
        price = float(price_element.text.strip('$'))
        return price
    return None

def send_email(subject, body, to_email):
    from_email = "your_email@gmail.com"
    from_password = "your_password"
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_price', methods=['POST'])
def check_price():
    contact_info = request.form.get('contact_info')
    if not contact_info:
        return jsonify({'error': 'Contact information is required'}), 400

    if 'isbn_text' in request.form:
        isbn_input = request.form['isbn_text']
    elif 'isbn_photo' in request.files:
        isbn_photo = request.files['isbn_photo']
        image = Image.open(isbn_photo)
        isbn_input = pytesseract.image_to_string(image)
    else:
        return jsonify({'error': 'No input provided'}), 400

    isbns = re.findall(r'\b\d{10}\b|\b\d{13}\b', isbn_input)
    if not isbns:
        return jsonify({'error': 'No valid ISBN found'}), 400

    results = []
    for isbn in isbns:
        price = fetch_book_price(isbn)
        if price:
            threshold_price = price * 0.3
            is_valid = threshold_price >= 25
            results.append({'isbn': isbn, 'price': price, 'is_valid': is_valid})
        else:
            results.append({'isbn': isbn, 'error': 'Price not found'})

    result_str = '\n'.join([f"ISBN: {res['isbn']}, Price: {res.get('price', 'N/A')}, Valid: {res.get('is_valid', 'N/A')}" for res in results])
    email_body = f"Contact Info: {contact_info}\n\n{result_str}"
    send_email('Books2Bucks Results', email_body, 'pelican193972@gmail.com')

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
