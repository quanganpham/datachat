# Vanna AI SQL Agent

A natural language SQL agent powered by **Vanna AI 2.0** and **OpenAI GPT-4o**.

Ask questions in plain English and get SQL results, charts, and insights!

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and set your API key:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Create Sample Database

```bash
python setup_database.py
```

This creates a sample SQLite database with:
- 8 departments
- 50 employees
- 12 projects

### 4. Run the Agent

```bash
python main.py
```

### 5. Open the Web Interface

Navigate to: **http://localhost:8000**

## Sample Queries

Try these natural language queries:

- "Show all employees"
- "What is the average salary by department?"
- "List all projects that are in progress"
- "Which department has the highest budget?"
- "Show me employees hired in 2024"
- "What's the total budget across all departments?"
- "Who are the highest paid employees?"
- "Show me a chart of employees per department"

## User Roles

| Role | Email | Permissions |
|------|-------|-------------|
| Admin | `admin@example.com` | See SQL, save memory, full access |
| User | Any other email | Query and visualize only |

To switch users, set the `vanna_email` cookie in your browser.

## Project Structure

```
vanna_sql_agent/
├── main.py           # Main application
├── config.py         # Configuration settings
├── setup_database.py # Database setup script
├── sample_data.db    # SQLite database (created)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
└── README.md         # This file
```

## Configuration

Edit `config.py` to customize:

- **OPENAI_MODEL**: Change to `gpt-4o-mini` for faster/cheaper responses
- **DATABASE_PATH**: Point to your own SQLite database
- **HOST/PORT**: Change server binding
- **ADMIN_EMAILS**: Add admin users

## Features

- 🗣️ **Natural Language to SQL** - Ask in English, get SQL results
- 📊 **Auto Visualization** - Charts generated from query results
- 🧠 **Agent Memory** - Learns from past interactions
- 🔐 **User Authentication** - Role-based access control
- ⚡ **Real-time Streaming** - Live responses
- 🌐 **Beautiful Web UI** - Pre-built chat component
