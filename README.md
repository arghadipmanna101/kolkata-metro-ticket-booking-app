# 🚇 Kolkata Metro Booking & Verification System

> A full-stack transit routing, ticketing, and system-verification platform for the Kolkata Metro network — built with a dual-database architecture combining **PostgreSQL** for transactional data and **SQLite** for static graph topology.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-336791?logo=postgresql)
![SQLite](https://img.shields.io/badge/database-SQLite-003B57?logo=sqlite)

> **Disclaimer:** This is a fictional, dummy project created for a technical assessment. It is not affiliated with, endorsed by, or connected to Kolkata Metro Rail Corporation or any real transit authority.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Database Schema](#-database-schema)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [API Reference](#-api-reference)
- [Screenshots](#-screenshots)
- [Project Structure](#-project-structure)
- [Known Limitations](#-known-limitations)

---

## 🌟 Overview

This application lets users explore the Kolkata Metro network, calculate the fastest and cheapest route between any two stations — including line interchanges — and book digital QR tickets. Behind the scenes, a security gateway cross-verifies configuration fragments stored across **two separate databases** and a background worker thread before unlocking system access.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ **Smart Route Planner** | Computes the shortest path between any two stations using **Dijkstra's algorithm**, factoring in both train travel time and walking transfer time between lines. |
| 🔁 **Multi-Line Interchange Support** | Automatically detects and routes through line changes (e.g. Blue → Green at Esplanade), with transfer time built into the total journey. |
| 🎫 **Auto-Expiring QR Tickets** | A background scheduler thread runs every 60 seconds, automatically expiring tickets once their validity window passes. |
| 📊 **Live Ticket Dashboard** | View total bookings, active tickets, and expired tickets at a glance, with a detailed QR ticket viewer. |
| 🔐 **System Security Gateway** | A live diagnostic panel verifies system integrity by combining key fragments from PostgreSQL and SQLite, validated against a fresh worker heartbeat, before decrypting a clearance code (AES-256-CBC). |
| ⚡ **Real-Time Diagnostics** | Automatically polls system health every 15 seconds and displays pass/fail status for each verification check. |

---

## 🛠️ Tech Stack

**Frontend**
- React 18 + Vite
- Tailwind CSS
- Axios
- Lucide React (icons)

**Backend**
- Python 3.9+ / FastAPI
- SQLAlchemy (ORM)
- Uvicorn (ASGI server)
- `cryptography` (AES-256-CBC decryption)

**Databases**
- **PostgreSQL** — transactional data: tickets, system config, worker heartbeats
- **SQLite** — static graph data: stations, connections, interchanges, vault keys

---

## 🏗️ Architecture

```
┌─────────────────┐        REST API        ┌──────────────────┐
│   React + Vite   │ ───────────────────── │   FastAPI Backend │
│   (Port 5173)    │                        │    (Port 8000)    │
└─────────────────┘                        └─────────┬─────────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              │                                                  │
                     ┌────────▼─────────┐                              ┌─────────▼────────┐
                     │   PostgreSQL      │                              │      SQLite       │
                     │ ─────────────────│                              │ ──────────────────│
                     │ • system_config   │                              │ • stations         │
                     │ • worker_heartbeat│                              │ • connections       │
                     │ • tickets         │                              │ • interchanges      │
                     │ • users           │                              │ • vault_keys        │
                     └───────────────────┘                              └────────────────────┘
```

A background daemon thread (`cron_scheduler.py`) runs continuously alongside the FastAPI app, expiring stale tickets and refreshing the worker heartbeat every 60 seconds — this heartbeat is one of three checks the Security Gateway monitors in real time.

---

## 🗄️ Database Schema

The metro network is modeled as a **weighted directed graph**:

- **`stations`** — each station is a distinct node per line (e.g. *Esplanade (Blue)* and *Esplanade (Green)* are separate rows), enabling accurate interchange routing.
- **`connections`** — directed train-track edges between adjacent stations on the same line, weighted by travel time and fare.
- **`interchanges`** — directed walking-transfer edges between the same physical station on different lines, weighted by transfer time.

Full schema documentation: [`database_setup/sqlite_ddl_description.md`](./database_setup/sqlite_ddl_description.md)

The route-finding endpoint runs **Dijkstra's algorithm** over this graph, treating both train segments and walking transfers as weighted edges, and returns the minimum-time path between any two station names — correctly resolving to the optimal line when a station name exists on multiple lines.

---

## ✅ Prerequisites

Make sure you have the following installed:

| Tool | Minimum Version |
|---|---|
| [Node.js](https://nodejs.org/) & npm | v18+ |
| [Python](https://www.python.org/) & pip | v3.9+ |
| [PostgreSQL](https://www.postgresql.org/download/) | Running locally |

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd kolkata_metro_ticket_booking_app
```

### 2. PostgreSQL Setup

Create the database:
```sql
CREATE DATABASE kolkata_metro;
```

Run the schema initialization script:
```bash
psql -h localhost -U postgres -d kolkata_metro -f database_setup/postgres_init.sql
```
> Adjust `-U` (username) and `-h` (host) flags to match your local Postgres setup.

This creates the `system_config`, `worker_heartbeat`, `tickets`, and `users` tables, and seeds the required verification key fragment.

**SQLite** requires no setup — `backend/app/db/metadata_graph.db` ships pre-populated with the complete station dataset.

### 3. Backend Setup

```bash
cd backend
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL with your local Postgres credentials
```

### 4. Frontend Setup

```bash
cd ../frontend
npm install
cp .env.example .env   # confirms VITE_API_URL points to your backend
```

---

## 🔑 Environment Variables

**`backend/.env`**

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:yourpassword@localhost:5432/kolkata_metro` |
| `SECRET_KEY` | App secret key | `dev_secret_key_metro_booking_verification_2026` |

**`frontend/.env`**

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Base URL for backend API calls | `http://localhost:8000/api` |

> ⚠️ Both `.env` files are git-ignored. Always copy from the corresponding `.env.example` and fill in your local values — never commit real credentials.

---

## ▶️ Running the Application

**Start the backend** (from `backend/`, with venv activated):
```bash
uvicorn app.main:app --reload --port 8000
```
- API: `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`

**Start the frontend** (from `frontend/`, in a separate terminal):
```bash
npm run dev
```
- App: `http://localhost:5173`

> Both servers must be running simultaneously for the app to function.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/allstations` | Returns all metro stations with `id`, `name`, and `line`. |
| `GET` | `/api/route?source=X&destination=Y` | Computes the shortest route between two stations using Dijkstra's algorithm. Returns fare, travel time, interchange count, and full itinerary. |
| `GET` | `/api/status` | Runs the three-part system verification check and returns a decrypted clearance code if all checks pass. |
| `GET` | `/api/tickets` | Lists all booked tickets, newest first. |
| `POST` | `/api/tickets` | Books a new ticket for a given source, destination, and fare. |

Full interactive documentation available at `/docs` once the backend is running.

---

## 📸 Screenshots

<!-- Add your screenshots here, e.g.: -->
<!-- ![Route Planner](./screenshots/route-dakshineswar-vip-bazar.png) -->

| Route | Fare | Time | Interchanges |
|---|---|---|---|
| Dakshineswar → VIP Bazar | ₹115 | 60 min | 2 |
| Park Street → Howrah | ₹15 | 13 min | 1 |
| Thakurpukur → Eco Park | ₹130 | 66 min | 2 |

---

## 📁 Project Structure

```
kolkata_metro_ticket_booking_app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # All API endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Environment/settings loader
│   │   │   └── security.py        # AES decryption logic
│   │   ├── db/
│   │   │   ├── postgres_client.py # SQLAlchemy models & session
│   │   │   ├── sqlite_client.py   # SQLite connection helper
│   │   │   └── metadata_graph.db  # Station/graph data
│   │   ├── services/
│   │   │   ├── graph_engine.py    # Dijkstra route-finding logic
│   │   │   └── unlock_service.py  # System verification logic
│   │   ├── worker/
│   │   │   └── cron_scheduler.py  # Background heartbeat/ticket expiry
│   │   └── main.py                # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx      # Ticket registry & metrics
│   │   │   ├── RouteSelector.jsx  # Route planner UI
│   │   │   └── SystemStatus.jsx   # Verification gateway UI
│   │   ├── services/
│   │   │   └── api.js             # Axios API client
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
├── database_setup/
│   ├── postgres_init.sql
│   └── sqlite_ddl_description.md
├── TESTIMONIAL.md
└── README.md
```

---

## ⚠️ Known Limitations

- The `users` table and model exist in the schema but have no corresponding authentication endpoints — likely scaffolding for a future feature, left untouched to preserve the existing schema.
- Ticket booking has no real payment integration; fares are calculated but not charged.
- The background scheduler runs in-process as a daemon thread rather than a dedicated task queue, which is adequate for local development but wouldn't scale horizontally in production.

---

<div align="center">

Built as part of a technical assessment · See [`TESTIMONIAL.md`](./TESTIMONIAL.md) for the engineering approach and debugging journey.

</div>
