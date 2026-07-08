# Governança e Qualificação de Demandas - Bahia

Aplicação migrada para uma arquitetura compatível com Vercel:

- Frontend: React + TypeScript + Vite.
- API: Flask em função serverless dentro de `api/index.py`.
- Banco: Supabase/Postgres em produção via `SUPABASE_DB_URL` ou `DATABASE_URL`.
- Fallback local: SQLite `bahia.db`.

O Streamlit original permanece em `app.py` como referência/backup.

## Rodar localmente

```bash
pip install -r requirements.txt
npm install
npm run dev
```

Para testar a API Flask localmente separada do Vite:

```bash
flask --app api.index run --port 5000
```

## Deploy Vercel

Variáveis de ambiente recomendadas:

```text
SUPABASE_DB_URL=postgresql://...
```

Comandos:

```bash
vercel deploy
vercel env add SUPABASE_DB_URL production
```

## Login inicial local

- usuário: `admin`
- senha: `admin123`
