from flask import Flask, render_template, request, redirect, url_for
import hashlib
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Sample inventory (you can connect to a real database like SQLite or PostgreSQL later)
inventory = {
    'Whole Chicken': 50,
    'Chicken Wings': 30,
    'Chicken Thighs': 20,
    'Chicken Breasts': 15
}

# Route for the homepage
@app.route("/")
def index():
    return render_template("index.html")

# Route for success after payment
@app.route("/success", methods=["GET"])
def success():
    return """
        <h1>Payment Successful!</h1>
        <p>Thank you for your order. We are processing your chicken order.</p>
    """

# Route for canceled payments
@app.route("/cancel", methods=["GET"])
def cancel():
    return """
        <h1>Payment Canceled</h1>
        <p>Your order was not completed. Please try again.</p>
    """

# Route to receive IPN notifications from PayFast
@app.route("/notify", methods=["POST"])
def notify():
    ipn_data = request.form
    print("Payment Notification:", ipn_data)
    
    # Verifying payment status (for illustration)
    if verify_ipn_checksum(ipn_data):
        # Handle successful payment here, e.g., reduce inventory
        update_inventory(ipn_data.get('item_name'), ipn_data.get('amount'))
        send_confirmation_email(ipn_data.get('email_address'), ipn_data.get('item_name'))

    return "Notification received", 200

# Function to update inventory after an order
def update_inventory(item_name, quantity):
    if inventory.get(item_name, 0) >= quantity:
        inventory[item_name] -= quantity
        print(f"Inventory updated: {item_name} - {quantity}kg sold")
    else:
        print(f"Not enough stock for {item_name}")

# Function to verify IPN checksum
def verify_ipn_checksum(ipn_data):
    checksum = hashlib.md5(f"merchant_key=46f0cd694581a&{sorted(ipn_data)}".encode()).hexdigest()
    return checksum == ipn_data.get('signature', '')

# Send confirmation email to customer
def send_confirmation_email(customer_email, order_details):
    msg = MIMEText(f"Thank you for your order: {order_details}")
    msg['Subject'] = 'Your Chicken Order Confirmation'
    msg['From'] = 'yourbusiness@example.com'
    msg['To'] = customer_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'your_email_password')
        server.sendmail('your_email@example.com', customer_email, msg.as_string())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
