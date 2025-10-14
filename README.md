# 💼 DermaLux Bot — Assistente de Agendas no WhatsApp

Projeto que auxilia uma clínica fictícia (DermaLux) a gerenciar agendas e compromissos via WhatsApp.

O bot conversa de forma humanizada, cria/atualiza compromissos no Google Calendar, armazena histórico no Supabase e usa MCP (Model Context Protocol) para expor ferramentas ao ChatGPT.

## 🧭 Visão geral

Canal: WhatsApp (via Z-API).

IA (Agente): ChatGPT com ferramentas MCP (ex.: criar/deletar eventos).

Agenda: Google Calendar (com regras de negócio).

Dados: Supabase (mensagens, serviços, fallback).

Servidores:
- API Server (Flask) — recebe webhooks do WhatsApp e conversa com o agente
- MCP Server (FastMCP) — expõe tools (Calendar/DB/etc.) para o agente

## 🧱 Arquitetura
```
Cliente (WhatsApp)
      │
      ▼
   Z-API ──► API Server (Flask) ──► OpenAI (Agente)
                                   │
                                   ▼
                               MCP Server ──► Google Calendar
                                   │
                                   └──► Supabase (histórico, serviços, fallback)

```
## 🔌 Serviços & Funcionalidades

### 🔹 Z-API
Envia/recebe mensagens de texto do WhatsApp.
Buffer de mensagens: agrega mensagens recebidas num intervalo (~7s) e processa como um único bloco.

### 🔹 Google Calendar
Cria / deleta / atualiza eventos.

Regras:
- Salva nome de quem solicitou, serviço e telefone na descrição.
- Não deleta eventos criados por outro número.
- Não cria eventos no passado ou fora do horário de funcionamento.

### 🔹 Agente (ChatGPT)
- Responde de forma humanizada e toma ações usando ferramentas (via MCP).
- Fallback humano: cliente pode pedir atendente → desativa automação por 1 dia.
- Usa histórico (Supabase) e dados de serviços para personalizar respostas.

### 🔹 Supabase (Banco de Dados)
- Serviços: catálogo totalmente customizável.
- Messages: histórico completo (entrada/saída).
- Fallback: sinaliza se o bot está ativo ou pausado para aquele número.
Tabelas:
Histórico de mensagens
```
table messages (
  id bigserial not null,
  phone_number text not null,
  role text not null,
  content text not null,
  inserted_at timestamp with time zone not null default ((now() AT TIME ZONE 'America/Sao_Paulo'::text))::timestamp with time zone,
  constraint messages_pkey primary key (id)
);
```
Serviços disponíveis
```
table services (
  id bigserial not null,
  category text not null,
  service text not null,
  duration text not null,
  cost text not null,
  inserted_at timestamp with time zone not null default ((now() AT TIME ZONE 'America/Sao_Paulo'::text))::timestamp with time zone,
  description text null,
  constraint services_pkey primary key (id)
);
```
Informações de fallback e bot ativo em cada número
```
table customers (
  phone_number text not null,
  bot_active boolean not null,
  date_bot_disabled date null,
  bot_blocked boolean not null default false,
  nickname text null,
  constraint customers_pkey primary key (phone_number)
);
```



### 🔹 MCP Server (Tools)
Conecta o agente à agenda e ao banco de dados e expõe tools ao agente, por ex.:
```
  create_calendar_event(summary, description, start, minutes)
  delete_calendar_event(id)
  list_events(start, end) (opcional)
```

## 🔄 Fluxo básico

1. Cliente envia a mensagem para o WhatsApp
2. Mensagem chega via Z-API → API (Flask).
3. API aplica buffer (junta mensagens próximas).
4. API chama Agente (OpenAI) com contexto + histórico.
5. Agente usa MCP tools (Calendar/DB) conforme a intenção.
6. Resultado → API → envia resposta ao cliente via Z-API.
7. Tudo é persistido no Supabase.

## 🧑‍💻 Autor
Rodrigo Gomes
🔗 [LinkedIn](https://www.linkedin.com/in/rodrigogomes-profile/)
