export type User = {
  id: number;
  nome: string;
  usuario: string;
  email?: string;
  perfil: string;
  ativo?: boolean | number;
  senha_temporaria?: boolean | number;
  trocar_senha_obrigatorio?: boolean | number;
  acesso_pendente?: boolean | number;
};

export type Row = Record<string, any>;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Erro na requisição.");
  }
  return data as T;
}

export const api = {
  login: (usuario: string, senha: string) =>
    request<{ user: User }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ usuario, senha })
    }),
  register: (email: string) =>
    request<{ message: string }>("/api/register", {
      method: "POST",
      body: JSON.stringify({ email })
    }),
  changePassword: (userId: number, senha: string) =>
    request<{ user: User; message: string }>("/api/change-password", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, senha })
    }),
  dashboard: () => request<any>("/api/dashboard"),
  entities: () => request<{ items: Row[] }>("/api/entities"),
  createEntity: (entidade: string, user: User) =>
    request<{ id: number; message: string }>("/api/entities", {
      method: "POST",
      body: JSON.stringify({ entidade, usuario: user.usuario, email: user.email || "" })
    }),
  qualificationOptions: () => request<{ items: Row[] }>("/api/qualification/start-options"),
  pendingQualification: (kind: "geral" | "bpf") => request<{ items: Row[] }>(`/api/qualification/pending/${kind}`),
  questions: (kind: "geral" | "bpf") => request<{ items: Row[] }>(`/api/questions/${kind}`),
  saveCadastro: (id: number, fields: Row) =>
    request<{ message: string }>("/api/qualification/cadastro", {
      method: "POST",
      body: JSON.stringify({ id, fields })
    }),
  saveGeneral: (entidade_id: number, respostas: Row[]) =>
    request<any>("/api/qualification/general", {
      method: "POST",
      body: JSON.stringify({ entidade_id, respostas })
    }),
  saveBpf: (entidade_id: number, respostas: Row[]) =>
    request<any>("/api/qualification/bpf", {
      method: "POST",
      body: JSON.stringify({ entidade_id, respostas })
    }),
  courses: () => request<{ items: Row[] }>("/api/courses"),
  courseQuestions: (courseId: number) => request<{ items: Row[] }>(`/api/courses/${courseId}/questions`),
  protocols: () => request<{ items: Row[]; status: string[] }>("/api/protocols"),
  createProtocol: (payload: Row) =>
    request<any>("/api/protocols", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  advanceProtocol: (protocolo: string, usuario: string, observacao = "", data_agendada = "") =>
    request<any>(`/api/protocols/${protocolo}/advance`, {
      method: "POST",
      body: JSON.stringify({ usuario, observacao, data_agendada })
    }),
  cancelProtocol: (protocolo: string, usuario: string, observacao = "") =>
    request<any>(`/api/protocols/${protocolo}/cancel`, {
      method: "POST",
      body: JSON.stringify({ usuario, observacao })
    }),
  forms: (protocolo: string) => request<any>(`/api/forms/${protocolo}`),
  table: (table: string) => request<{ items: Row[] }>(`/api/admin/table/${table}`),
  saveTable: (table: string, rows: Row[]) =>
    request<any>(`/api/admin/table/${table}`, {
      method: "POST",
      body: JSON.stringify({ rows })
    })
};
