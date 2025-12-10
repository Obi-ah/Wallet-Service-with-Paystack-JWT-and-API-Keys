# Wallet Service – Paystack • JWT • API Keys  
A backend wallet system that supports deposits via Paystack, wallet transfers, transaction history, Google Sign-In (JWT), and API key–based service access.

## 🔧 **Tech Stack**
- FastAPI • Python  
- PostgreSQL • SQLAlchemy 2.x  
- Paystack Payments  
- Google OAuth (JWT Authentication)  
- Secure API Keys (service-to-service)  

## **Core Features**
### **Authentication**
- Google OAuth → returns JWT  
- API Keys for service-to-service access  
- Max **5 active API keys** per user  
- API key permissions: `deposit`, `transfer`, `read`  
- API keys must **expire**, can be **revoked**, and can be **rolled over`

### **Wallet**
- Auto-created on user’s first login  
- Deposit using Paystack  
- Mandatory Paystack **webhook** for crediting wallet  
- Wallet-to-wallet transfers  
- View wallet balance  
- View transaction history  

### **Transactions**
- Types: `deposit`, `transfer_in`, `transfer_out`  
- Status: `pending`, `success`, `failed`  
- Webhook is **idempotent** – no double-crediting  
- Paystack reference is unique  

# **Endpoints Overview**

## Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Redirect to Google OAuth |
| GET | `/auth/google/callback` | Creates user, wallet, returns JWT |

##  API Keys
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/keys/create` | Create API key (max 5 active) |
| POST | `/keys/rollover` | Replace expired key with new one |

## Wallet
| Method | Endpoint | Permission |
|--------|----------|-------------|
| POST | `/wallet/deposit` | `deposit` |
| POST | `/wallet/paystack/webhook` | Paystack calls this |
| GET | `/wallet/deposit/{ref}/status` | `read` |
| GET | `/wallet/balance` | `read` |
| POST | `/wallet/transfer` | `transfer` |
| GET | `/wallet/transactions` | `read` |

#  **Authentication Rules**
### **JWT Auth**
```
Authorization: Bearer <jwt_token>
```

### **API Key Auth**
```
x-api-key: <api_key>
```

### JWT users → full permissions  
### API keys → restricted by assigned permissions  

#  **Paystack Flow**
1. User hits `/wallet/deposit`  
2. Server calls Paystack → returns `authorization_url`  
3. User completes payment  
4. Paystack sends webhook → `/wallet/paystack/webhook`  
5. Webhook verifies signature → credits wallet  

 **Only the webhook will credit the wallet.**

#  **Testing Order**
1. Login via Google → get JWT  
2. GET `/wallet/balance`  
3. Create API key `/keys/create`  
4. Deposit using `/wallet/deposit`  
5. Trigger webhook  
6. Confirm balance  
7. Transfer  
8. GET `/wallet/transactions`

#  Environment Variables
```
DATABASE_URL=
JWT_SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
```

#  Start the Service
```
uvicorn app.main:app --reload
```
