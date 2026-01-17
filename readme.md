<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager v0.1.09

**TravelManager** é uma aplicação web robusta e inteligente desenvolvida para o gerenciamento completo de viagens pessoais e em grupo. Além de controlar despesas e itinerários, o sistema utiliza **Inteligência Artificial (OpenAI)** para atuar como um agente de viagens pessoal.

A versão **v0.1.09** traz um salto em maturidade técnica, com ambiente preparado para produção (**Gunicorn + WhiteNoise**), segurança reforçada via variáveis de ambiente, **recuperação de senha** completa e integração com **Google Calendar**.

---

## 📋 Índice

1. [Sobre o Projeto](#-sobre-o-projeto)
2. [Funcionalidades](#-funcionalidades)
3. [Inteligência Artificial](#-inteligência-artificial-genai)
4. [Tecnologias Utilizadas](#-tecnologias-utilizadas)
5. [Instalação e Configuração](#-instalação-e-configuração)
6. [Roadmap](#-roadmap)

---

## 📖 Sobre o Projeto

O **TravelManager** centraliza todas as informações de uma viagem. Com uma interface baseada no AdminLTE totalmente **responsiva (Mobile First)**, ele permite criar timelines detalhadas, visualizar gastos com conversão automática, armazenar documentos e compartilhar roteiros.

Nesta nova versão, o foco foi a **estabilidade e segurança**, migrando configurações sensíveis para variáveis de ambiente e implementando fluxos automatizados de versionamento e deploy.

![Screenshot do Infográfico](app/core/static/img/infografico6.png)

---

## 🚀 Funcionalidades

### 🌍 Gestão de Roteiros & Integrações
* **Timeline "Dia a Dia":** Visualização cronológica com mapas interativos e geocoding.
* **Integração Google Calendar (Novo):** Exportação direta do roteiro para sua agenda pessoal.
* **Checklists Inteligentes:** Criação de listas com sugestões via IA.

### 💰 Gestão Financeira (Atualizado)
* **Dashboard Financeiro:** Gráficos interativos (Rosca/Barras) com filtros dinâmicos.
* **Conversão Automática:** Cotação de moedas em tempo real.
* **Bandeiras e Ícones:** Visualização rápida dos países visitados no histórico financeiro.

### 🔒 Segurança e Infraestrutura (Novo)
* **Recuperação de Senha:** Fluxo completo (Solicitação > E-mail > Nova Senha) seguro e criptografado.
* **Configuração Segura:** Todas as chaves (API, Secret Key, Debug) movidas para variáveis de ambiente (`.env`).
* **Servidor de Produção:** Execução otimizada via **Gunicorn** servindo arquivos estáticos com **WhiteNoise**.
* **Logs de Acesso:** Auditoria de Login/Logout com rastreamento de IP.

### 🤖 Inteligência Artificial (GenAI)
* **Insights de Destino:** Dicas de voltagem, gorjetas, segurança e frases úteis.
* **Roteiros Automáticos:** Sugestão de atividades baseada no perfil do usuário.

---

## 🛠 Tecnologias Utilizadas

* **Backend:** Python 3.11, Django 5.2
* **Servidor de Aplicação:** Gunicorn (WSGI) + WhiteNoise
* **Banco de Dados:** PostgreSQL
* **Frontend:** HTML5, Bootstrap 4, AdminLTE 3 (Mobile First), jQuery
* **APIs:** OpenAI (GPT-4o/Mini), Google Maps Platform, WeatherAPI
* **Infraestrutura:** Docker, Docker Compose, Portainer (Gestão de Env)
* **Automação:** Scripts Bash para versionamento semântico e release notes.

---

## ⚙ Instalação e Configuração

### Pré-requisitos
* Docker e Docker Compose instalados.
* Chaves de API (OpenAI, Google Maps, WeatherAPI).

### 1. Clonar o repositório
```bash
git clone [https://github.com/seu-usuario/travel-manager.git](https://github.com/seu-usuario/travel-manager.git)
cd travel-manager

```

### 2. Configurar Variáveis de Ambiente (Crítico na v0.1.09)

Crie um arquivo `.env` na raiz ou configure no seu gerenciador (Portainer) com as seguintes chaves. **O sistema não rodará sem isso.**

```ini
# --- Django ---
DJANGO_SECRET_KEY=sua_chave_secreta_aqui
DJANGO_DEBUG=True  # Use False em produção
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,seu-dominio.com

# --- Banco de Dados ---
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=travel_db
SQL_USER=travel_user
SQL_PASSWORD=travel_password
SQL_HOST=db
SQL_PORT=5432

# --- APIs Externas ---
GOOGLE_MAPS_API_KEY=sua_chave_google
WEATHER_API_KEY=sua_chave_clima
OPENAI_API_KEY=sua_chave_openai

```

### 3. Executar com Docker Compose

O comando abaixo fará o build da imagem (agora com Gunicorn) e subirá os containers.

```bash
docker compose up -d --build

```

Acesse: `http://localhost:8000`

---

## 🗺 Roadmap

Abaixo, o status atual das funcionalidades.

### ✅ Concluído (v0.1.09)

* [x] **Infraestrutura de Produção:** Migração para Gunicorn e `settings.py` seguro.
* [x] **Recuperação de Senha:** Módulo completo com envio de e-mail SMTP.
* [x] **Integração Google Calendar:** Botão para exportar eventos.
* [x] **Dashboard Financeiro 2.0:** Novos filtros e visualização aprimorada.
* [x] **Automação de Versão:** Versionamento automático lendo `CHANGELOG.md`.
* [x] **Link de Changelog:** Página de histórico de versões acessível no rodapé.
* [x] **Integração com OpenAI:** Roteiros, Dicas e Checklist.
* [x] **Módulo Administrativo de E-mail:** Configuração SMTP visual.
* [x] **Logs de Acesso:** Auditoria de segurança.

### 🔜 Próximos Passos (Sugestões)

* [ ] **Divisão de Gastos (Splitwise):** Permitir indicar "quem pagou" uma despesa.
* [ ] **Login Social:** Autenticação via Google/Facebook.
* [ ] **Notificações Push:** Alertas via navegador para início de viagens.
* [ ] **Modo Offline:** PWA para acesso básico sem internet.

---

<p align="center">
<small>Desenvolvido por Carlos Henrique Viola - Versão 0.1.09</small>
</p>

```

```