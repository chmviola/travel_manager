<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager v0.1.00

**TravelManager** é uma aplicação web robusta e inteligente desenvolvida para o gerenciamento completo de viagens pessoais e em grupo. Além de controlar despesas e itinerários, o sistema utiliza **Inteligência Artificial (OpenAI)** para atuar como um agente de viagens pessoal e agora conta com **Auditoria de Segurança**, **Configuração Dinâmica de E-mail** e uma **Timeline Otimizada**.

---

## 📋 Índice

1. [Sobre o Projeto](#-sobre-o-projeto)
2. [Funcionalidades](#-funcionalidades)
3. [Inteligência Artificial](#-inteligência-artificial-genai)
4. [Tecnologias Utilizadas](#-tecnologias-utilizadas)
5. [Estrutura do Projeto](#-estrutura-do-projeto)
6. [Instalação e Configuração](#-instalação-e-configuração)
7. [Como Executar](#-como-executar)
8. [Roadmap](#-roadmap)

---

## 📖 Sobre o Projeto

O **TravelManager** centraliza todas as informações de uma viagem. Com uma interface baseada no AdminLTE agora **totalmente responsiva (Mobile First)**, ele permite criar timelines detalhadas dia a dia, visualizar gastos com conversão automática, armazenar documentos e fotos, e compartilhar roteiros com amigos e familiares com níveis de permissão distintos.

---

## 🚀 Funcionalidades

### 🌍 Gestão de Roteiros
* **Timeline "Dia a Dia" (NOVO):** Navegação otimizada por abas de datas. Carrega no mapa e na lista apenas os itens do dia selecionado, evitando poluição visual em viagens longas.
* **Identificação Visual:** Detecção automática de bandeiras dos países e previsão do tempo integrada.
* **Mapas Dinâmicos:** Integração com Google Maps para visualizar trajetos e locais específicos do dia.

### 🛡️ Administração & Segurança (NOVO)
* **Logs de Acesso:** Sistema de auditoria que registra todos os Logins e Logouts, capturando IP e data.
* **Filtros de Auditoria:** Ferramenta de busca nos logs para inspecionar o histórico de acesso de um usuário específico.
* **Configuração de E-mail (SMTP):** Interface visual para configurar o servidor de envio de e-mails (Host, Porta, Usuário, Senha, TLS/SSL) sem necessidade de alterar arquivos de código.

### 👥 Colaboração e Compartilhamento
* **Convite de Usuários:** Compartilhe viagens com outros usuários cadastrados.
* **Permissões Granulares:**
    * **Leitor:** Apenas visualiza o roteiro e fotos.
    * **Editor:** Pode adicionar itens, editar gastos e subir fotos.
    * **Dono:** Controle total e gestão de acessos.

### 📸 Galeria de Fotos
* **Upload Múltiplo:** Carregamento em massa de fotos da viagem.
* **Visualização Polaroid:** Grid responsivo com legendas e visualização em lightbox (modal).

### 💰 Gestão Financeira
* **Multi-moeda:** Suporte a diversas moedas (USD, EUR, GBP, etc.) com conversão automática para BRL baseada em cotação real.
* **Dashboard:** Gráficos de gastos por categoria (Hospedagem, Alimentação, Transporte).

### 📄 Documentos e Exportação
* **Anexos:** Armazenamento de vouchers e bilhetes (PDF, Imagens).
* **Exportação PDF:** Gere um roteiro impresso formatado profissionalmente ou um Checklist de viagem.

---

## 🤖 Inteligência Artificial (GenAI)

O sistema utiliza a API da OpenAI (GPT-4o-mini) para recursos avançados:

1.  **Planejador Automático:** Cria roteiros baseados no destino, duração e interesses.
2.  **Guia de Bolso Aprimorado:** Gera dicas culturais, frases úteis, voltagem, gorjetas e agora inclui **Gastronomia Típica** (pratos imperdíveis do local).
3.  **Checklist Inteligente:** Sugere o que levar na mala baseado no clima e tipo de viagem.

![Screenshot do Infográfico](app/core/static/img/infografico5.png)

---

## 🛠 Tecnologias Utilizadas

* **Backend:** Python 3.11, Django 5.2.
* **Banco de Dados:** PostgreSQL 13.
* **Frontend:** HTML5, CSS3, Bootstrap 4, AdminLTE 3 (Responsivo), jQuery.
* **Containerização:** Docker & Docker Compose.
* **Mapas:** Google Maps JavaScript API & Geocoding API.
* **AI:** OpenAI API (GPT Models).
* **Imagens/PDF:** Pillow, xhtml2pdf.

---

## 📂 Estrutura do Projeto

```text
├── app
│   ├── config
│   │   ├── asgi.py
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── core
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── context_processors.py
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── signals.py                <-- NOVO (Lógica de Logs)
│   │   ├── static
│   │   │   └── img
│   │   │       ├── ...
│   │   ├── templates
│   │   │   ├── base.html
│   │   │   ├── config
│   │   │   │   ├── access_logs.html  <-- NOVO (Auditoria)
│   │   │   │   ├── email_settings.html <-- NOVO (SMTP)
│   │   │   │   ├── api_form.html
│   │   │   │   ├── api_list.html
│   │   │   │   └── profile.html
│   │   │   ├── dashboard.html
│   │   │   ├── financial_dashboard.html
│   │   │   ├── index.html
│   │   │   ├── login.html
│   │   │   ├── trips
│   │   │   │   ├── attachment_list.html
│   │   │   │   ├── checklist.html
│   │   │   │   ├── checklist_pdf.html
│   │   │   │   ├── expense_form.html
│   │   │   │   ├── trip_confirm_delete.html
│   │   │   │   ├── trip_detail.html
│   │   │   │   ├── trip_form.html
│   │   │   │   ├── trip_gallery.html
│   │   │   │   ├── trip_item_confirm_delete.html
│   │   │   │   ├── trip_item_form.html
│   │   │   │   ├── trip_list.html
│   │   │   │   └── trip_pdf.html
│   │   │   └── users
│   │   │       ├── user_form.html
│   │   │       └── user_list.html
│   │   ├── templatetags
│   │   │   ├── core_extras.py
│   │   │   └── __init__.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── utils.py
│   │   └── views.py
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── docker-compose-dev.yml
├── docker-compose.yml
├── Jenkinsfile
├── Jenkinsfile-dev
├── migrate.sh
├── readme.md
└── setup_travel.sh

```

---

## ⚙️ Instalação e Configuração

### Pré-requisitos

* Docker e Docker Compose instalados.

### Configuração de Ambiente

Crie um arquivo `.env` na raiz ou ajuste as variáveis no `docker-compose-dev.yml`.

As configurações sensíveis (OpenAI Key, Google Maps Key, SMTP) agora são gerenciadas **diretamente pela interface administrativa** após o primeiro login.

---

## ▶️ Como Executar

### Ambiente de Desenvolvimento

```bash
docker compose -f docker-compose-dev.yml up -d --build

```

Acesse: `http://localhost:8000`

### Ambiente de Produção

```bash
docker compose -f docker-compose.yml up -d --build

```

Acesse: `http://localhost:8080`

---

## 🗺 Roadmap

Abaixo, o status atual das funcionalidades.

### ✅ Concluído (v0.080)

* [x] **Integração com OpenAI** (Roteiros, Dicas e Checklist).
* [x] **Guia de Bolso Expandido** (Inclusão de Gastronomia e formatação automática).
* [x] **Timeline "Dia a Dia"** (Navegação por abas de data e filtro de mapa).
* [x] **Módulo Administrativo de E-mail** (Configuração SMTP visual).
* [x] **Logs de Acesso** (Registro de Login/Logout com filtros por usuário).
* [x] **Exportação de Documentos** (PDF do Roteiro e Checklist).
* [x] **Mapa Interativo** e Geocoding na timeline.
* [x] **Compartilhamento de Viagem:** Sistema de convites com permissões.
* [x] **Galeria de Fotos:** Upload múltiplo e visualização organizada.
* [x] **Responsividade Mobile:** Ajustes de layout para acesso via celular.

### 🔜 Próximos Passos (Sugestões)

* [ ] **Divisão de Gastos (Splitwise):** Permitir indicar "quem pagou" uma despesa.
* [ ] **Integração com Google Calendar:** Botão para exportar o roteiro (.ics).
* [ ] **Notificações por E-mail:** Enviar alerta real via SMTP (usando a nova config).
* [ ] **Login Social:** Autenticação via Google/Facebook (OAuth2).
* [ ] **Modo Offline (PWA):** Visualizar roteiro sem internet.

```

## 👤 Autor

**Carlos Viola**

* Copyright © 2026. Todos os direitos reservados.


```

*Documentação gerada automaticamente com base na versão v0.1.00 do TravelManager.*

```

```