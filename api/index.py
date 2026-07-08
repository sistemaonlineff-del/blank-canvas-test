from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS


APP_DIR = Path(__file__).resolve().parents[1]
DB_PATH = APP_DIR / "bahia.db"
DATABASE_URL = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

NIVEIS = ["Básico", "Intermediário", "Avançado"]
AREAS_CURSO = ["CIMATEC", "SEBRAE"]
FORM_GERAL_PENDENTE = "Formulario geral pendente"
CADASTRO_INICIAL = "Cadastro inicial"
STATUS_FLUXO = [
    "Validação Administrativa",
    "Análise Técnica",
    "Agendamento",
    "Execução",
    "Finalizado",
    "Cancelado",
    "Reprovado",
]
EDITABLE_TABLES = {
    "cursos": "cursos",
    "perguntas_qualificacao": "perguntas_qualificacao",
    "perguntas_bpf": "perguntas_bpf",
    "perguntas_curso": "perguntas_curso",
    "alternativas_curso": "alternativas_curso",
    "owners_area": "owners_area",
    "entidades": "entidades",
    "usuarios": "usuarios",
}

app = Flask(__name__)
CORS(app)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_sql(sql: str) -> str:
    if USE_POSTGRES:
        return sql.replace("?", "%s")
    return re.sub(r"\s+RETURNING\s+id\s*$", "", sql, flags=re.IGNORECASE)


@contextmanager
def db():
    if USE_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with db() as conn:
        cur = conn.execute(normalize_sql(sql), params)
        return [dict(row) for row in cur.fetchall()]


def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple[Any, ...] = ()) -> int | None:
    with db() as conn:
        cur = conn.execute(normalize_sql(sql), params)
        if USE_POSTGRES and sql.lstrip().lower().startswith("insert"):
            try:
                row = cur.fetchone()
                return row["id"] if row and "id" in row else None
            except Exception:
                return None
        return getattr(cur, "lastrowid", None)


def init_db():
    if USE_POSTGRES:
        return
    ddl = """
    CREATE TABLE IF NOT EXISTS usuarios (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT,
      usuario TEXT UNIQUE,
      senha_hash TEXT,
      perfil TEXT,
      email TEXT,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS entidades (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entidade TEXT,
      cnpj TEXT,
      email_responsavel TEXT,
      telefone TEXT,
      endereco TEXT,
      territorio_identidade TEXT,
      municipio_entidade TEXT,
      certificacao TEXT,
      licenca_ambiental TEXT,
      atep TEXT,
      agente_negocio TEXT,
      numero_convenio TEXT,
      an_atep_ateg TEXT,
      nome_ateg TEXT,
      coordenador_tipo TEXT,
      nome_coordenador TEXT,
      natureza_juridica TEXT,
      dap_caf TEXT,
      tipologia_beneficiarios TEXT,
      comunidade_tradicional TEXT,
      ativa_dinamica TEXT,
      status_qualificacao TEXT DEFAULT 'Cadastro inicial',
      nivel TEXT,
      pontuacao INTEGER DEFAULT 0,
      pontuacao_q1 INTEGER DEFAULT 0,
      pontuacao_q2 INTEGER DEFAULT 0,
      data_cadastro TEXT,
      cadastrado_por TEXT,
      cadastrado_por_email TEXT,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS cursos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      curso TEXT,
      area TEXT,
      nivel TEXT,
      descricao TEXT,
      carga_horaria TEXT,
      owner_email TEXT,
      estoque_total INTEGER DEFAULT 0,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS perguntas_qualificacao (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      questionario TEXT,
      ordem INTEGER,
      pergunta TEXT,
      opcao_1 TEXT,
      opcao_2 TEXT,
      opcao_3 TEXT,
      pontos_1 INTEGER DEFAULT 0,
      pontos_2 INTEGER DEFAULT 5,
      pontos_3 INTEGER DEFAULT 10,
      pontos_sim INTEGER DEFAULT 1,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS perguntas_bpf (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      secao TEXT,
      subsecao TEXT,
      codigo_pergunta TEXT,
      ordem INTEGER,
      pergunta TEXT,
      opcoes TEXT DEFAULT 'S;N;P;NA',
      pontos_sim INTEGER DEFAULT 1,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS perguntas_curso (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      curso_id INTEGER,
      ordem INTEGER,
      pergunta TEXT,
      pontos_sim INTEGER DEFAULT 1,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS alternativas_curso (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      pergunta_id INTEGER,
      ordem INTEGER,
      alternativa TEXT,
      pontos INTEGER DEFAULT 0,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS protocolos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      protocolo TEXT UNIQUE,
      entidade_id INTEGER,
      curso_id INTEGER,
      area TEXT,
      pontuacao_curso INTEGER,
      status TEXT,
      etapa_atual TEXT,
      responsavel_atual TEXT,
      solicitante_nome TEXT,
      solicitante_email TEXT,
      data_abertura TEXT,
      data_atualizacao TEXT,
      data_agendada TEXT,
      observacao TEXT,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS respostas_entidade (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entidade_id INTEGER,
      questionario TEXT,
      pergunta_id INTEGER,
      pergunta TEXT,
      resposta TEXT,
      pontuacao INTEGER,
      data_resposta TEXT
    );
    CREATE TABLE IF NOT EXISTS respostas_bpf (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entidade_id INTEGER,
      pergunta_id INTEGER,
      pergunta TEXT,
      resposta TEXT,
      pontuacao INTEGER,
      data_resposta TEXT
    );
    CREATE TABLE IF NOT EXISTS respostas_curso (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      protocolo TEXT,
      pergunta_id INTEGER,
      pergunta TEXT,
      resposta TEXT,
      pontuacao INTEGER,
      data_resposta TEXT
    );
    CREATE TABLE IF NOT EXISTS owners_area (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      area TEXT,
      etapa TEXT,
      nome TEXT,
      email TEXT,
      usuario TEXT,
      ativo INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS historico_fluxo (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      protocolo TEXT,
      status_anterior TEXT,
      status_novo TEXT,
      usuario TEXT,
      data_movimento TEXT,
      observacao TEXT
    );
    """
    if USE_POSTGRES:
        return
    with db() as conn:
        conn.executescript(ddl)
        exists = conn.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
        if not exists:
            conn.execute(
                "INSERT INTO usuarios(nome,usuario,senha_hash,perfil,email,ativo) VALUES(?,?,?,?,?,1)",
                ("Administrador", "admin", hash_pw("admin123"), "Administrador", ""),
            )


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in user.items() if k != "senha_hash"}


def bool_value(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in {"1", "true", "sim", "yes"}
    return bool(value)


def allowed_levels(nivel: str) -> list[str]:
    return {
        "Básico": ["Básico"],
        "Intermediário": ["Básico", "Intermediário"],
        "Avançado": ["Básico", "Intermediário", "Avançado"],
    }.get(nivel, ["Básico"])


def next_step(status: str) -> tuple[str, str]:
    return {
        "Validação Administrativa": ("Análise Técnica", "Técnico"),
        "Análise Técnica": ("Agendamento", "Agendamento"),
        "Agendamento": ("Execução", "Executor"),
        "Execução": ("Finalizado", "Finalizado"),
    }.get(status, (status, ""))


@app.get("/api/health")
def health():
    init_db()
    return jsonify({"ok": True, "backend": "postgres" if USE_POSTGRES else "sqlite"})


@app.post("/api/login")
def login():
    init_db()
    data = request.get_json(force=True)
    login_value = (data.get("usuario") or "").strip().lower()
    password = data.get("senha") or ""
    user = fetch_one(
        "SELECT * FROM usuarios WHERE ativo=1 AND (LOWER(usuario)=? OR LOWER(email)=?) LIMIT 1",
        (login_value, login_value),
    )
    if not user or user.get("senha_hash") != hash_pw(password):
        return jsonify({"error": "Usuário ou senha inválidos."}), 401
    return jsonify({"user": public_user(user)})


@app.get("/api/dashboard")
def dashboard():
    init_db()
    entidades = fetch_all("SELECT * FROM entidades WHERE ativo=1")
    cursos = fetch_all("SELECT * FROM cursos WHERE ativo=1")
    protocolos = fetch_all("SELECT * FROM protocolos")
    andamento = [p for p in protocolos if p.get("status") not in {"Finalizado", "Cancelado", "Reprovado"}]
    return jsonify(
        {
            "cards": {
                "entidades": len(entidades),
                "qualificadas": len([e for e in entidades if e.get("status_qualificacao") == "Concluída"]),
                "formGeralPendentes": len([e for e in entidades if e.get("status_qualificacao") == FORM_GERAL_PENDENTE]),
                "bpfPendentes": len([e for e in entidades if e.get("status_qualificacao") == "BPF pendente"]),
                "cursos": len(cursos),
                "fluxos": len(andamento),
            },
            "protocolos": protocolos[-20:],
            "entidadesPorNivel": entidades,
            "cursosPorArea": cursos,
        }
    )


@app.get("/api/entities")
def entities():
    init_db()
    rows = fetch_all("SELECT * FROM entidades WHERE ativo=1 ORDER BY id DESC")
    return jsonify({"items": rows})


@app.post("/api/entities")
def create_entity():
    init_db()
    data = request.get_json(force=True)
    nome = (data.get("entidade") or "").strip()
    if not nome:
        return jsonify({"error": "Informe o nome da entidade."}), 400
    row_id = execute(
        """INSERT INTO entidades(entidade,status_qualificacao,data_cadastro,cadastrado_por,cadastrado_por_email,ativo)
           VALUES(?,?,?,?,?,?) RETURNING id""",
        (nome, CADASTRO_INICIAL, now_str(), data.get("usuario", "admin"), data.get("email", ""), True),
    )
    return jsonify({"id": row_id, "message": "Entidade cadastrada."})


@app.get("/api/qualification/start-options")
def qualification_start_options():
    init_db()
    rows = fetch_all(
        """SELECT * FROM entidades
           WHERE ativo=1 AND COALESCE(status_qualificacao,'') NOT IN (?, ?)
           ORDER BY entidade""",
        (FORM_GERAL_PENDENTE, "BPF pendente"),
    )
    return jsonify({"items": rows})


@app.post("/api/qualification/cadastro")
def save_cadastro():
    init_db()
    data = request.get_json(force=True)
    entidade_id = data.get("id")
    fields = data.get("fields", {})
    execute(
        """UPDATE entidades
           SET cnpj=?, email_responsavel=?, telefone=?, endereco=?, territorio_identidade=?,
               municipio_entidade=?, certificacao=?, licenca_ambiental=?, numero_convenio=?,
               an_atep_ateg=?, agente_negocio=?, atep=?, nome_ateg=?, coordenador_tipo=?,
               nome_coordenador=?, natureza_juridica=?, dap_caf=?, tipologia_beneficiarios=?,
               comunidade_tradicional=?, ativa_dinamica=?, status_qualificacao=?
           WHERE id=?""",
        (
            fields.get("cnpj"),
            fields.get("email_responsavel"),
            fields.get("telefone"),
            fields.get("endereco"),
            fields.get("territorio_identidade"),
            fields.get("municipio_entidade"),
            fields.get("certificacao"),
            fields.get("licenca_ambiental"),
            fields.get("numero_convenio"),
            fields.get("an_atep_ateg"),
            fields.get("agente_negocio"),
            fields.get("atep"),
            fields.get("nome_ateg"),
            fields.get("coordenador_tipo"),
            fields.get("nome_coordenador"),
            fields.get("natureza_juridica"),
            fields.get("dap_caf"),
            fields.get("tipologia_beneficiarios"),
            fields.get("comunidade_tradicional"),
            fields.get("ativa_dinamica"),
            FORM_GERAL_PENDENTE,
            entidade_id,
        ),
    )
    return jsonify({"message": "Dados cadastrais salvos."})


@app.get("/api/questions/<kind>")
def questions(kind: str):
    init_db()
    if kind == "geral":
        rows = fetch_all("SELECT * FROM perguntas_qualificacao WHERE ativo=1 ORDER BY questionario, ordem")
    elif kind == "bpf":
        rows = fetch_all("SELECT * FROM perguntas_bpf WHERE ativo=1 ORDER BY secao, subsecao, ordem")
    else:
        return jsonify({"error": "Tipo inválido."}), 404
    return jsonify({"items": rows})


@app.get("/api/qualification/pending/<kind>")
def qualification_pending(kind: str):
    init_db()
    status = FORM_GERAL_PENDENTE if kind == "geral" else "BPF pendente"
    rows = fetch_all("SELECT * FROM entidades WHERE ativo=1 AND status_qualificacao=? ORDER BY id DESC", (status,))
    return jsonify({"items": rows})


@app.post("/api/qualification/general")
def save_general():
    init_db()
    data = request.get_json(force=True)
    entidade_id = int(data["entidade_id"])
    respostas = data.get("respostas", [])
    pontos = sum(int(r.get("pontuacao") or 0) for r in respostas)
    nivel = "Básico" if pontos <= 20 else "Intermediário" if pontos <= 35 else "Avançado"
    data_resposta = now_str()
    with db() as conn:
        conn.execute(normalize_sql("DELETE FROM respostas_entidade WHERE entidade_id=?"), (entidade_id,))
        for r in respostas:
            conn.execute(
                normalize_sql(
                    """INSERT INTO respostas_entidade(entidade_id,questionario,pergunta_id,pergunta,resposta,pontuacao,data_resposta)
                       VALUES(?,?,?,?,?,?,?)"""
                ),
                (
                    entidade_id,
                    r.get("questionario"),
                    r.get("pergunta_id"),
                    r.get("pergunta"),
                    r.get("resposta"),
                    r.get("pontuacao"),
                    data_resposta,
                ),
            )
        conn.execute(
            normalize_sql(
                "UPDATE entidades SET status_qualificacao='BPF pendente', nivel=?, pontuacao=?, pontuacao_q1=? WHERE id=?"
            ),
            (nivel, pontos, pontos, entidade_id),
        )
    return jsonify({"message": "Formulário Geral salvo.", "nivel": nivel, "pontuacao": pontos})


@app.post("/api/qualification/bpf")
def save_bpf():
    init_db()
    data = request.get_json(force=True)
    entidade_id = int(data["entidade_id"])
    respostas = data.get("respostas", [])
    pontos = sum(int(r.get("pontuacao") or 0) for r in respostas)
    data_resposta = now_str()
    with db() as conn:
        conn.execute(normalize_sql("DELETE FROM respostas_bpf WHERE entidade_id=?"), (entidade_id,))
        for r in respostas:
            conn.execute(
                normalize_sql(
                    "INSERT INTO respostas_bpf(entidade_id,pergunta_id,pergunta,resposta,pontuacao,data_resposta) VALUES(?,?,?,?,?,?)"
                ),
                (entidade_id, r.get("pergunta_id"), r.get("pergunta"), r.get("resposta"), r.get("pontuacao"), data_resposta),
            )
        conn.execute(
            normalize_sql("UPDATE entidades SET status_qualificacao='Concluída', pontuacao=COALESCE(pontuacao,0)+? WHERE id=?"),
            (pontos, entidade_id),
        )
    return jsonify({"message": "BPF salvo. Entidade liberada para cursos."})


@app.get("/api/courses")
def courses():
    init_db()
    rows = fetch_all("SELECT * FROM cursos WHERE ativo=1 ORDER BY area,nivel,curso")
    return jsonify({"items": rows})


@app.get("/api/protocols")
def protocols():
    init_db()
    rows = fetch_all(
        """SELECT p.*, e.entidade, e.nivel AS nivel_entidade, c.curso
           FROM protocolos p
           LEFT JOIN entidades e ON e.id=p.entidade_id
           LEFT JOIN cursos c ON c.id=p.curso_id
           ORDER BY p.id DESC"""
    )
    return jsonify({"items": rows, "status": STATUS_FLUXO})


@app.post("/api/protocols")
def create_protocol():
    init_db()
    data = request.get_json(force=True)
    protocolo = f"BA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    data_mov = now_str()
    execute(
        """INSERT INTO protocolos(protocolo,entidade_id,curso_id,area,pontuacao_curso,status,etapa_atual,responsavel_atual,
                  solicitante_nome,solicitante_email,data_abertura,data_atualizacao,observacao)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id""",
        (
            protocolo,
            data.get("entidade_id"),
            data.get("curso_id"),
            data.get("area"),
            data.get("pontuacao_curso", 0),
            "Validação Administrativa",
            "Administrativo",
            "Administrativo",
            data.get("solicitante_nome", ""),
            data.get("solicitante_email", ""),
            data_mov,
            data_mov,
            data.get("observacao", ""),
        ),
    )
    execute(
        "INSERT INTO historico_fluxo(protocolo,status_anterior,status_novo,usuario,data_movimento,observacao) VALUES(?,?,?,?,?,?)",
        (protocolo, "", "Validação Administrativa", data.get("usuario", "admin"), data_mov, data.get("observacao", "")),
    )
    return jsonify({"message": "Protocolo criado.", "protocolo": protocolo})


@app.post("/api/protocols/<protocolo>/advance")
def advance_protocol(protocolo: str):
    init_db()
    data = request.get_json(force=True)
    row = fetch_one("SELECT * FROM protocolos WHERE protocolo=? LIMIT 1", (protocolo,))
    if not row:
        return jsonify({"error": "Protocolo não encontrado."}), 404
    novo_status, nova_etapa = next_step(row.get("status"))
    data_mov = now_str()
    execute(
        "UPDATE protocolos SET status=?, etapa_atual=?, responsavel_atual=?, data_atualizacao=? WHERE protocolo=?",
        (novo_status, nova_etapa, nova_etapa, data_mov, protocolo),
    )
    execute(
        "INSERT INTO historico_fluxo(protocolo,status_anterior,status_novo,usuario,data_movimento,observacao) VALUES(?,?,?,?,?,?)",
        (protocolo, row.get("status"), novo_status, data.get("usuario", "admin"), data_mov, data.get("observacao", "")),
    )
    return jsonify({"message": "Fluxo atualizado.", "status": novo_status})


@app.get("/api/forms/<protocolo>")
def protocol_forms(protocolo: str):
    init_db()
    prot = fetch_one("SELECT * FROM protocolos WHERE protocolo=? LIMIT 1", (protocolo,))
    if not prot:
        return jsonify({"error": "Protocolo não encontrado."}), 404
    entidade_id = prot.get("entidade_id")
    return jsonify(
        {
            "geral": fetch_all("SELECT * FROM respostas_entidade WHERE entidade_id=? ORDER BY id", (entidade_id,)),
            "bpf": fetch_all("SELECT * FROM respostas_bpf WHERE entidade_id=? ORDER BY id", (entidade_id,)),
            "curso": fetch_all("SELECT * FROM respostas_curso WHERE protocolo=? ORDER BY id", (protocolo,)),
            "historico": fetch_all("SELECT * FROM historico_fluxo WHERE protocolo=? ORDER BY id", (protocolo,)),
        }
    )


@app.get("/api/admin/table/<table>")
def get_table(table: str):
    init_db()
    if table not in EDITABLE_TABLES:
        return jsonify({"error": "Tabela não permitida."}), 404
    rows = fetch_all(f"SELECT * FROM {EDITABLE_TABLES[table]} ORDER BY id DESC")
    return jsonify({"items": rows})


@app.post("/api/admin/table/<table>")
def save_table(table: str):
    init_db()
    if table not in EDITABLE_TABLES:
        return jsonify({"error": "Tabela não permitida."}), 404
    real_table = EDITABLE_TABLES[table]
    data = request.get_json(force=True)
    rows = data.get("rows", [])
    for row in rows:
        row = {k: v for k, v in row.items() if k != "_deleted"}
        row_id = row.get("id")
        cols = [k for k in row.keys() if k != "id"]
        if row_id:
            set_clause = ", ".join(f"{c}=?" for c in cols)
            execute(f"UPDATE {real_table} SET {set_clause} WHERE id=?", tuple(row[c] for c in cols) + (row_id,))
        elif any(v not in (None, "") for v in row.values()):
            placeholders = ", ".join("?" for _ in cols)
            execute(f"INSERT INTO {real_table}({', '.join(cols)}) VALUES({placeholders})", tuple(row[c] for c in cols))
    return jsonify({"message": "Tabela salva."})


init_db()
