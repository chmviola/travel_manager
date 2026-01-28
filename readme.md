<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager v0.1.21

**TravelManager** é uma aplicação web robusta e inteligente desenvolvida para o gerenciamento completo de viagens pessoais e em grupo. Além de controlar despesas e itinerários, o sistema utiliza **Inteligência Artificial (OpenAI)** para atuar como um agente de viagens pessoal.

A versão **v0.1.21** consolida o sistema como uma ferramenta de automação completa, introduzindo um **Sistema de Lembretes Inteligentes**, um **Calendário Interativo** aprimorado e maior estabilidade na gestão de câmbio e finanças.

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

Nesta nova iteração, o foco foi a **experiência do usuário e automação**, garantindo que o viajante seja notificado sobre eventos críticos e tenha acesso rápido às informações através de modais interativos no calendário.

![Screenshot do Infográfico](app/core/static/img/infografico.png)

---

## 🗺 Roadmap

Abaixo, o status atual das funcionalidades.

### ✅ Concluído (v0.1.21)

* [x] **Sistema de Lembretes:** Notificações automáticas por e-mail com antecedência configurável (de 1 hora até 1 mês antes do evento).
* [x] **E-mails Transacionais:** Templates HTML personalizados para lembretes, incluindo links diretos para mapas, documentos e detalhes da viagem.
* [x] **Calendário Interativo:** Visualização de detalhes dos itens (voos, hotéis, etc.) em modais flutuantes diretamente no calendário, sem troca de página.
* [x] **Cotações Resilientes:** Script de câmbio aprimorado com sistema de cache (mantém a última cotação válida em caso de falha na API externa).
* [x] **Gestão Financeira Inteligente:** Filtros de gastos restringidos ao contexto da viagem específica e interface de pagamento (Pago/Pendente) simplificada.
* [x] **Integração Google Calendar:** Exportação e sincronização de eventos de viagem.
* [x] **Recuperação de Senha:** Fluxo completo via e-mail com tokens de segurança.
* [x] **Integração com OpenAI:** Geração de roteiros, dicas de viagem e checklists personalizados via IA.
* [x] **Infraestrutura de Produção:** Ambiente preparado com Gunicorn, WhiteNoise e configurações de segurança.

### 🔜 Próximos Passos

* [ ] **Divisão de Gastos (Splitwise):** Permitir dividir despesas entre colaboradores da viagem.
* [ ] **Modo Offline (PWA):** Acesso básico às informações do roteiro sem conexão com internet.
* [ ] **Gestão de Bagagem:** Checklist visual de itens por categoria com peso estimado.

---

## 🛠 Tecnologias Utilizadas

* **Backend:** Python 3.11+ / Django 5.x
* **Frontend:** AdminLTE 3 (Bootstrap 4), jQuery, FullCalendar
* **Banco de Dados:** PostgreSQL (Produção) / SQLite (Desenvolvimento)
* **IA:** OpenAI API (GPT-4o / GPT-3.5)
* **Infraestrutura:** Docker & Docker Compose, Gunicorn
* **APIs:** AwesomeAPI (Câmbio), Google Maps, OpenWeatherMap

---

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone [https://github.com/seu-usuario/travelmanager.git](https://github.com/seu-usuario/travelmanager.git)
cd travelmanager

```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DEBUG=False
SECRET_KEY=sua_chave_secrea
ALLOWED_HOSTS=localhost,127.0.0.1

# --- Banco de Dados ---
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=travel_db
SQL_USER=postgres
SQL_PASSWORD=postgres
SQL_HOST=db
SQL_PORT=5432

# --- APIs Externas ---
GOOGLE_MAPS_API_KEY=sua_chave_google
WEATHER_API_KEY=sua_chave_clima
OPENAI_API_KEY=sua_chave_openai

```

### 3. Executar com Docker Compose

```bash
docker compose up -d --build

```

Acesse: `http://localhost:8000`

```
---

Desenvolvido por Carlos Henrique Viola - Versão 0.1.21

```

```