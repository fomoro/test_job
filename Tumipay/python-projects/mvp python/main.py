from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from abc import ABC, abstractmethod
from faker import Faker
from enum import Enum  # <--- IMPORTANTE
import uuid
import random
from datetime import datetime

app = FastAPI(title="TumiPay Mock - Ciclo de Vida Completo")
fake = Faker()

# --- Configuración ---
VALID_PAYMENT_METHODS = ["pse", "credit_card", "nequi"]
VALID_PROVIDERS = ["payu", "kushki", "stripe"]
MAX_TRANSACTION_LIMIT = 5000000.0

# --- Memoria ---
processed_idempotency_keys = {} 
db_transactions = [] 

# --- NUEVO: DEFINICIÓN DE ESTADOS (ENUM) ---
class PayinStatus(str, Enum):
    CREATED = "CREATED"     # Se recibió la petición
    VALIDATED = "VALIDATED" # Pasó las reglas de negocio (cuenta, saldo, etc.)
    PROCESSED = "PROCESSED" # El proveedor externo (PayU, etc.) confirmó el pago
    FAILED = "FAILED"       # Algo falló en el proceso

# ==========================================
# --- CAPA DE INFRAESTRUCTURA (PATRÓN ADAPTER) ---
# ==========================================

class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, amount: float, client_data: dict) -> dict:
        pass

class PayUAdapter(PaymentGateway):
    def process_payment(self, amount: float, client_data: dict) -> dict:
        print(f"--> [PayU Adapter] Enviando {amount} COP a {client_data['email']}")
        return {"ref": f"payu-{uuid.uuid4()}", "msg": "Transacción Aprobada PayU"}

class KushkiAdapter(PaymentGateway):
    def process_payment(self, amount: float, client_data: dict) -> dict:
        cents = int(amount * 100)
        print(f"--> [Kushki Adapter] Procesando {cents} centavos vía API Cajita.")
        return {"ref": f"ticket-{random.randint(10000,99999)}", "msg": "OK Kushki"}

class StripeAdapter(PaymentGateway):
    def process_payment(self, amount: float, client_data: dict) -> dict:
        print(f"--> [Stripe Adapter] Charging client {client_data['id']} - USD Equiv.")
        return {"ref": f"ch_{uuid.uuid4()}", "msg": "Succeeded Stripe"}

class PaymentFactory:
    @staticmethod
    def get_provider(provider_id: str) -> PaymentGateway:
        if provider_id == "payu": return PayUAdapter()
        elif provider_id == "kushki": return KushkiAdapter()
        elif provider_id == "stripe": return StripeAdapter()
        else:
            raise HTTPException(status_code=400, detail=f"Proveedor '{provider_id}' no configurado")

# ==========================================
# --- FIN DE INFRAESTRUCTURA ---
# ==========================================

# --- Modelos ---
class Account(BaseModel):
    account_id: str
    account_number: str
    account_type: str
    status: str 

class Client(BaseModel):
    client_id: str
    full_name: str
    email: EmailStr
    accounts: List[Account]

class TransactionRequest(BaseModel):
    client_id: str
    account_id: str
    amount: float
    currency: str
    payment_method_id: str
    provider_id: str

class TransactionResponse(BaseModel):
    transaction_id: str
    status: PayinStatus       # <--- AHORA USA EL ENUM
    status_message: str
    created_at: str
    amount: float
    idempotency_key: str
    provider_reference: Optional[str] = None
    client_id: Optional[str] = None
    account_id: Optional[str] = None

# --- Datos ---
db_clients = []
db_clients.append({
    "client_id": "cli-123-test",
    "full_name": "Wolfan Tester",
    "email": "wolfan@tumipay.com",
    "accounts": [
        {"account_id": "acc-active-001", "account_number": "111-222", "account_type": "checking", "status": "active"},
        {"account_id": "acc-blocked-999", "account_number": "999-888", "account_type": "savings", "status": "blocked"}
    ]
})

for _ in range(5):
    db_clients.append({
        "client_id": str(uuid.uuid4()),
        "full_name": fake.name(),
        "email": fake.email(),
        "accounts": [{"account_id": str(uuid.uuid4()), "account_number": fake.iban(), "account_type": "checking", "status": "active"}]
    })

# --- Endpoints ---

@app.get("/api/v1/clients", response_model=List[Client])
async def list_clients():
    return db_clients

@app.post("/api/v1/payins", response_model=TransactionResponse, status_code=201)
async def create_payin(
    payload: TransactionRequest,
    x_idempotency_key: str = Header(..., alias="x-idempotency-key")
):
    # ---------------------------------------------------------
    # PASO 0: INICIO DEL CICLO DE VIDA (CREATED)
    # ---------------------------------------------------------
    current_status = PayinStatus.CREATED
    print(f"🔄 [Ciclo de Vida] Estado Inicial: {current_status.value}")

    # 1. CONTROL DE DUPLICADOS (Idempotencia)
    if x_idempotency_key in processed_idempotency_keys:
        prev_id = processed_idempotency_keys[x_idempotency_key]
        raise HTTPException(status_code=409, detail=f"Conflicto: Llave ya procesada (Tx ID: {prev_id}).")

    try:
        # ---------------------------------------------------------
        # PASO 1: VALIDACIONES DE NEGOCIO
        # ---------------------------------------------------------
        if payload.payment_method_id not in VALID_PAYMENT_METHODS:
            raise ValueError("Método de pago inválido") # Usamos ValueError para capturar abajo
        
        if payload.provider_id not in VALID_PROVIDERS: 
            raise ValueError("Proveedor inválido")

        client = next((c for c in db_clients if c["client_id"] == payload.client_id), None)
        if not client: raise ValueError("Cliente no encontrado")

        account = next((a for a in client["accounts"] if a["account_id"] == payload.account_id), None)
        if not account: raise ValueError("Cuenta ajena al cliente")

        if account["status"] != "active":
            raise ValueError(f"Cuenta {account['status']}: No recibe fondos")
        
        if payload.amount <= 0 or payload.amount > MAX_TRANSACTION_LIMIT:
            raise ValueError("Monto fuera de límites")

        # SI LLEGAMOS AQUI, LAS REGLAS DE NEGOCIO PASARON
        current_status = PayinStatus.VALIDATED
        print(f"✅ [Ciclo de Vida] Reglas de Negocio OK -> Estado: {current_status.value}")

        # ---------------------------------------------------------
        # PASO 2: PROCESAMIENTO EXTERNO (ADAPTER)
        # ---------------------------------------------------------
        gateway = PaymentFactory.get_provider(payload.provider_id)
        client_data = {"email": client["email"], "id": client["client_id"]}
        
        # Llamada al adaptador
        provider_response = gateway.process_payment(payload.amount, client_data)
        
        # SI EL ADAPTADOR RESPONDE BIEN
        current_status = PayinStatus.PROCESSED
        print(f"🚀 [Ciclo de Vida] Pago Exitoso -> Estado Final: {current_status.value}")

        # Guardar éxito
        new_tx_id = str(uuid.uuid4())
        processed_idempotency_keys[x_idempotency_key] = new_tx_id

        tx = {
            "transaction_id": new_tx_id,
            "status": current_status, # GUARDAMOS EL ENUM
            "status_message": provider_response["msg"],
            "created_at": datetime.now().isoformat(),
            "amount": payload.amount,
            "provider_reference": provider_response["ref"],
            "client_id": payload.client_id,
            "account_id": payload.account_id,
            "idempotency_key": x_idempotency_key
        }
        db_transactions.append(tx)
        return tx

    except ValueError as e:
        # MANEJO DE ERRORES DE NEGOCIO
        current_status = PayinStatus.FAILED
        print(f"❌ [Ciclo de Vida] Error de Negocio -> Estado: {current_status.value}")
        # En un sistema real, aquí guardaríamos la transacción fallida en BD
        # Para el mock, devolvemos el error HTTP correspondiente
        if "Cuenta" in str(e):
             raise HTTPException(status_code=409, detail=str(e))
        elif "encontrado" in str(e):
             raise HTTPException(status_code=404, detail=str(e))
        else:
             raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # MANEJO DE ERRORES DE SISTEMA
        current_status = PayinStatus.FAILED
        print(f"🔥 [Ciclo de Vida] Error Crítico -> Estado: {current_status.value}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/api/v1/payins/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    transaction = next((t for t in db_transactions if t["transaction_id"] == transaction_id), None)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return transaction