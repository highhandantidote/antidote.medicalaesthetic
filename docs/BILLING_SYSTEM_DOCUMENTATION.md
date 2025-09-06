# Antidote Prepaid Credit Billing System Documentation

## Overview
This document provides comprehensive documentation for the prepaid credit billing system implemented for the Antidote medical aesthetic marketplace platform. The system allows clinics to purchase credits and pay for patient leads based on dynamic pricing tiers.

## System Architecture

### Core Components
1. **Integrated Billing System** - Main billing logic and credit management
2. **Lead Generation with Billing** - Lead capture with automatic credit deduction
3. **Lead Disputes System** - Quality control and refund management
4. **Enhanced Credit Billing** - Razorpay payment integration
5. **Clinic Dashboard Integration** - UI for credit management

## File Structure and Implementation

### 1. Core Billing Files

#### `integrated_billing_system.py`
**Purpose**: Main billing service with credit management logic
**Key Classes**:
- `BillingService`: Core billing operations
- `CreditTransaction`: Database model for transactions

**Key Methods**:
- `get_clinic_credit_balance(clinic_id)` - Get current credit balance
- `deduct_credits_for_lead(clinic_id, lead_cost, lead_id)` - Automatic deduction
- `add_credits(clinic_id, amount, description)` - Credit top-up
- `calculate_lead_cost(package_price)` - Dynamic pricing calculation

**Routes**:
- `/clinic/billing-dashboard` - Main billing dashboard
- `/clinic/credits/topup` - Credit purchase page
- `/clinic/credits/history` - Transaction history

#### `enhanced_credit_billing.py`
**Purpose**: Razorpay payment integration and credit purchasing
**Key Features**:
- Razorpay order creation
- Payment verification
- Automatic credit addition after successful payment

**Routes**:
- `/create-razorpay-order` - Create payment order
- `/verify-payment` - Verify and process payment
- `/payment-success` - Success callback
- `/payment-failure` - Failure callback

#### `lead_disputes_system.py`
**Purpose**: Lead quality management and dispute resolution
**Key Features**:
- Dispute creation and tracking
- Automatic refunds for approved disputes
- Quality scoring system

**Routes**:
- `/clinic/disputes` - Dispute management dashboard
- `/clinic/disputes/create/<int:lead_id>` - Create new dispute
- `/admin/disputes` - Admin dispute review
- `/admin/disputes/<int:dispute_id>/resolve` - Resolve disputes

#### `enhanced_lead_generation.py`
**Purpose**: Lead capture with integrated billing
**Key Features**:
- Automatic credit deduction on lead generation
- Dynamic pricing based on package value
- Integration with existing lead flow

**Routes**:
- `/contact-clinic` - Lead submission with billing
- `/clinic/leads/update-status` - Lead status updates

### 2. Database Models

#### Credit Transactions Table
```sql
CREATE TABLE credit_transactions (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER REFERENCES clinics(id),
    amount DECIMAL(10,2),
    transaction_type VARCHAR(20), -- 'credit', 'deduction', 'refund'
    description TEXT,
    lead_id INTEGER REFERENCES leads(id),
    payment_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Lead Disputes Table
```sql
CREATE TABLE lead_disputes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    clinic_id INTEGER REFERENCES clinics(id),
    dispute_type VARCHAR(50),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT,
    refund_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
```

### 3. Template Files

#### `templates/clinic/billing_dashboard.html`
**Purpose**: Main billing dashboard for clinics
**Features**:
- Credit balance display
- Transaction history
- Top-up functionality
- Dispute management

#### `templates/clinic/dashboard.html` (Enhanced)
**Purpose**: Integrated clinic dashboard with billing tab
**New Features**:
- Credit balance in header
- Low balance alerts
- Billing tab with pricing tiers
- Recent transactions summary

#### `templates/clinic/credit_topup.html`
**Purpose**: Credit purchase interface
**Features**:
- Razorpay payment integration
- Credit package selection
- Payment status handling

#### `templates/clinic/disputes.html`
**Purpose**: Lead dispute management
**Features**:
- Dispute creation form
- Dispute status tracking
- Refund history

### 4. Route Integration

#### Main Route File: `routes.py`
**Billing System Registration**:
```python
# Integrated billing system
app.register_blueprint(billing_bp, url_prefix='/clinic')

# Lead disputes system  
app.register_blueprint(disputes_bp, url_prefix='/clinic')

# Enhanced lead generation with billing
app.register_blueprint(enhanced_lead_bp, url_prefix='/')

# Enhanced credit billing with Razorpay
app.register_blueprint(enhanced_credit_bp, url_prefix='/')
```

#### Clinic Routes: `clinic_routes.py` (Enhanced)
**Billing Integration**:
- Enhanced `clinic_dashboard()` with credit balance
- Added billing metrics and transaction data
- Integrated billing navigation

## Dynamic Pricing Tiers

### Pricing Structure
The system uses 6 dynamic pricing tiers based on package value:

| Package Price Range | Credit Cost | Usage Scenario |
|-------------------|-------------|----------------|
| < ₹5,000 | 100 Credits | Basic treatments |
| ₹5,000 - ₹10,000 | 180 Credits | Standard procedures |
| ₹10,000 - ₹20,000 | 250 Credits | Mid-range treatments |
| ₹20,000 - ₹50,000 | 320 Credits | Premium procedures |
| ₹50,000 - ₹100,000 | 400 Credits | High-value treatments |
| ₹100,000+ | 500 Credits | Luxury procedures |

### Implementation Logic
```python
def calculate_lead_cost(package_price):
    if package_price < 5000:
        return 100
    elif package_price < 10000:
        return 180
    elif package_price < 20000:
        return 250
    elif package_price < 50000:
        return 320
    elif package_price < 100000:
        return 400
    else:
        return 500
```

## Payment Integration

### Razorpay Setup
**Environment Variables Required**:
- `RAZORPAY_KEY_ID` - Public key for frontend
- `RAZORPAY_KEY_SECRET` - Secret key for backend verification

**Payment Flow**:
1. User selects credit package
2. Razorpay order created on backend
3. Payment processed on frontend
4. Payment verified on backend
5. Credits added to clinic account

### Credit Packages
Standard credit packages offered:
- ₹1,000 = 1,000 Credits
- ₹5,000 = 5,500 Credits (10% bonus)
- ₹10,000 = 11,500 Credits (15% bonus)
- ₹25,000 = 30,000 Credits (20% bonus)
- ₹50,000 = 62,500 Credits (25% bonus)

## Lead Dispute System

### Dispute Types
1. **Invalid Contact** - Wrong/fake contact information
2. **Duplicate Lead** - Same lead generated multiple times
3. **Poor Quality** - Lead doesn't match requirements
4. **Technical Error** - System or processing error

### Resolution Process
1. Clinic creates dispute with evidence
2. Admin reviews dispute details
3. Admin approves/rejects with notes
4. Automatic refund for approved disputes
5. Quality scores updated for tracking

### Quality Scoring
- **Good Quality**: 0 disputes per 10 leads
- **Average Quality**: 1-2 disputes per 10 leads  
- **Poor Quality**: 3+ disputes per 10 leads

## API Endpoints

### Billing APIs
```
GET /clinic/billing-dashboard - Main billing dashboard
POST /clinic/credits/topup - Initiate credit purchase
GET /clinic/credits/history - Transaction history
POST /create-razorpay-order - Create payment order
POST /verify-payment - Verify payment completion
```

### Dispute APIs
```
GET /clinic/disputes - Dispute dashboard
POST /clinic/disputes/create/<lead_id> - Create dispute
GET /admin/disputes - Admin dispute management
POST /admin/disputes/<dispute_id>/resolve - Resolve dispute
```

### Lead APIs (Enhanced)
```
POST /contact-clinic - Submit lead with billing
PUT /clinic/leads/update-status - Update lead status
```

## Integration Points

### Existing System Integration
1. **Lead Generation Flow**: Enhanced to include automatic billing
2. **Clinic Dashboard**: Added billing section and credit display
3. **Admin Panel**: Added dispute management interface
4. **Package Management**: Integrated with dynamic pricing

### Data Flow
1. Patient submits lead through package/clinic page
2. System calculates credit cost based on package price
3. Credits automatically deducted from clinic account
4. Lead delivered to clinic with billing record
5. Clinic can dispute low-quality leads
6. Admin resolves disputes with potential refunds

## Configuration

### Environment Variables
```
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret_key
DATABASE_URL=your_database_connection_string
```

### Database Setup
Run the following SQL to create required tables:
```sql
-- Credit transactions table
CREATE TABLE IF NOT EXISTS credit_transactions (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER REFERENCES clinics(id),
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    description TEXT,
    lead_id INTEGER REFERENCES leads(id),
    payment_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead disputes table  
CREATE TABLE IF NOT EXISTS lead_disputes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    clinic_id INTEGER REFERENCES clinics(id),
    dispute_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT,
    refund_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
```

## Usage Examples

### Getting Clinic Credit Balance
```python
from integrated_billing_system import BillingService

# Get current balance
balance = BillingService.get_clinic_credit_balance(clinic_id)
print(f"Current balance: ₹{balance}")
```

### Processing Lead with Billing
```python
# Calculate lead cost
lead_cost = BillingService.calculate_lead_cost(package_price)

# Deduct credits
success = BillingService.deduct_credits_for_lead(
    clinic_id=clinic_id,
    lead_cost=lead_cost, 
    lead_id=lead_id
)
```

### Creating Dispute
```python
# Create dispute for low-quality lead
dispute = LeadDispute(
    lead_id=lead_id,
    clinic_id=clinic_id,
    dispute_type='invalid_contact',
    description='Phone number is not reachable'
)
```

## Monitoring and Analytics

### Key Metrics Tracked
- Total credit balance per clinic
- Monthly credit spending
- Lead generation volume and costs
- Dispute rates and resolution times
- Payment success rates

### Dashboard Features
- Real-time credit balance
- Transaction history with filtering
- Lead cost breakdown by package type
- Dispute tracking and resolution status
- Payment history and receipts

## Support and Maintenance

### Common Issues
1. **Payment Failures**: Check Razorpay credentials and network connectivity
2. **Credit Deduction Errors**: Verify lead generation flow and billing integration
3. **Dispute Resolution**: Ensure admin access and proper dispute workflow

### Troubleshooting
- Check application logs for billing-related errors
- Verify database connections and table structure
- Test Razorpay integration in sandbox mode
- Monitor credit balance calculations for accuracy

## Future Enhancements

### Planned Features
1. **Bulk Credit Purchases**: Enterprise-level credit packages
2. **Credit Sharing**: Multi-location clinic credit sharing
3. **Advanced Analytics**: Detailed ROI and performance metrics
4. **Automated Refunds**: AI-powered dispute resolution
5. **Credit Expiration**: Time-based credit validity

This documentation provides a complete overview of the billing system implementation. Developers can use this guide to understand the architecture, integrate new features, and maintain the existing functionality.