# Antidote Billing System Implementation Guide

## Overview
The Antidote platform uses a simplified credit-based billing system with Razorpay payment gateway integration. Clinics can top up credits using various payment methods and promotional codes for discounts.

## Core Architecture

### Backend Components

#### 1. Simple Billing System (`simple_billing_system.py`)
- **Purpose**: Main billing logic with promotional code support
- **Key Features**:
  - Credit purchase with Razorpay integration
  - Promotional code validation and application
  - Payment verification and credit allocation
  - Transaction history tracking

#### 2. Models (`models.py`)
**CreditTransaction Model**:
```python
class CreditTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'credit', 'debit'
    description = db.Column(db.Text)
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**PromoCode Model**:
```python
class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    bonus_credits = db.Column(db.Float, default=0)
    min_amount = db.Column(db.Float, default=0)
    max_discount = db.Column(db.Float)
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
```

**PromoUsage Model**:
```python
class PromoUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promo_code.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transaction.id'))
    discount_amount = db.Column(db.Float, nullable=False)
    bonus_credits = db.Column(db.Float, default=0)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### 3. Clinic Routes (`clinic_routes.py`)
**Key Endpoints**:
- `/clinic/billing-dashboard` - Main billing dashboard
- `/clinic/credits/topup` - Credit top-up interface
- `/clinic/simple-purchase-credits` - Process credit purchase
- `/clinic/verify-payment` - Verify Razorpay payment
- `/clinic/check-promo-code` - Validate promotional codes

## Frontend Components

### 1. Main Templates

#### Billing Dashboard (`templates/clinic/billing_dashboard.html`)
- **Purpose**: Central hub for all billing activities
- **Features**:
  - Current credit balance display
  - Transaction history
  - Quick top-up options
  - Navigation to detailed billing features

#### Credit Top-up Interface (`templates/clinic/simple_credit_topup.html`)
- **Purpose**: Credit purchase interface with Razorpay integration
- **Features**:
  - Amount input with quick selection buttons
  - Promotional code application
  - Real-time payment summary calculation
  - Razorpay payment modal integration

### 2. JavaScript Integration

#### Razorpay Integration
```javascript
// Payment initiation
function initiatePayment(amount) {
    $.post('/clinic/simple-purchase-credits', {
        amount: amount,
        promo_code: appliedPromo ? appliedPromo.code : '',
        csrf_token: $('meta[name=csrf-token]').attr('content')
    })
    .done(function(response) {
        if (response.success) {
            openRazorpayCheckout(response);
        }
    });
}

// Razorpay modal opening
function openRazorpayCheckout(orderData) {
    const options = {
        key: orderData.key,
        amount: orderData.razorpay_amount,
        currency: 'INR',
        name: 'Antidote Clinic',
        description: `Add ₹${orderData.credits.toLocaleString()} Credits`,
        order_id: orderData.order_id,
        handler: function(response) {
            verifyPayment(response, orderData);
        }
    };
    
    const rzp = new window.Razorpay(options);
    rzp.open();
}
```

## API Endpoints

### 1. Credit Purchase Flow

#### POST `/clinic/simple-purchase-credits`
**Purpose**: Create Razorpay order for credit purchase
**Request Parameters**:
```json
{
    "amount": 1000,
    "promo_code": "SAVE20",
    "csrf_token": "token_value"
}
```

**Response**:
```json
{
    "success": true,
    "order_id": "order_xxxxxxxxx",
    "key": "rzp_test_xxxxxxxxx",
    "amount": 1000,
    "credits": 1000,
    "razorpay_amount": 100000,
    "currency": "INR"
}
```

#### POST `/clinic/verify-payment`
**Purpose**: Verify Razorpay payment and allocate credits
**Request Parameters**:
```json
{
    "razorpay_payment_id": "pay_xxxxxxxxx",
    "razorpay_order_id": "order_xxxxxxxxx",
    "razorpay_signature": "signature_value",
    "csrf_token": "token_value"
}
```

**Response**:
```json
{
    "success": true,
    "message": "Payment verified and credits added",
    "new_balance": 5000
}
```

### 2. Promotional Code Management

#### POST `/clinic/check-promo-code`
**Purpose**: Validate and calculate promotional code benefits
**Request Parameters**:
```json
{
    "code": "SAVE20",
    "amount": 1000,
    "csrf_token": "token_value"
}
```

**Response**:
```json
{
    "success": true,
    "discount": 200,
    "bonus_credits": 100,
    "message": "20% discount applied"
}
```

## Configuration

### Environment Variables
```bash
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxx
RAZORPAY_KEY_SECRET=your_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Database Migration
Run the following to ensure all tables exist:
```python
from app import app, db
with app.app_context():
    db.create_all()
```

## Payment Flow Sequence

1. **User Initiates Payment**
   - User enters amount and optional promo code
   - Frontend validates inputs and calculates final amount

2. **Order Creation**
   - Backend creates Razorpay order
   - Promotional code validation and discount calculation
   - Returns order details to frontend

3. **Payment Processing**
   - Frontend opens Razorpay payment modal
   - User completes payment (card/UPI/wallet)
   - Razorpay returns payment response

4. **Payment Verification**
   - Backend verifies payment signature
   - Creates credit transaction record
   - Updates clinic credit balance
   - Records promotional code usage

5. **Completion**
   - User sees success message
   - Updated balance reflected in dashboard

## Security Features

### CSRF Protection
- All forms include CSRF tokens
- Server validates tokens on each request

### Payment Signature Verification
```python
def verify_payment_signature(payment_id, order_id, signature, secret):
    generated_signature = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)
```

### Input Validation
- Amount validation (minimum/maximum limits)
- Promotional code existence and validity checks
- User authorization verification

## Error Handling

### Common Error Scenarios
1. **Razorpay Library Not Loaded**
   - Error: "Payment gateway not loaded"
   - Solution: Refresh page to reload JavaScript

2. **Payment Verification Failed**
   - Error: "Payment verification failed"
   - Solution: Contact support with payment details

3. **Promotional Code Issues**
   - Invalid/expired codes
   - Usage limit exceeded
   - Minimum amount not met

### Logging
All payment operations are logged with appropriate levels:
- INFO: Successful operations
- ERROR: Payment failures
- DEBUG: Detailed transaction flow

## Testing

### Test Payment Credentials
```
Test Card: 4111 1111 1111 1111
CVV: Any 3 digits
Expiry: Any future date
```

### Test Promotional Codes
The system includes sample promotional codes for testing:
- `SAVE20`: 20% discount
- `FLAT500`: ₹500 fixed discount
- `BONUS100`: 10% bonus credits

## Deployment Checklist

1. ✅ Environment variables configured
2. ✅ Database tables created
3. ✅ Razorpay webhook endpoints (if needed)
4. ✅ SSL certificate for payment security
5. ✅ Error monitoring setup
6. ✅ Backup procedures for financial data

## Monitoring and Analytics

### Key Metrics to Track
- Credit purchase volume
- Payment success/failure rates
- Promotional code usage
- Average transaction amounts
- User conversion rates

### Database Queries for Reporting
```sql
-- Monthly credit purchase summary
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as transactions,
    SUM(amount) as total_amount
FROM credit_transaction 
WHERE status = 'completed' 
GROUP BY month 
ORDER BY month;

-- Top promotional codes
SELECT 
    pc.code,
    COUNT(pu.id) as usage_count,
    SUM(pu.discount_amount) as total_discount
FROM promo_code pc
JOIN promo_usage pu ON pc.id = pu.promo_code_id
GROUP BY pc.code
ORDER BY usage_count DESC;
```

## Future Enhancements

### Planned Features
1. **Subscription Models**: Recurring payment options
2. **Credit Packages**: Bulk purchase discounts
3. **Referral System**: Credit rewards for referrals
4. **Advanced Analytics**: Detailed spending insights
5. **Multi-currency Support**: International payments

### Technical Improvements
1. **Webhook Integration**: Real-time payment status updates
2. **Automated Reconciliation**: Daily payment matching
3. **Advanced Fraud Detection**: Risk scoring algorithms
4. **Mobile App Integration**: Native payment flows

---

*This documentation covers the current implementation as of June 2025. For updates or technical support, contact the development team.*