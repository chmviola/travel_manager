<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager

**TravelManager** é uma aplicação web robusta e inteligente desenvolvida para o gerenciamento completo de viagens pessoais. Além de controlar despesas e itinerários, o sistema agora utiliza **Inteligência Artificial (OpenAI)** para atuar como um agente de viagens pessoal, sugerindo roteiros, dicas culturais e gerando checklists automáticos.

---

## 📋 Índice

1. [Sobre o Projeto](#-sobre-o-projeto)
2. [Funcionalidades](#-funcionalidades)
3. [Inteligência Artificial](#-inteligência-artificial-genai)
4. [Tecnologias Utilizadas](#-tecnologias-utilizadas)
5. [Arquitetura e Persistência](#-arquitetura-e-persistência)
6. [Estrutura do Projeto](#-estrutura-do-projeto)
7. [Instalação e Configuração](#-instalação-e-configuração)
8. [Como Executar](#-como-executar)
9. [CI/CD e Deploy](#-cicd-e-deploy)
10. [Roadmap](#-roadmap)
11. [Autor](#-autor)

---

## 📖 Sobre o Projeto

O **TravelManager** centraliza todas as informações de uma viagem, eliminando a necessidade de planilhas dispersas. Com uma interface baseada no AdminLTE, ele permite criar timelines detalhadas, visualizar gastos com conversão automática de moedas e, agora, **gerar documentos em PDF** para impressão. O diferencial atual é a integração profunda com IA para automatizar o planejamento.

---

## 🚀 Funcionalidades

### ✈️ Gestão de Viagens & Documentos
* **CRUD Completo:** Gestão total de viagens e status.
* **Exportação PDF:**
    * **Roteiro Completo:** Gera um "Diário de Bordo" em PDF contendo cronograma dia a dia, resumo financeiro e dicas da IA.
    * **Checklist de Bagagem:** Gera lista de itens para impressão.
* **Identificação Visual:** Detecção automática de bandeiras baseada no destino.
* **Favicon Dinâmico:** Identidade visual consistente na navegação.

### 📅 Timeline Interativa
* **Planejador Automático:** Criação de itens de roteiro manuais ou via IA.
* **Mapas Integrados:** Visualização de timeline com pinos no Google Maps e geocodificação de endereços.
* **Previsão do Tempo:** Cache inteligente de dados meteorológicos para cada item do roteiro.

### ✅ Checklist Inteligente
* **Gerenciador de Malas:** Criação de listas de verificação por categorias (Roupas, Documentos, Eletrônicos).
* **Edição Flexível:** Adição de novas categorias (Box) e itens personalizados.
* **Limpeza Rápida:** Ferramenta para remover itens já marcados/concluídos.

### 💰 Gestão Financeira
* **Multi-moeda:** Suporte a USD, EUR, GBP, entre outras.
* **Conversão Real-Time:** Cotação automática para BRL baseada em APIs externas.
* **Dashboard:** Gráficos e tabelas detalhadas de gastos por categoria.

---

## 🤖 Inteligência Artificial (GenAI)

O sistema utiliza a API da OpenAI (GPT-4o-mini) para funcionalidades avançadas:

1.  **Planejador de Roteiros (Killer Feature):**
    * O usuário informa seus interesses (ex: "Gosto de museus e gastronomia, odeio baladas").
    * A IA gera uma timeline completa dia-a-dia com horários, locais e descrições, salvando diretamente no banco de dados.

2.  **Guia de Bolso (Trip Insights):**
    * Gera automaticamente um card com informações cruciais sobre o destino:
    * **Moeda & Gorjeta:** "No Japão não se dá gorjeta".
    * **Eletricidade:** "Tomada Tipo G, 230V".
    * **Frases Úteis:** "Bom dia", "Obrigado" na língua local.
    * **Segurança:** Dicas de áreas a evitar.

3.  **Checklist Generativo:**
    * Cria uma lista de bagagem sugerida baseada no clima, duração e propósito da viagem.

![Screenshot do Logo](app/core/static/img/infografico2.png)

---

## 🛠 Tecnologias Utilizadas

### Backend
* **Python 3.11+** & **Django 5.x**
* **PostgreSQL 15:** Banco de dados relacional.
* **OpenAI API:** Integração com GPT Models.
* **xhtml2pdf:** Motor de geração de relatórios PDF.

### Frontend
* **AdminLTE 3.2:** Interface administrativa responsiva.
* **Google Maps JavaScript API:** Mapas e Places.
* **Chart.js:** Visualização de dados financeiros.

---

## 🏗 Arquitetura e Persistência

O projeto roda inteiramente em Docker. Um ponto crucial da arquitetura é a **persistência dos arquivos de migração**.

### Mapeamento de Volumes (Migrations)
Para evitar a perda de histórico de banco de dados e garantir consistência entre ambientes, o diretório de migrações do Django é mapeado para volumes persistentes no host, separado do código do container.

* **Desenvolvimento (`docker-compose-dev.yml`):**
    * Caminho Host: `/var/data/migrations-dev`
    * Caminho Container: `/usr/src/app/core/migrations`
    * *Objetivo:* Permite rodar `makemigrations` dentro do container e persistir os arquivos `.py` gerados mesmo se o container for destruído.

* **Produção (`docker-compose.yml`):**
    * Caminho Host: `/var/data/migrations`
    * Caminho Container: `/usr/src/app/core/migrations`
    * *Objetivo:* Garante que o estado das migrações aplicadas em produção seja preservado.

---

## 📂 Estrutura do Projeto

```text
app
├── config                  # Configurações do Django (settings, urls)
├── core
│   ├── admin.py            # Registro de modelos no Admin
│   ├── forms.py            # Formulários (Trip, Expense, UserProfile)
│   ├── models.py           # Modelagem de dados (Trip, TripItem, Expense, APIConfiguration)
│   ├── static              # Arquivos estáticos (CSS, JS, Imagens)
│   ├── templates           # HTMLs (Baseados no AdminLTE)
│   │   ├── base.html
│   │   ├── config          # Templates de configuração (API, Perfil)
│   │   ├── trips           # Templates principais (Detalhes, Checklist, PDF)
│   │   │   ├── checklist_pdf.html
│   │   │   ├── trip_detail.html
│   │   │   ├── trip_pdf.html
│   │   │   └── ...
│   │   └── users
│   ├── utils.py            # Lógica de IA e integrações externas
│   └── views.py            # Controladores
├── Dockerfile
├── docker-compose-dev.yml  # Orquestração Dev
├── docker-compose.yml      # Orquestração Prod
└── requirements.txt

```

---

## 📝 Instalação e Configuração

### Configuração de APIs

O sistema possui um módulo administrativo interno (`/config/apis/`) para gerenciar chaves de API sem precisar reiniciar o servidor ou editar arquivos `.env`.

As seguintes chaves devem ser cadastradas no sistema:

1. **GOOGLE_MAPS_API:** Para mapas e geocoding.
2. **OPENAI_API:** Para funcionalidades de inteligência artificial.
3. **WEATHER_API:** (Opcional) Para previsão do tempo.

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

### ✅ Concluído

* [x] Integração com OpenAI (Roteiros e Dicas).
* [x] Sistema de Checklist (Edição e IA).
* [x] Exportação de Roteiro e Checklist em PDF.
* [x] Módulo de gestão de chaves de API no banco.
* [x] Correção de persistência de migrações via Docker Volumes.
* [x] Mapa interativo na timeline.

### 🔜 Próximos Passos (Backlog)

* [ ] **Integração com E-mail:** Envio automático do PDF do roteiro por e-mail.
* [ ] **Login Social:** Autenticação via Google/Facebook.
* [ ] **Upload de Fotos na Galeria:** Criar uma galeria de fotos da viagem além dos anexos documentais.
* [ ] **Link de Compartilhamento Público:** Gerar uma URL única "somente leitura" para compartilhar o roteiro com amigos.
* [ ] **Parsing de E-mails:** (Avançado) Ler confirmações de voo/hotel encaminhadas por e-mail e criar itens automaticamente.

---

## 👤 Autor

**Carlos Viola**

* Copyright © 2025. Todos os direitos reservados.

```

*Documentação gerada automaticamente com base na versão v0.0.60 do TravelManager.*

```

```