# Billing System Code Reference

## Implementation Files

### Core Billing Logic Files

#### 1. `integrated_billing_system.py`
**File Type**: Flask Blueprint  
**Purpose**: Main billing service and credit management  
**Size**: ~450 lines  
**Key Components**:
- `BillingService` class with static methods
- Blueprint registration as `billing_bp`
- Database operations for credit transactions

**Routes Defined**:
```python
@billing_bp.route('/billing-dashboard')
@billing_bp.route('/credits/topup', methods=['GET', 'POST'])
@billing_bp.route('/credits/history')
@billing_bp.route('/credits/balance')
```

**Key Methods**:
```python
BillingService.get_clinic_credit_balance(clinic_id)
BillingService.deduct_credits_for_lead(clinic_id, lead_cost, lead_id)
BillingService.add_credits(clinic_id, amount, description)
BillingService.calculate_lead_cost(package_price)
```

#### 2. `enhanced_credit_billing.py`
**File Type**: Flask Blueprint  
**Purpose**: Razorpay payment integration  
**Size**: ~400 lines  
**Key Components**:
- Razorpay client initialization
- Payment order creation and verification
- Blueprint registration as `enhanced_credit_bp`

**Routes Defined**:
```python
@enhanced_credit_bp.route('/create-razorpay-order', methods=['POST'])
@enhanced_credit_bp.route('/verify-payment', methods=['POST'])
@enhanced_credit_bp.route('/payment-success')
@enhanced_credit_bp.route('/payment-failure')
```

**Environment Dependencies**:
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

#### 3. `lead_disputes_system.py`
**File Type**: Flask Blueprint  
**Purpose**: Lead quality management and disputes  
**Size**: ~350 lines  
**Key Components**:
- Dispute creation and resolution
- Admin dispute management
- Automatic refund processing
- Blueprint registration as `disputes_bp`

**Routes Defined**:
```python
@disputes_bp.route('/disputes')
@disputes_bp.route('/disputes/create/<int:lead_id>', methods=['GET', 'POST'])
@disputes_bp.route('/disputes/<int:dispute_id>/cancel', methods=['POST'])
# Admin routes
@admin_disputes_bp.route('/admin/disputes')
@admin_disputes_bp.route('/admin/disputes/<int:dispute_id>/resolve', methods=['POST'])
```

#### 4. `enhanced_lead_generation.py`
**File Type**: Flask Blueprint  
**Purpose**: Lead capture with integrated billing  
**Size**: ~300 lines  
**Key Components**:
- Enhanced lead submission with billing
- Automatic credit deduction
- Integration with existing lead flow
- Blueprint registration as `enhanced_lead_bp`

**Routes Defined**:
```python
@enhanced_lead_bp.route('/contact-clinic', methods=['POST'])
@enhanced_lead_bp.route('/clinic/leads/update-status', methods=['POST'])
```

### Enhanced Existing Files

#### 5. `clinic_routes.py` (Modified)
**Modifications Made**:
- Enhanced `clinic_dashboard()` function (lines 1334-1413)
- Added credit balance retrieval
- Integrated billing metrics
- Added transaction history

**Key Changes**:
```python
# Lines 1352-1358: Credit balance integration
try:
    from integrated_billing_system import BillingService
    credit_balance = BillingService.get_clinic_credit_balance(clinic['id'])
except Exception as e:
    logger.warning(f"Error getting credit balance: {e}")
    credit_balance = 0

# Lines 1376-1408: Enhanced dashboard data
recent_transactions_result = db.session.execute(text("SELECT * FROM credit_transactions WHERE clinic_id = :clinic_id ORDER BY created_at DESC LIMIT 15"), {'clinic_id': clinic['id']}).fetchall()
```

#### 6. `routes.py` (Modified)
**Modifications Made**:
- Added blueprint registrations (lines ~6000-6100)
- Integrated billing system with main application

**Key Additions**:
```python
# Billing system registrations
app.register_blueprint(billing_bp, url_prefix='/clinic')
app.register_blueprint(disputes_bp, url_prefix='/clinic') 
app.register_blueprint(enhanced_lead_bp, url_prefix='/')
app.register_blueprint(enhanced_credit_bp, url_prefix='/')
```

## Template Files

### Main Templates

#### 1. `templates/clinic/billing_dashboard.html`
**File Type**: Jinja2 Template  
**Purpose**: Complete billing dashboard interface  
**Size**: ~600 lines  
**Key Sections**:
- Credit balance display
- Transaction history table
- Top-up functionality
- Analytics charts
- Dispute management links

**Template Variables Required**:
```python
{
    'clinic': clinic_data,
    'credit_balance': float,
    'recent_transactions': list,
    'monthly_spending': float,
    'total_leads': int,
    'dispute_count': int
}
```

#### 2. `templates/clinic/dashboard.html` (Enhanced)
**Modifications Made**:
- Added credit balance in header (lines 30-41)
- Added low balance alerts (lines 94-115)
- Added billing tab (lines 125-129)
- Added billing overview section (lines 277-439)

**New Template Sections**:
```html
<!-- Credit Balance Header -->
<div class="credit-balance">
    <div class="credit-amount">₹{{ "{:,.0f}".format(clinic.credit_balance or 0) }}</div>
    <div class="credit-label">Available Credits</div>
</div>

<!-- Billing Tab Content -->
<div class="tab-pane fade" id="billing" role="tabpanel">
    <!-- Billing overview cards and transaction history -->
</div>
```

#### 3. `templates/clinic/credit_topup.html`
**File Type**: Jinja2 Template  
**Purpose**: Credit purchase interface  
**Size**: ~400 lines  
**Key Features**:
- Credit package selection
- Razorpay payment integration
- Payment status handling

#### 4. `templates/clinic/disputes.html`
**File Type**: Jinja2 Template  
**Purpose**: Dispute management interface  
**Size**: ~350 lines  
**Key Features**:
- Dispute creation form
- Dispute listing and status
- Evidence upload capability

#### 5. `templates/admin/disputes.html`
**File Type**: Jinja2 Template  
**Purpose**: Admin dispute resolution  
**Size**: ~300 lines  
**Key Features**:
- Dispute review interface
- Resolution actions
- Refund processing

## Database Schema

### New Tables Created

#### Credit Transactions Table
```sql
-- Table: credit_transactions
CREATE TABLE credit_transactions (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER REFERENCES clinics(id),
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'credit', 'deduction', 'refund'
    description TEXT,
    lead_id INTEGER REFERENCES leads(id),
    payment_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_credit_transactions_clinic_id ON credit_transactions(clinic_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at);
```

#### Lead Disputes Table
```sql
-- Table: lead_disputes
CREATE TABLE lead_disputes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    clinic_id INTEGER REFERENCES clinics(id),
    dispute_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    admin_notes TEXT,
    refund_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_lead_disputes_clinic_id ON lead_disputes(clinic_id);
CREATE INDEX idx_lead_disputes_status ON lead_disputes(status);
```

## Route Mapping

### Complete Route List

#### Clinic Billing Routes (`/clinic/` prefix)
```
GET  /clinic/billing-dashboard          → billing_dashboard()
GET  /clinic/credits/topup             → credit_topup()
POST /clinic/credits/topup             → process_credit_topup()
GET  /clinic/credits/history           → credit_history()
GET  /clinic/credits/balance           → get_credit_balance()
```

#### Payment Processing Routes
```
POST /create-razorpay-order            → create_razorpay_order()
POST /verify-payment                   → verify_payment()
GET  /payment-success                  → payment_success()
GET  /payment-failure                  → payment_failure()
```

#### Dispute Management Routes (`/clinic/` prefix)
```
GET  /clinic/disputes                  → disputes_dashboard()
GET  /clinic/disputes/create/<int:lead_id>  → create_dispute()
POST /clinic/disputes/create/<int:lead_id>  → submit_dispute()
POST /clinic/disputes/<int:dispute_id>/cancel  → cancel_dispute()
```

#### Lead Generation Routes
```
POST /contact-clinic                   → enhanced_contact_clinic()
POST /clinic/leads/update-status       → update_lead_status()
```

#### Admin Routes
```
GET  /admin/disputes                   → admin_disputes()
POST /admin/disputes/<int:dispute_id>/resolve  → resolve_dispute()
```

#### Enhanced Existing Routes
```
GET  /clinic/dashboard                 → clinic_dashboard() [Enhanced with billing]
```

## JavaScript Integration

### Frontend Files

#### Billing Dashboard JavaScript
**Location**: Embedded in `templates/clinic/billing_dashboard.html`  
**Key Functions**:
```javascript
function openTopUpModal()              // Open credit purchase modal
function loadTransactionHistory()      // Load transaction data
function updateCreditBalance()         // Refresh balance display
function initializeCharts()           // Setup analytics charts
```

#### Payment Integration JavaScript
**Location**: Embedded in `templates/clinic/credit_topup.html`  
**Key Functions**:
```javascript
function initiateRazorpayPayment()     // Start payment process
function handlePaymentSuccess()        // Success callback
function handlePaymentFailure()        // Failure callback
```

## API Integration Points

### External Services

#### Razorpay Integration
**Files Involved**:
- `enhanced_credit_billing.py` (Backend)
- `templates/clinic/credit_topup.html` (Frontend)

**API Endpoints Used**:
- Order Creation: `orders.create()`
- Payment Verification: `utility.verify_payment_signature()`

**Required Credentials**:
- Razorpay Key ID (Public)
- Razorpay Key Secret (Private)

### Internal API Endpoints

#### Billing Service API
```python
# Credit balance check
GET /clinic/credits/balance
Response: {"balance": 1500.00, "status": "success"}

# Transaction history
GET /clinic/credits/history?page=1&limit=20
Response: {"transactions": [...], "total": 45, "page": 1}
```

## Configuration Requirements

### Environment Variables
```bash
# Required for payment processing
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxx

# Database connection
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### Application Configuration
```python
# In main application file
from integrated_billing_system import billing_bp
from enhanced_credit_billing import enhanced_credit_bp
from lead_disputes_system import disputes_bp
from enhanced_lead_generation import enhanced_lead_bp

# Register blueprints
app.register_blueprint(billing_bp, url_prefix='/clinic')
app.register_blueprint(enhanced_credit_bp, url_prefix='/')
app.register_blueprint(disputes_bp, url_prefix='/clinic')
app.register_blueprint(enhanced_lead_bp, url_prefix='/')
```

## Testing and Debugging

### Key Log Points
```python
# Billing operations
logger.info(f"Credit deduction: Clinic {clinic_id}, Amount {amount}")
logger.error(f"Payment verification failed: {error}")

# Dispute processing
logger.info(f"Dispute created: Lead {lead_id}, Type {dispute_type}")
logger.info(f"Dispute resolved: {dispute_id}, Refund {refund_amount}")
```

### Testing Endpoints
```bash
# Test credit balance
curl -X GET "http://localhost:5000/clinic/credits/balance" \
  -H "Authorization: Bearer <token>"

# Test payment creation
curl -X POST "http://localhost:5000/create-razorpay-order" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000}'
```

## Performance Considerations

### Database Indexes
```sql
-- Critical indexes for billing performance
CREATE INDEX idx_credit_transactions_clinic_created ON credit_transactions(clinic_id, created_at DESC);
CREATE INDEX idx_leads_clinic_created ON leads(clinic_id, created_at DESC);
CREATE INDEX idx_disputes_status_created ON lead_disputes(status, created_at DESC);
```

### Caching Strategy
- Credit balances cached for 5 minutes
- Transaction history paginated (20 per page)
- Dispute counts cached for 10 minutes

## Security Measures

### Payment Security
- Razorpay signature verification
- CSRF token validation
- Secure payment ID storage

### Access Control
- Clinic-specific data isolation
- Admin-only dispute resolution
- Authenticated route protection

This reference document provides complete details for developers to understand, maintain, and extend the billing system implementation.