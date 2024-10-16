from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
import sqlite3
from typing import List
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class BugReport(BaseModel):
    title: str
    description: str

class BugReportOut(BugReport):
    id: int

# Security scheme for Bearer Token
security = HTTPBearer()

def initialize_database():
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)
        conn.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    initialize_database()
    yield
    # Shutdown code (if any)

app = FastAPI(lifespan=lifespan)

# Function to verify the Bearer Token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Replace 'mysecrettoken' with your actual token or validation logic
    if token != "mysecrettoken":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Endpoint to create a new bug report
@app.post("/bugreports", response_model=BugReportOut, status_code=status.HTTP_201_CREATED)
def create_bug_report(
    bug_report: BugReport,
    token: str = Depends(verify_token)
):
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bug_reports (title, description) VALUES (?, ?)
        """, (bug_report.title, bug_report.description))
        conn.commit()
        bug_report_id = cursor.lastrowid
    return BugReportOut(id=bug_report_id, **bug_report.dict())

# Endpoint to list all bug reports
@app.get("/bugreports", response_model=List[BugReportOut])
def list_bug_reports(token: str = Depends(verify_token)):
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description FROM bug_reports
        """)
        rows = cursor.fetchall()
        bug_reports = [BugReportOut(id=row[0], title=row[1], description=row[2]) for row in rows]
    return bug_reports

# Endpoint to get a single bug report by ID
@app.get("/bugreports/{bug_report_id}", response_model=BugReportOut)
def get_bug_report(bug_report_id: int, token: str = Depends(verify_token)):
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description FROM bug_reports WHERE id = ?
            """, (bug_report_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug report not found"
            )
        bug_report = BugReportOut(id=row[0], title=row[1], description=row[2])
    return bug_report

# Endpoint to update an existing bug report
@app.put("/bugreports/{bug_report_id}", response_model=BugReportOut)
def update_bug_report(
    bug_report_id: int,
    bug_report: BugReport,
    token: str = Depends(verify_token)
):
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bug_reports SET title = ?, description = ? WHERE id = ?
        """, (bug_report.title, bug_report.description, bug_report_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug report not found"
            )
    return BugReportOut(id=bug_report_id, **bug_report.dict())

# Endpoint to delete a bug report
@app.delete("/bugreports/{bug_report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug_report(bug_report_id: int, token: str = Depends(verify_token)):
    with sqlite3.connect("bugreports.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM bug_reports WHERE id = ?
        """, (bug_report_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug report not found"
            )
    return
