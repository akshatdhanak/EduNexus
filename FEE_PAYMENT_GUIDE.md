# Fee Operations & Razorpay Payment Integration Guide

## Overview

The system now includes comprehensive fee operations with Razorpay payment gateway integration.

## Features Implemented

### 1. **Fee Dashboard for Students**

- View semester-wise fee breakdown
- Track: Fees to be collected, Previously paid, Paid, Outstanding
- View payment receipts with payment mode and reference details
- Link: http://127.0.0.1:8000/student_app/fee_dashboard/

### 2. **Razorpay Payment Integration**

- **Supported Payment Methods:**
  - Credit/Debit Cards (Visa, Mastercard, RuPay)
  - Net Banking (All major banks)
  - UPI (GPay, PhonePe, Paytm, etc.)
  - Wallets (Paytm, PhonePe, Amazon Pay, etc.)

### 3. **Payment Flow**

1. Student views fee dashboard
2. Clicks "Pay Now" button for semester with outstanding fees
3. Redirected to secure Razorpay payment page
4. Completes payment via preferred method
5. Automatic receipt generation
6. Fee structure updated with paid amount

## Setup Instructions

### Step 1: Get Razorpay API Keys

1. Sign up at https://razorpay.com/
2. Go to Dashboard → Settings → API Keys
3. Generate Test/Live Keys
4. Copy **Key ID** and **Key Secret**

### Step 2: Configure Razorpay Keys

Edit `/project1/settings.py` and replace the placeholder values:

```python
# Razorpay Configuration
RAZORPAY_KEY_ID = 'rzp_test_xxxxxxxxxxxxx'  # Replace with your Key ID
RAZORPAY_KEY_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxx'  # Replace with your Key Secret
```

**Important:**

- Use **Test Keys** (start with `rzp_test_`) for development
- Use **Live Keys** (start with `rzp_live_`) for production
- Keep the secret key secure and never commit it to public repositories

### Step 3: Add Fee Structure for Students

#### Method 1: Django Admin Panel

1. Go to http://127.0.0.1:8000/admin/
2. Navigate to **Admin_app → Fee structures**
3. Click **Add Fee Structure**
4. Fill in:
   - **Student**: Select the student
   - **Semester**: 1-8
   - **Fees to be collected**: Enter amount (e.g., 50000)
   - **Refunded**: 0 (default)
   - **Previously paid**: 0 (default)
   - **Paid**: 0 (default)
   - **Outstanding**: Auto-calculated on save
5. Click **Save**

#### Method 2: Python Shell (Bulk Creation)

```bash
python manage.py shell
```

```python
from admin_app.models import Student, FeeStructure

# Get a student
student = Student.objects.first()

# Create fee structure for all semesters
for semester in range(1, 9):
    FeeStructure.objects.create(
        student=student,
        semester=semester,
        fees_to_be_collected=50000,  # Adjust amount as needed
        paid=0,
        outstanding=50000
    )

print("Fee structure created for all semesters!")
```

### Step 4: Test Payment Flow

#### Using Test Mode:

1. Set test keys in settings.py
2. Go to fee dashboard as student
3. Click "Pay Now" for any semester
4. Use Razorpay test card details:
   - **Card Number**: 4111 1111 1111 1111
   - **CVV**: Any 3 digits
   - **Expiry**: Any future date
5. Complete payment
6. Verify receipt is generated

## Payment Methods Details

### 1. **Online (Razorpay)**

- Instant payment processing
- Multiple payment options
- Automatic receipt generation
- Reference No: Razorpay Payment ID
- Reference Bank: Razorpay

### 2. **Cash** (Admin Entry)

- Recorded manually by admin
- No reference details required

### 3. **RTGS/NEFT** (Admin Entry)

- Bank transfer details
- Reference No: Transaction ID
- Reference Date: Transfer date
- Reference Bank: Bank name

### 4. **Card** (Admin Entry)

- Card payment at office
- Reference No: Transaction ID

### 5. **Cheque** (Admin Entry)

- Cheque details
- Reference No: Cheque number
- Reference Date: Cheque date
- Reference Bank: Bank name

## Admin Operations

### Adding Manual Receipts

1. Go to Django Admin → Fee Receipts
2. Click **Add Fee Receipt**
3. Fill in:
   - Student
   - Fee structure (select semester)
   - Receipt No (auto or manual)
   - Date
   - Payment Mode
   - Reference details (if applicable)
   - Amount
4. Save

### Viewing Payment History

- Admin can view all receipts: http://127.0.0.1:8000/admin/admin_app/feereceipt/
- Filter by student, semester, payment mode, date

### Generating Reports

- Use Django admin filters to export payment data
- Filter by date range, payment mode, student

## Security Features

1. **CSRF Protection**: All forms protected
2. **Authentication Required**: Only logged-in students can pay
3. **Payment Verification**: Razorpay signature verification (optional)
4. **Secure Keys**: API keys stored in settings, not in code
5. **HTTPS Required**: Use HTTPS in production for secure payments

## Testing Payment Integration

### Test Cards (Razorpay Test Mode):

**Success:**

- Card: 4111 1111 1111 1111
- CVV: Any 3 digits
- Expiry: Any future date

**Failure:**

- Card: 4000 0000 0000 0002

**UPI:**

- UPI ID: success@razorpay

## Troubleshooting

**Problem**: Payment button not working
**Solution**:

1. Check Razorpay keys are set correctly
2. Verify razorpay package is installed: `pip install razorpay`
3. Check browser console for JavaScript errors

**Problem**: Payment successful but receipt not created
**Solution**:

1. Check payment_success view for errors
2. Verify FeeStructure exists for that semester
3. Check Django logs for exceptions

**Problem**: "Authentication Error" from Razorpay
**Solution**:

1. Verify Key ID and Secret are correct
2. Check if using test keys for test mode
3. Ensure keys have no extra spaces

## Production Deployment

Before going live:

1. **Switch to Live Keys**:

   ```python
   RAZORPAY_KEY_ID = 'rzp_live_xxxxxxxxxxxxx'
   RAZORPAY_KEY_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxx'
   ```

2. **Enable HTTPS**: Razorpay requires HTTPS in production

3. **Set DEBUG = False** in settings.py

4. **Add Webhook** (optional but recommended):
   - Go to Razorpay Dashboard → Webhooks
   - Add endpoint: `https://yourdomain.com/payment_webhook/`
   - Select events: payment.captured, payment.failed

5. **Test thoroughly** with live keys in test environment first

## File Structure

```
├── student_app/
│   ├── views.py (pay_fees, payment_success, payment_failure)
│   ├── urls.py (payment routes)
│   └── templates/
│       └── student_app/
│           ├── fee_dashboard.html (main dashboard)
│           └── payment_page.html (Razorpay checkout)
├── admin_app/
│   └── models.py (FeeStructure, FeeReceipt models)
└── project1/
    └── settings.py (Razorpay configuration)
```

## Access Points

- **Student Fee Dashboard**: http://127.0.0.1:8000/student_app/fee_dashboard/
- **Payment Page**: Automatic redirect from "Pay Now" button
- **Admin Fee Operations**: http://127.0.0.1:8000/admin/admin_app/feestructure/
- **Admin Receipts**: http://127.0.0.1:8000/admin/admin_app/feereceipt/

## Support

For Razorpay integration issues:

- Documentation: https://razorpay.com/docs/
- Support: https://razorpay.com/support/

For system issues, check Django logs and error messages.
