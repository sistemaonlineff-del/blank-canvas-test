import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Database, FileText, Home, LogOut, RefreshCw, Search, Settings, UserPlus } from "lucide-react";
import { api, Row, User } from "./api";
import "./styles.css";

type Page = "home" | "qualificacao" | "cursos" | "status" | "aprovacoes" | "entidades" | "config";

const pageLabels: Record<Page, string> = {
  home: "Tela principal",
  qualificacao: "Qualificar Nova Entidade",
  cursos: "Cursos",
  status: "Consultar Status",
  aprovacoes: "Minhas Aprovações",
  entidades: "Entidades",
  config: "Configurações"
};

const tableLabels: Record<string, string> = {
  cursos: "Cursos",
  perguntas_qualificacao: "Perguntas Entidade",
  perguntas_bpf: "Perguntas BPF",
  perguntas_curso: "Perguntas Curso",
  alternativas_curso: "Alternativas Curso",
  owners_area: "Owners por Área",
  entidades: "Entidades",
  usuarios: "Usuários"
};

function useAsync<T>(factory: () => Promise<T>, deps: React.DependencyList) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    factory()
      .then((value) => active && setData(value))
      .catch((err) => active && setError(err.message || String(err)))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, deps);

  return { data, loading, error, reload: () => factory().then(setData) };
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await api.login(usuario, senha);
      localStorage.setItem("bahia_user", JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="login-page">
      <section className="login-hero">
        <h1>Governança e Qualificação de Demandas - Bahia</h1>
        <span>Sistema Bahia</span>
      </section>
      <form className="login-card" onSubmit={submit}>
        <h2>Acesso ao sistema</h2>
        <p>Entre para acompanhar qualificações, cursos e fluxos.</p>
        <label>E-mail ou usuário</label>
        <input value={usuario} onChange={(e) => setUsuario(e.target.value)} autoFocus />
        <label>Senha</label>
        <input value={senha} onChange={(e) => setSenha(e.target.value)} type="password" />
        {error && <div className="alert error">{error}</div>}
        <button type="submit">Entrar</button>
      </form>
    </main>
  );
}

function Layout({ user, page, setPage, logout, children }: any) {
  const admin = ["Administrador", "Moderador"].includes(user.perfil);
  const pages: { id: Page; icon: React.ReactNode }[] = [
    { id: "home", icon: <Home size={18} /> },
    { id: "qualificacao", icon: <UserPlus size={18} /> },
    { id: "cursos", icon: <FileText size={18} /> },
    { id: "status", icon: <Search size={18} /> },
    { id: "aprovacoes", icon: <CheckCircle2 size={18} /> },
    ...(admin ? [{ id: "entidades" as Page, icon: <Database size={18} /> }, { id: "config" as Page, icon: <Settings size={18} /> }] : [])
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/assets/logo_1.jpeg" />
          <img src="/assets/logo_2.jpeg" />
          <strong>Sistema Bahia</strong>
          <span>Governança & Qualificação</span>
        </div>
        <div className="user-chip">
          <div className="avatar">{(user.nome || user.usuario || "U").slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{user.nome || user.usuario}</strong>
            <span>{user.perfil} · {user.usuario}</span>
          </div>
        </div>
        <nav>
          {pages.map((item) => (
            <button key={item.id} className={page === item.id ? "active" : ""} onClick={() => setPage(item.id)}>
              {item.icon}
              {pageLabels[item.id]}
            </button>
          ))}
        </nav>
        <button className="logout" onClick={logout}>
          <LogOut size={18} />
          Sair
        </button>
      </aside>
      <section className="content">
        <header className="topbar">
          <h1>Governança e Qualificação de Demandas - Bahia</h1>
          <p>Sistema Bahia · {user.perfil}</p>
        </header>
        {children}
      </section>
    </div>
  );
}

function HomePage() {
  const { data, loading, error } = useAsync(api.dashboard, []);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage text={error} />;
  const cards = data?.cards || {};
  return (
    <PageBlock title="Tela principal">
      <div className="cards-grid">
        <Metric title="Entidades cadastradas" value={cards.entidades} />
        <Metric title="Entidades qualificadas" value={cards.qualificadas} />
        <Metric title="Form. geral pendentes" value={cards.formGeralPendentes} />
        <Metric title="BPF pendentes" value={cards.bpfPendentes} />
        <Metric title="Cursos disponíveis" value={cards.cursos} />
        <Metric title="Fluxos em andamento" value={cards.fluxos} />
      </div>
      <DataTable rows={data?.protocolos || []} empty="Nenhum protocolo criado." />
    </PageBlock>
  );
}

function EntidadesPage({ user }: { user: User }) {
  const [nome, setNome] = useState("");
  const [message, setMessage] = useState("");
  const { data, loading, error, reload } = useAsync(api.entities, [message]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const result = await api.createEntity(nome, user);
    setNome("");
    setMessage(result.message);
    await reload();
  }

  return (
    <PageBlock title="Entidades">
      <form className="inline-form" onSubmit={create}>
        <label>Cadastrar Nova entidade</label>
        <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Nome da Entidade" />
        <button>Salvar</button>
      </form>
      {message && <div className="alert success">{message}</div>}
      {loading ? <Loading /> : error ? <ErrorMessage text={error} /> : <DataTable rows={data?.items || []} />}
    </PageBlock>
  );
}

function QualificacaoPage() {
  const [tab, setTab] = useState<"cadastro" | "geral" | "bpf">("cadastro");
  const [selected, setSelected] = useState<Row | null>(null);
  const [fields, setFields] = useState<Row>({});
  const [message, setMessage] = useState("");
  const options = useAsync(api.qualificationOptions, [message]);
  const pendingGeral = useAsync(() => api.pendingQualification("geral"), [message]);
  const pendingBpf = useAsync(() => api.pendingQualification("bpf"), [message]);

  async function saveCadastro(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    const result = await api.saveCadastro(selected.id, fields);
    setMessage(result.message);
    setSelected(null);
    setFields({});
    setTab("geral");
  }

  return (
    <PageBlock title="Qualificar Nova Entidade">
      <Tabs value={tab} onChange={setTab} items={[
        ["cadastro", "Selecionar entidade da base"],
        ["geral", "Aguardando Finalizar Formulario Geral"],
        ["bpf", "Aguardando Finalizar Formulario BPF"]
      ]} />
      {message && <div className="alert success">{message}</div>}
      {tab === "cadastro" && (
        <form className="panel" onSubmit={saveCadastro}>
          <label>Entidade cadastrada na base</label>
          <select onChange={(e) => setSelected(options.data?.items.find((item) => String(item.id) === e.target.value) || null)} value={selected?.id || ""}>
            <option value="">Selecionar</option>
            {(options.data?.items || []).map((item) => <option key={item.id} value={item.id}>{item.id} | {item.entidade}</option>)}
          </select>
          <div className="form-grid">
            {["cnpj", "municipio_entidade", "territorio_identidade", "email_responsavel", "telefone", "endereco", "certificacao", "licenca_ambiental", "numero_convenio", "natureza_juridica"].map((field) => (
              <label key={field}>{field.replace(/_/g, " ")}
                <input value={fields[field] || ""} onChange={(e) => setFields({ ...fields, [field]: e.target.value })} />
              </label>
            ))}
          </div>
          <button disabled={!selected}>Salvar dados cadastrais</button>
        </form>
      )}
      {tab === "geral" && <DataTable rows={pendingGeral.data?.items || []} empty="Nenhuma entidade aguardando Formulario Geral." />}
      {tab === "bpf" && <DataTable rows={pendingBpf.data?.items || []} empty="Nenhuma entidade aguardando BPF." />}
    </PageBlock>
  );
}

function CursosPage({ user }: { user: User }) {
  const entities = useAsync(api.entities, []);
  const courses = useAsync(api.courses, []);
  const [payload, setPayload] = useState<Row>({});
  const [message, setMessage] = useState("");
  const qualified = (entities.data?.items || []).filter((item) => item.status_qualificacao === "Concluída");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const course = (courses.data?.items || []).find((item) => String(item.id) === String(payload.curso_id));
    const result = await api.createProtocol({
      ...payload,
      area: course?.area,
      solicitante_nome: user.nome,
      solicitante_email: user.email,
      usuario: user.usuario
    });
    setMessage(`${result.message} ${result.protocolo}`);
    setPayload({});
  }

  return (
    <PageBlock title="Cursos">
      <form className="panel" onSubmit={submit}>
        <label>Entidade
          <select value={payload.entidade_id || ""} onChange={(e) => setPayload({ ...payload, entidade_id: Number(e.target.value) })}>
            <option value="">Selecionar</option>
            {qualified.map((item) => <option key={item.id} value={item.id}>{item.entidade} · {item.nivel}</option>)}
          </select>
        </label>
        <label>Curso
          <select value={payload.curso_id || ""} onChange={(e) => setPayload({ ...payload, curso_id: Number(e.target.value) })}>
            <option value="">Selecionar</option>
            {(courses.data?.items || []).map((item) => <option key={item.id} value={item.id}>{item.curso} · {item.area} · {item.nivel}</option>)}
          </select>
        </label>
        <label>Observação
          <textarea value={payload.observacao || ""} onChange={(e) => setPayload({ ...payload, observacao: e.target.value })} />
        </label>
        <button>Salvar e iniciar fluxo</button>
      </form>
      {message && <div className="alert success">{message}</div>}
    </PageBlock>
  );
}

function StatusPage() {
  const { data, loading, error } = useAsync(api.protocols, []);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage text={error} />;
  return <PageBlock title="Consultar Status"><DataTable rows={data?.items || []} /></PageBlock>;
}

function AprovacoesPage({ user }: { user: User }) {
  const [selected, setSelected] = useState("");
  const [message, setMessage] = useState("");
  const protocols = useAsync(api.protocols, [message]);
  const forms = useAsync(() => selected ? api.forms(selected) : Promise.resolve(null), [selected, message]);
  const rows = protocols.data?.items || [];

  async function advance() {
    if (!selected) return;
    const result = await api.advanceProtocol(selected, user.usuario);
    setMessage(result.message);
  }

  return (
    <PageBlock title="Minhas Aprovações">
      {message && <div className="alert success">{message}</div>}
      <DataTable rows={rows} />
      <div className="inline-form">
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Selecionar protocolo</option>
          {rows.map((row) => <option key={row.protocolo} value={row.protocolo}>{row.protocolo} · {row.entidade} · {row.status}</option>)}
        </select>
        <button onClick={advance} disabled={!selected}>Aprovar / Avançar</button>
      </div>
      {selected && <DataTable rows={forms.data?.historico || []} empty="Sem histórico." />}
    </PageBlock>
  );
}

function ConfigPage() {
  const [table, setTable] = useState("cursos");
  const [rows, setRows] = useState<Row[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.table(table).then((data) => setRows(data.items));
  }, [table, message]);

  async function save() {
    await api.saveTable(table, rows);
    setMessage("Tabela salva.");
  }

  return (
    <PageBlock title="Configurações">
      <Tabs value={table} onChange={setTable as any} items={Object.entries(tableLabels)} />
      {message && <div className="alert success">{message}</div>}
      <EditableTable rows={rows} onChange={setRows} />
      <button onClick={save}>Salvar tabela</button>
    </PageBlock>
  );
}

function EditableTable({ rows, onChange }: { rows: Row[]; onChange: (rows: Row[]) => void }) {
  const columns = useMemo(() => Array.from(new Set(rows.flatMap((row) => Object.keys(row)))), [rows]);
  const editableColumns = columns.length ? columns : ["curso", "area", "nivel", "ativo"];

  function update(index: number, key: string, value: string) {
    const next = rows.slice();
    next[index] = { ...next[index], [key]: value };
    onChange(next);
  }

  return (
    <div className="table-scroll">
      <table>
        <thead><tr>{editableColumns.map((col) => <th key={col}>{col}</th>)}<th></th></tr></thead>
        <tbody>
          {[...rows, {}].map((row, index) => (
            <tr key={index}>
              {editableColumns.map((col) => (
                <td key={col}>
                  <input value={row[col] ?? ""} disabled={col === "id" && Boolean(row[col])} onChange={(e) => update(index, col, e.target.value)} />
                </td>
              ))}
              <td><button className="icon" onClick={() => onChange(rows.filter((_, i) => i !== index))}>Remover</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DataTable({ rows, empty = "Nenhum registro encontrado." }: { rows: Row[]; empty?: string }) {
  if (!rows.length) return <div className="empty">{empty}</div>;
  const cols = Array.from(new Set(rows.flatMap((row) => Object.keys(row)))).slice(0, 12);
  return (
    <div className="table-scroll">
      <table>
        <thead><tr>{cols.map((col) => <th key={col}>{col}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>{cols.map((col) => <td key={col}>{String(row[col] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Tabs({ value, onChange, items }: { value: any; onChange: (value: any) => void; items: [any, string][] }) {
  return <div className="tabs">{items.map(([id, label]) => <button key={id} className={value === id ? "active" : ""} onClick={() => onChange(id)}>{label}</button>)}</div>;
}

function PageBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return <main><h2 className="page-title">{title}</h2>{children}</main>;
}

function Metric({ title, value }: { title: string; value: any }) {
  return <div className="metric"><strong>{value ?? 0}</strong><span>{title}</span></div>;
}

function Loading() { return <div className="empty">Carregando...</div>; }
function ErrorMessage({ text }: { text: string }) { return <div className="alert error">{text}</div>; }

export default function App() {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("bahia_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [page, setPage] = useState<Page>("home");

  if (!user) return <Login onLogin={setUser} />;

  function logout() {
    localStorage.removeItem("bahia_user");
    setUser(null);
  }

  return (
    <Layout user={user} page={page} setPage={setPage} logout={logout}>
      {page === "home" && <HomePage />}
      {page === "entidades" && <EntidadesPage user={user} />}
      {page === "qualificacao" && <QualificacaoPage />}
      {page === "cursos" && <CursosPage user={user} />}
      {page === "status" && <StatusPage />}
      {page === "aprovacoes" && <AprovacoesPage user={user} />}
      {page === "config" && <ConfigPage />}
    </Layout>
  );
}
