import psycopg2
import pandas as pd
from tabulate import tabulate

# Cadena de conexión
DB_URL = "postgresql://neondb_owner:npg_JFvV9G0LpxsS@ep-weathered-dawn-ae1flers-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def run_query(query, params=None):
    conn = psycopg2.connect(DB_URL)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def print_table(df, title):
    print(f"\n=== {title} ===")
    if df.empty:
        print("Sin resultados")
    else:
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))


query_historial = """
SELECT 
    t.created_at,
    t.status,
    t.amount,
    t.currency,
    p.name AS provider,
    pm.name AS method,
    t.status_message
FROM transactions t
JOIN clients c ON t.client_id = c.client_id
JOIN providers p ON t.provider_id = p.provider_id
JOIN payment_methods pm ON t.payment_method_id = pm.method_id
WHERE c.email = %s
ORDER BY t.created_at DESC;
"""

df = run_query(query_historial, params=("wolfan@tumipay.com",))
print_table(df, "Historial del cliente")

query_fallos = """
SELECT 
    status_message, 
    provider_id,
    COUNT(*) AS total_failures
FROM transactions
WHERE status = 'FAILED'
GROUP BY status_message, provider_id
ORDER BY total_failures DESC;
"""

df = run_query(query_fallos)
print_table(df, "Diagnóstico de fallos")
