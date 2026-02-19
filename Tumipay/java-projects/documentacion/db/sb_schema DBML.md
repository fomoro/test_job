
---

## Versión dbdiagram.io (DBML)

👉 Esta la pegas **directamente en https://dbdiagram.io**  
Te genera el diagrama visual automáticamente.

```dbml
Table providers {
  provider_id varchar(20) [pk]
  name varchar(50)
  is_active boolean
  created_at timestamp
}

Table payment_methods {
  method_id varchar(20) [pk]
  name varchar(50)
  created_at timestamp
}

Table clients {
  client_id varchar(50) [pk]
  full_name varchar(100)
  email varchar(100) [unique]
  created_at timestamp
}

Table accounts {
  account_id varchar(50) [pk]
  client_id varchar(50)
  account_number varchar(50) [unique]
  account_type varchar(20)
  status varchar(20)
  balance numeric(15,2)
  created_at timestamp
}

Table transactions {
  transaction_id varchar(50) [pk]
  client_id varchar(50)
  account_id varchar(50)
  payment_method_id varchar(20)
  provider_id varchar(20)
  amount numeric(15,2)
  currency varchar(3)
  provider_reference varchar(100)
  status varchar(20)
  status_message text
  idempotency_key varchar(100) [unique]
  created_at timestamp
}

Ref: accounts.client_id > clients.client_id
Ref: transactions.client_id > clients.client_id
Ref: transactions.account_id > accounts.account_id
Ref: transactions.payment_method_id > payment_methods.method_id
Ref: transactions.provider_id > providers.provider_id
```