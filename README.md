```text
README.md
```

---

# Sheet ↔ Jira MCP Agent

AI Agent sử dụng **Gemini + MCP (Model Context Protocol)** để thao tác và đồng bộ dữ liệu giữa **Google Sheets** và **Jira** thông qua **ngôn ngữ tự nhiên**.

Agent cho phép người dùng yêu cầu các tác vụ như:

* đọc dữ liệu từ Google Sheets
* lọc / sắp xếp / phân tích dữ liệu
* tìm kiếm và tạo issue Jira
* đồng bộ task từ Sheet → Jira
* đồng bộ Jira → Sheet
* thao tác dữ liệu trực tiếp trên Sheet

Tất cả được thực hiện bằng cách **LLM tự động gọi tools thông qua MCP**.

---

# Kiến trúc hệ thống

```
User
  │
  ▼
Gemini LLM Agent
  │
  ▼
Tool Registry
  │
  ├── Sheet Tools
  │       ├── sheet_get_data
  │       ├── sheet_update_cells
  │       └── sheet_list_sheets
  │
  ├── Jira Tools
  │       ├── jira_search_issues
  │       ├── jira_get_issue
  │       ├── jira_create_issue
  │       └── jira_get_projects
  │
  └── Workflow Tools
          ├── sync_sheet_to_jira
          └── sync_jira_to_sheet
  │
  ▼
MCP Clients
  │
  ├── Google Sheets MCP
  └── Atlassian Jira MCP
  │
  ▼
External Services
  ├── Google Sheets
  └── Jira
```

---

# Tính năng chính

### 1. AI Agent điều khiển bằng ngôn ngữ tự nhiên

Ví dụ:

```
Đọc dữ liệu từ sheet Tasks
```

```
Lọc các task priority cao
```

```
Đồng bộ các task chưa có Jira key sang Jira
```

```
Tìm các issue Jira đang Blocked
```

---

### 2. Thao tác Google Sheets

Agent có thể:

* đọc dữ liệu sheet
* cập nhật cell
* liệt kê tab
* phân tích dữ liệu
* lọc / sắp xếp

Tools:

```
sheet_list_sheets
sheet_get_data
sheet_update_cells
```

---

### 3. Thao tác Jira

Agent có thể:

* tìm issue
* lấy thông tin issue
* tạo issue mới
* liệt kê project

Tools:

```
jira_search_issues
jira_get_issue
jira_create_issue
jira_get_projects
```

---

### 4. Workflow đồng bộ

Agent hỗ trợ các workflow:

```
sync_sheet_to_jira
sync_jira_to_sheet
```

Ví dụ:

```
Đồng bộ các task từ sheet sang Jira
```

---

# Cấu trúc project

```
app
│
├── agent
│   └── orchestrator.py
│
├── llm
│   ├── gemini_agent.py
│   └── prompts.py
│
├── mcp
│   ├── http_client.py
│   ├── stdio_client.py
│   ├── sheets_client.py
│   └── jira_client.py
│
├── tools
│   ├── raw_sheet_tools.py
│   ├── raw_jira_tools.py
│   ├── sync_tools.py
│   └── registry.py
│
├── utils
│   └── logger.py
│
└── main.py
```

---

# Yêu cầu hệ thống

* Python **3.12**
* uv / pip
* Google Gemini API key
* Google Service Account
* Jira API token

---

# Cài đặt

### 1. Clone project

```
git clone <repo>
cd sheet-jira-agent
```

---

### 2. Tạo virtual environment

```
uv .venv
```

Activate:

Windows

```
.venv\Scripts\activate
```

Linux / Mac

```
source .venv/bin/activate
```

---

### 3. Cài dependencies

```
uv pip install -r requirements.txt
```

---

# Cấu hình môi trường

Tạo file:

```
.env
```

Ví dụ:

```
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@example.com
JIRA_API_TOKEN=YOUR_API_TOKEN

SERVICE_ACCOUNT_PATH=service-account.json

DEFAULT_SPREADSHEET_ID=YOUR_SPREADSHEET_ID
DEFAULT_TASKS_SHEET=Tasks

DEFAULT_JIRA_PROJECT_KEY=KAN
DEFAULT_JIRA_ISSUE_TYPE=Task

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```

---

# Thiết lập Google Sheets

1. Tạo **Google Cloud Service Account**

2. Tải file:

```
service-account.json
```

3. Share Google Sheet cho service account email:

```
xxxxx@xxxxx.iam.gserviceaccount.com
```

---

# Thiết lập Jira

Tạo API token:

```
https://id.atlassian.com/manage-profile/security/api-tokens
```

Sau đó cấu hình:

```
JIRA_USERNAME
JIRA_API_TOKEN
```

---

# Khởi động MCP Servers

### Google Sheets MCP

Agent sẽ tự khởi động:

```
mcp-google-sheets
```

---

### Jira MCP

Chạy riêng một terminal:

```
uvx --python=3.12 mcp-atlassian \
--transport streamable-http \
--port 9000
```

---

# Chạy AI Agent

```
python -m app.main
```

---

# Ví dụ sử dụng

Agent sẽ mở CLI:

```
Gemini MCP Agent started.
```

---

### Lấy dữ liệu sheet

```
Đọc dữ liệu từ tab Tasks
```

---

### Tìm issue Jira

```
Tìm các issue mới nhất trong project KAN
```

---

### Tạo issue Jira

```
Tạo issue Jira với summary "Fix login bug"
```

---

### Đồng bộ sheet → Jira

```
Đồng bộ các task chưa có Jira key sang Jira
```

---

# Bảo mật

Không commit các file sau:

```
.env
service-account.json
```

Thêm vào `.gitignore`:

```
.env
service-account.json
.venv
```

---

# Roadmap

Planned features:

* filter / sort sheet tasks
* automatic Jira ↔ Sheet reconciliation
* vector search over sheet data
* Slack / Telegram integration
* Web UI dashboard
* multi-sheet support
* multi-project Jira sync

---

# Công nghệ sử dụng

* **Gemini API**
* **Model Context Protocol (MCP)**
* **Google Sheets MCP**
* **Atlassian MCP**
* **Python AsyncIO**
* **httpx**

---

# Ý tưởng

Project này triển khai mô hình:

```
LLM Tool-Using Agent
```

Trong đó:

* LLM hiểu yêu cầu tự nhiên
* tự động chọn tool
* gọi tool qua MCP
* thực thi thao tác trên hệ thống thật

---

# License

MIT License

---
