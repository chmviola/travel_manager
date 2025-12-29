<p align="center">
  <img src="app/core/static/img/logo.png" alt="Logo do App" width="200">
</p>

# TravelManager

**TravelManager** é uma aplicação web robusta desenvolvida para gerenciamento completo de viagens pessoais. O sistema permite planejar roteiros detalhados, controlar despesas em múltiplas moedas e visualizar itinerários de forma interativa.

---

## 📋 Índice

1. [Sobre o Projeto](https://www.google.com/search?q=%23-sobre-o-projeto)
2. [Funcionalidades](https://www.google.com/search?q=%23-funcionalidades)
3. [Tecnologias Utilizadas](https://www.google.com/search?q=%23-tecnologias-utilizadas)
4. [Arquitetura e Infraestrutura](https://www.google.com/search?q=%23-arquitetura-e-infraestrutura)
5. [Estrutura do Projeto](https://www.google.com/search?q=%23-estrutura-do-projeto)
6. [Instalação e Configuração](https://www.google.com/search?q=%23-instala%C3%A7%C3%A3o-e-configura%C3%A7%C3%A3o)
7. [Como Executar](https://www.google.com/search?q=%23-como-executar)
8. [Comandos Úteis](https://www.google.com/search?q=%23-comandos-%C3%BAteis)
9. [CI/CD e Deploy](https://www.google.com/search?q=%23-cicd-e-deploy)
10. [Roadmap](https://www.google.com/search?q=%23-roadmap)
11. [Autor](https://www.google.com/search?q=%23-autor)

---

## 📖 Sobre o Projeto

O **TravelManager** nasceu da necessidade de centralizar todas as informações de uma viagem em um único local, substituindo planilhas complexas e documentos dispersos. O objetivo é oferecer uma interface amigável (baseada no AdminLTE) para criar timelines de viagem, visualizar locais no mapa e, crucialmente, gerenciar o orçamento com conversão automática de moedas para Real (BRL).

---

## 🚀 Funcionalidades

### ✈️ Gestão de Viagens

* **CRUD Completo:** Criação, leitura, atualização e exclusão de viagens.
* **Status da Viagem:** Controle visual (Planejada, Confirmada, Concluída).
* **Identificação Visual:** Detecção automática de países baseada nos endereços cadastrados, exibindo as respectivas bandeiras nos cards e detalhes da viagem.

### 📅 Timeline e Itinerário

* **Linha do Tempo Visual:** Organização cronológica de eventos (Voos, Hotéis, Restaurantes, Atividades).
* **Categorização:** Ícones e cores distintas para cada tipo de atividade.
* **Integração com Mapas:** Visualização de endereços e coordenadas via Google Maps API (Modal e Links).
* **Detalhes Extras:** Campo de notas inteligente que processa dados JSON legados e formata textos com quebras de linha.

### 💰 Gestão Financeira

* **Multi-moeda:** Registro de gastos em diversas moedas (USD, EUR, GBP, etc.).
* **Conversão Automática:** Cálculo estimativo do valor em BRL baseado em taxas de câmbio configuráveis.
* **Dashboard Financeiro:**
* KPIs de gastos totais, gastos do ano corrente e contagem de lançamentos.
* Gráficos interativos (Donut e Barras) por categoria e por viagem.
* Tabela detalhada (DataTables) com ordenação, pesquisa e exportação (PDF, Excel).



### 🔐 Usuários e Segurança

* **Autenticação:** Sistema de login seguro.
* **Perfil de Usuário:** Edição de dados pessoais e alteração de senha com validação rigorosa de complexidade (Regex).
* **Permissões:** Diferenciação entre usuários comuns e superusuários (Admin).

---

## 🛠 Tecnologias Utilizadas

### Backend

* **Python 3.11+**
* **Django 5.x:** Framework web principal.
* **PostgreSQL 15:** Banco de dados relacional (substituindo SQLite para maior robustez).

### Frontend

* **AdminLTE 3.2:** Template administrativo baseado em Bootstrap 4.
* **Jinja2 / Django Templates:** Motor de renderização.
* **Chart.js:** Para gráficos financeiros.
* **DataTables:** Para tabelas avançadas e ordenáveis.
* **Flag Icon CSS:** Para exibição dinâmica de bandeiras.
* **FontAwesome:** Ícones vetoriais.

### Infraestrutura

* **Docker & Docker Compose:** Containerização da aplicação e banco de dados.
* **Nginx:** Proxy reverso (geralmente configurado via Portainer/Host).
* **Google Maps API:** Geocoding e Maps JavaScript API.

![Screenshot do Logo](app/core/static/img/infografico1.png)

---

## 🏗 Arquitetura e Infraestrutura

O projeto utiliza uma arquitetura MVC (Model-View-Controller) padrão do Django, containerizada para fácil deploy.

* **Ambientes:** O projeto suporta ambientes de Desenvolvimento (`dev`) e Produção, controlados via arquivos `docker-compose` distintos.
* **Persistência:** Volumes Docker nomeados são utilizados para persistir dados do PostgreSQL (`travel_db_data`) e arquivos de mídia (`media_data`).

---

## 📂 Estrutura do Projeto

```text
travel_manager/
├── app/                        # Código fonte da aplicação Django
│   ├── config/                 # Configurações globais (settings.py, urls.py)
│   ├── core/                   # App principal
│   │   ├── migrations/         # Histórico de banco de dados
│   │   ├── static/             # Arquivos CSS, JS, Imagens (Logo)
│   │   ├── templates/          # Arquivos HTML (AdminLTE extendido)
│   │   ├── templatetags/       # Filtros customizados (core_extras.py)
│   │   ├── forms.py            # Formulários e validações
│   │   ├── models.py           # Modelagem do banco de dados
│   │   ├── views.py            # Lógica de negócio e Views
│   │   └── utils.py            # Utilitários (ex: conversão de moeda)
│   ├── manage.py
│   └── Dockerfile              # Definição da imagem Python
├── docker-compose.yml          # Orquestração (Produção)
├── docker-compose-dev.yml      # Orquestração (Desenvolvimento)
├── Jenkinsfile                 # Pipeline CI/CD (Produção)
├── Jenkinsfile-dev             # Pipeline CI/CD (Desenvolvimento)
├── .env                        # Variáveis de ambiente (não versionado)
└── README.md                   # Documentação

```

---

## 📝 Instalação e Configuração

### Pré-requisitos

* Docker e Docker Compose instalados.
* Git instalado.
* Uma chave de API do Google Maps válida.

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/travel_manager.git
cd travel_manager

```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (ou configure as variáveis no seu ambiente de CI/CD/Docker).

| Variável | Descrição | Exemplo |
| --- | --- | --- |
| `DEBUG` | Modo de depuração (1 para True, 0 para False) | `1` |
| `SECRET_KEY` | Chave secreta do Django | `sua-chave-super-secreta` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos | `localhost 127.0.0.1 *` |
| `SQL_ENGINE` | Engine do Banco | `django.db.backends.postgresql` |
| `SQL_DATABASE` | Nome do Banco | `travel_db` |
| `SQL_USER` | Usuário do Banco | `travel_user` |
| `SQL_PASSWORD` | Senha do Banco | `travel_pass` |
| `SQL_HOST` | Host do Banco (Nome do serviço no Compose) | `travel_db_dev` |
| `SQL_PORT` | Porta do Banco | `5432` |
| `Maps_API_KEY` | Chave da API do Google | `AIzaSy...` |

---

## ▶️ Como Executar

### Ambiente de Desenvolvimento (Local)

Para rodar a aplicação localmente utilizando o arquivo de composição de desenvolvimento:

1. **Construir e subir os containers:**
```bash
docker compose -f docker-compose-dev.yml up -d --build

```


2. **Executar Migrações (Primeira vez):**
```bash
docker exec -it travel_manager_web_dev python manage.py migrate

```


3. **Criar Superusuário:**
```bash
docker exec -it travel_manager_web_dev python manage.py createsuperuser

```


4. **Acessar:**
Abra o navegador em `http://localhost:8000`.

### Ambiente de Produção

Geralmente gerenciado via Portainer/Jenkins, mas manualmente pode ser executado com:

```bash
docker compose -f docker-compose.yml up -d --build

```

A porta padrão de produção configurada é a `8080`.

---

## 💻 Comandos Úteis

Acesso ao Shell do container:

```bash
docker exec -it travel_manager_web_dev /bin/sh

```

Recarregar o Django (Reiniciar container):

```bash
docker restart travel_manager_web_dev

```

Fazer dump dos dados (Backup):

```bash
docker exec travel_manager_web_dev python manage.py dumpdata > backup.json

```

Limpar banco de dados (Flush):

```bash
docker exec -it travel_manager_web_dev python manage.py flush

```

---

## 🔄 CI/CD e Deploy

O projeto utiliza uma esteira automatizada de DevOps:

1. **GitHub:** O código é enviado para o repositório (branches `main` ou `develop`).
2. **Jenkins:** Detecta a alteração, valida a existência dos arquivos críticos (`docker-compose`, etc.).
3. **Portainer (Webhook):** O Jenkins aciona um Webhook no Portainer.
4. **Portainer (Stack):** O Portainer baixa a nova imagem/código do Git e atualiza a Stack automaticamente (re-pull), mantendo os volumes de dados persistentes.

---

## 🗺 Roadmap

* [ ] Integração com API de Clima para previsão do tempo nas datas da viagem.
* [X] Upload de anexos (PDFs de passagens/reservas) nos itens da timeline.
* [ ] Exportação do roteiro completo em PDF.
* [ ] Compartilhamento de viagem (Link público "somente leitura").
* [X] Widget de cotação de moedas em tempo real no Dashboard.

---

## 👤 Autor

**Carlos Viola**

* Copyright © 2025. Todos os direitos reservados.

---

*Documentação gerada automaticamente com base na versão v0.0.40 do TravelManager.*