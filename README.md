# 🛒 Smart Shopping Cart System

A smart retail shopping cart that automates product identification, weight verification, cart management, and digital payment. The system combines barcode scanning with load-cell-based weight validation to reduce manual billing and improve the shopping experience.

## 📌 Project Overview

Traditional supermarket billing involves manual checkout, which can lead to long queues and billing errors.

Our Smart Shopping Cart System allows customers to scan product barcodes, verify products using weight measurements, manage their cart in real time, and complete payments through Razorpay.

The system integrates hardware and software components to provide an automated shopping experience.

## ✨ Key Features

- **Barcode Scanning:** Identifies products using their unique barcodes.
- **Weight-Based Validation:** Verifies scanned products using actual weight measurements.
- **Real-Time Cart Management:** Automatically updates cart items, quantities, and prices.
- **Sensor Calibration:** Uses multiple weight readings and median-based measurement to improve stability.
- **Tolerance-Based Verification:** Allows acceptable weight variation during product validation.
- **Voice Alerts:** Provides audio notifications for item addition and weight mismatch.
- **Product Recommendations:** Displays recommended products through the recommendation API.
- **Online Payment:** Integrates Razorpay for digital payments.
- **PDF Receipt Generation:** Generates downloadable billing receipts using ReportLab.
- **Admin Panel:** Allows administrators to add products, calibrate weights, and manage product quantities.

## 🛠️ Technologies Used

<img width="856" height="538" alt="image" src="https://github.com/user-attachments/assets/b07579a2-2c8f-41f3-a859-35d99d409768" />


### Python Libraries

- `streamlit` – User interface and application dashboard.
- `fastapi` – Backend API development.
- `requests` – HTTP communication between frontend and backend.
- `pandas` – Product and order data handling.
- `statistics` – Median-based weight measurement.
- `collections` – Managing sensor readings using deque.
- `gtts` – Text-to-speech voice alerts.
- `base64` – Encoding audio for browser playback.
- `reportlab` – Generating downloadable PDF receipts.
- `io` – Creating PDF files in memory using BytesIO.

## ⚙️ System Workflow

1. Customer scans a product barcode.
2. The barcode is sent to the FastAPI backend.
3. Product information and expected weight are retrieved from MySQL.
4. Arduino reads the load-cell measurements through HX711.
5. Weight readings are transferred to the backend.
6. Multiple readings are collected and processed to reduce fluctuations.
7. The measured weight is compared with the expected weight using a tolerance range.
8. If the weight matches, the product is added to the cart.
9. Streamlit displays updated cart information.
10. The customer completes payment through Razorpay.
11. A digital receipt is generated and can be downloaded as a PDF.

## ⚖️ Weight Validation Technique

The system uses multiple sensor readings instead of depending on a single reading.

- Collects multiple weight measurements.
- Uses median-based readings for more stable calibration.
- Collects 10 weight-difference readings during product validation.
- Removes extreme readings before calculating the average.
- Uses a 15% tolerance range during product addition.

This helps reduce false mismatch detections caused by sensor fluctuations.

## 💳 Payment Integration

Razorpay is integrated into the cart checkout process.

1. The frontend requests order creation from FastAPI.
2. The backend returns the Razorpay order ID and amount.
3. Razorpay Checkout JavaScript opens the payment interface.
4. After successful payment, the frontend sends a confirmation request to the backend.
5. The user is redirected to the receipt page.

## 🧾 PDF Receipt Generation

The project uses **ReportLab** to dynamically generate PDF receipts.

- Retrieves order details from the backend.
- Displays order ID, date, product details, quantities, and total amount.
- Creates a formatted PDF using ReportLab.
- Uses BytesIO to generate the PDF in memory.
- Provides a Streamlit download button.

## 🚀 Future Enhancements

- Computer vision for product identification.
- Improved sensor calibration and measurement accuracy.
- Cloud-based deployment.
- Mobile application integration.
- Advanced personalized product recommendations.

## Results
<img width="1600" height="635" alt="image" src="https://github.com/user-attachments/assets/077f5fe5-f9a7-4228-9cd8-97949d251b17" />
<img width="1600" height="737" alt="image" src="https://github.com/user-attachments/assets/dc496679-96cd-45c7-9464-fda46237438b" />
<img width="1600" height="720" alt="image" src="https://github.com/user-attachments/assets/fd615c6a-539a-477e-9f9d-5ee1051c609f" />
<img width="1600" height="644" alt="image" src="https://github.com/user-attachments/assets/8d1a9e83-9d0b-4346-94b1-7efff2907ffb" />


## 🎯 Applications

- Supermarkets
- Hypermarkets
- Retail stores
- Automated checkout systems

## 👩‍💻 Project Domain

IoT | Retail Automation | Embedded Systems | Web Application Development
