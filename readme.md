<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager v0.079

**TravelManager** é uma aplicação web robusta e inteligente desenvolvida para o gerenciamento completo de viagens pessoais e em grupo. Além de controlar despesas e itinerários, o sistema utiliza **Inteligência Artificial (OpenAI)** para atuar como um agente de viagens pessoal e agora permite **Colaboração em Tempo Real** e **Gestão de Memórias Fotográficas**.

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

O **TravelManager** centraliza todas as informações de uma viagem. Com uma interface baseada no AdminLTE agora **totalmente responsiva (Mobile First)**, ele permite criar timelines detalhadas, visualizar gastos com conversão automática, armazenar documentos e fotos, e compartilhar roteiros com amigos e familiares com níveis de permissão distintos.

---

## 🚀 Funcionalidades

### 🌍 Gestão de Roteiros
* **Timeline Interativa:** Visualização cronológica com ícones intuitivos (Voo, Hotel, Trem, Ônibus, Restaurante).
* **Identificação Visual:** Detecção automática de bandeiras dos países e previsão do tempo integrada na timeline.
* **Mapas Dinâmicos:** Integração com Google Maps para visualizar trajetos e locais específicos.

### 👥 Colaboração e Compartilhamento (NOVO)
* **Convite de Usuários:** Compartilhe viagens com outros usuários cadastrados via e-mail.
* **Permissões Granulares:**
    * **Leitor:** Apenas visualiza o roteiro e fotos.
    * **Editor:** Pode adicionar itens, editar gastos e subir fotos.
    * **Dono:** Controle total e gestão de acessos.

### 📸 Galeria de Fotos (NOVO)
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

1.  **Planejador Automático:** Cria roteiros dia-a-dia baseados no destino, duração e interesses do usuário, respeitando a lógica de dias da viagem.
2.  **Guia de Bolso:** Gera dicas culturais, frases úteis, voltagem de tomadas e etiqueta de gorjetas para o destino.
3.  **Checklist Inteligente:** Sugere o que levar na mala baseado no clima e tipo de viagem.

![Screenshot do Logo](app/core/static/img/infografico4.png)

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
│   │   ├── static
│   │   │   └── img
│   │   │       ├── infografico1.png
│   │   │       ├── infografico2.png
│   │   │       ├── infografico3.png
│   │   │       ├── logo-orinial.jpg
│   │   │       └── logo.png
│   │   ├── templates
│   │   │   ├── base.html
│   │   │   ├── config
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
* Chaves de API (OpenAI e Google Maps) - *Podem ser inseridas via interface após o login*.

### Configuração de Ambiente

Crie um arquivo `.env` na raiz (baseado no exemplo) ou ajuste as variáveis no `docker-compose-dev.yml`.

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

Acesse: `http://localhost:8080` (Ou via proxy reverso configurado).

---

## 🗺 Roadmap

Abaixo, o status atual das funcionalidades planejadas.

### ✅ Concluído (v0.079)

* [x] **Integração com OpenAI** (Roteiros, Dicas e Checklist).
* [x] **Exportação de Documentos** (PDF do Roteiro e Checklist).
* [x] **Gestão de Chaves de API** via banco de dados.
* [x] **Mapa Interativo** e Geocoding na timeline.
* [x] **Compartilhamento de Viagem:** Sistema de convites com permissões (Leitor/Editor).
* [x] **Galeria de Fotos:** Upload múltiplo e visualização organizada.
* [x] **Responsividade Mobile:** Ajustes de layout para acesso via celular.
* [x] **Ícones Expandidos:** Suporte para Trem e Ônibus na timeline.
* [x] **Feedback de UX:** Toasts de sucesso e Loading states nos botões de IA.

### 🔜 Próximos Passos (Sugestões)

* [ ] **Divisão de Gastos (Splitwise):** Permitir indicar "quem pagou" uma despesa e calcular o acerto de contas entre os viajantes.
* [ ] **Integração com Google Calendar:** Botão para exportar o roteiro (.ics) direto para a agenda do celular.
* [ ] **Notificações por E-mail:** Enviar alerta real via SMTP quando um usuário for convidado para uma viagem.
* [ ] **Login Social:** Autenticação via Google/Facebook (OAuth2).
* [ ] **Modo Offline (PWA):** Permitir visualizar o roteiro básico mesmo sem internet.
* [ ] **Parsing de E-mails:** (Avançado) Ler confirmações de voo/hotel encaminhadas e criar itens automaticamente.

```

## 👤 Autor

**Carlos Viola**

* Copyright © 2025. Todos os direitos reservados.

```

*Documentação gerada automaticamente com base na versão v0.0.79 do TravelManager.*

```