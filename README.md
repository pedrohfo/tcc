# 📘 PROJETO TCC - Backend (Django) & Frontend (React)

Este projeto contém o **backend** desenvolvido em **Django + Django REST Framework** e o **frontend** desenvolvido em **React + Vite**.

---

## ⚙️ Requisitos

* Python 3.10+
* Node.js 18+
* npm ou yarn

---

## 🚀 Configuração do Backend (Django)

### 1. Criar e ativar ambiente virtual

No **Windows PowerShell**:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

> ⚠️ Se aparecer o erro `a execução de scripts foi desabilitada neste sistema.` execute:

```powershell
Set-ExecutionPolicy Unrestricted -Scope Process
```

### 2. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 3. Rodar migrações

```powershell
python manage.py migrate
```

### 4. Rodar servidor backend

```powershell
python manage.py runserver
```

Backend rodando em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🎨 Configuração do Frontend (React + Vite)

### 1. Entrar na pasta do frontend

```powershell
cd frontend
```

### 2. Instalar dependências

```powershell
npm install
```

### 3. Rodar servidor frontend

```powershell
npm run dev
```

Frontend rodando em: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 📦 Arquivos Importantes

* `requirements.txt` → Dependências do backend (Django)
* `package.json` → Dependências do frontend (React)
* `.gitignore` → Ignora arquivos desnecessários (inclui `.venv/` e `node_modules/`)

---

## 🛠️ Comandos úteis

### Atualizar dependências do backend

```powershell
pip freeze > requirements.txt
```

### Desativar ambiente virtual

```powershell
deactivate
```

---

## ✅ Resumo rápido

1. Criar `.venv` e ativar
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py runserver`
5. `cd frontend && npm install && npm run dev`
