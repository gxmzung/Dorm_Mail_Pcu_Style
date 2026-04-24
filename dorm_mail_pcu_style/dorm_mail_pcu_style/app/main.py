from __future__ import annotations

import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional
from urllib.parse import quote, unquote

import qrcode
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "dorm_mail_pcu_style.db"
QR_DIR = BASE_DIR / "app" / "static" / "qr"

app = FastAPI(title="Dorm Mail PCU Style Demo", version="3.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def encode_cookie(value: str) -> str:
    return quote(value, safe="")


def decode_cookie(value: Optional[str]) -> str:
    return unquote(value) if value else ""


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def current_user(request: Request) -> Optional[dict]:
    role = request.cookies.get("role")
    if not role:
        return None
    return {
        "role": role,
        "student_name": decode_cookie(request.cookies.get("student_name")),
        "dorm_room": decode_cookie(request.cookies.get("dorm_room")),
    }


def make_pin() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def ensure_qr(token: str) -> str:
    QR_DIR.mkdir(parents=True, exist_ok=True)
    target = QR_DIR / f"{token}.png"
    if not target.exists():
        qrcode.make(token).save(target)
    return f"/static/qr/{token}.png"


def create_notification(
    conn: sqlite3.Connection,
    parcel_id: int,
    student_name: str,
    dorm_room: str,
    title: str,
    body: str,
) -> None:
    conn.execute(
        """
        INSERT INTO notifications (
            parcel_id, student_name, dorm_room, title, body, created_at, is_read
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (parcel_id, student_name, dorm_room, title, body, now_str()),
    )


def add_audit(
    conn: sqlite3.Connection,
    parcel_id: int,
    actor_role: str,
    actor_name: str,
    event_ko: str,
    detail: str,
) -> None:
    conn.execute(
        """
        INSERT INTO pickup_audit (
            parcel_id, actor_role, actor_name, event_ko, detail, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (parcel_id, actor_role, actor_name, event_ko, detail, now_str()),
    )


def init_db() -> None:
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS parcels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                dorm_room TEXT NOT NULL,
                carrier TEXT NOT NULL,
                item_type TEXT NOT NULL,
                arrived_at TEXT NOT NULL,
                pin_code TEXT NOT NULL,
                pickup_token TEXT NOT NULL,
                qr_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'READY',
                picked_up_at TEXT,
                notes TEXT,
                verified_by TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcel_id INTEGER,
                student_name TEXT NOT NULL,
                dorm_room TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pickup_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcel_id INTEGER NOT NULL,
                actor_role TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                event_ko TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        count = conn.execute("SELECT COUNT(*) AS c FROM parcels").fetchone()["c"]

        if count == 0:
            seeds = [
                ("김하늘", "여자기숙사 402호", "CJ대한통운", "택배 상자", "의류", "483921", "READY"),
                ("이수민", "여자기숙사 317호", "우체국", "등기 우편", "서류", "731204", "READY"),
                ("박지윤", "여자기숙사 508호", "한진택배", "소형 택배", "전자기기", "614538", "PICKED"),
            ]

            for student_name, dorm_room, carrier, item_type, notes, pin_code, status in seeds:
                token = uuid.uuid4().hex
                qr_path = ensure_qr(token)
                picked_up_at = now_str() if status == "PICKED" else None
                verified_by = "생활관 담당자" if status == "PICKED" else ""

                conn.execute(
                    """
                    INSERT INTO parcels (
                        student_name, dorm_room, carrier, item_type, arrived_at,
                        pin_code, pickup_token, qr_path, status, picked_up_at,
                        notes, verified_by
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        student_name,
                        dorm_room,
                        carrier,
                        item_type,
                        now_str(),
                        pin_code,
                        token,
                        qr_path,
                        status,
                        picked_up_at,
                        notes,
                        verified_by,
                    ),
                )

                parcel_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                create_notification(
                    conn,
                    parcel_id,
                    student_name,
                    dorm_room,
                    "우편물 도착 안내",
                    f"{carrier} {item_type} 1건이 도착했습니다. 수령 PIN과 QR 코드를 확인해 주세요.",
                )

                add_audit(conn, parcel_id, "system", "seed", "등록", f"{carrier} / {dorm_room}")

                if status == "PICKED":
                    add_audit(conn, parcel_id, "admin", "생활관 담당자", "수령 완료", "기본 예시 데이터")


def dashboard() -> dict:
    with db() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM parcels ORDER BY id DESC").fetchall()]
        notifications = [dict(r) for r in conn.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 8").fetchall()]
        recent_logs = [dict(r) for r in conn.execute("SELECT * FROM pickup_audit ORDER BY id DESC LIMIT 8").fetchall()]

    return {
        "rows": rows,
        "notifications": notifications,
        "recent_logs": recent_logs,
        "total": len(rows),
        "ready": sum(1 for r in rows if r["status"] == "READY"),
        "picked": sum(1 for r in rows if r["status"] == "PICKED"),
        "overdue": sum(1 for r in rows if r["status"] == "OVERDUE"),
    }


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(
        "landing.html",
        {"request": request, "user": current_user(request)},
    )


@app.post("/login/admin")
def login_admin():
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie("role", "admin")
    resp.set_cookie("student_name", "")
    resp.set_cookie("dorm_room", "")
    return resp


@app.post("/login/student")
def login_student(student_name: str = Form(...), dorm_room: str = Form(...)):
    resp = RedirectResponse("/student", status_code=303)
    resp.set_cookie("role", "student")
    resp.set_cookie("student_name", encode_cookie(student_name))
    resp.set_cookie("dorm_room", encode_cookie(dorm_room))
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    for key in ["role", "student_name", "dorm_room"]:
        resp.delete_cookie(key)
    return resp


@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": current_user(request), **dashboard()},
    )


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    user = current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "user": user, **dashboard()},
    )


@app.post("/admin/register")
def admin_register(
    student_name: str = Form(...),
    dorm_room: str = Form(...),
    carrier: str = Form(...),
    item_type: str = Form(...),
    notes: str = Form(""),
):
    token = uuid.uuid4().hex
    pin_code = make_pin()
    qr_path = ensure_qr(token)

    with db() as conn:
        conn.execute(
            """
            INSERT INTO parcels (
                student_name, dorm_room, carrier, item_type, arrived_at,
                pin_code, pickup_token, qr_path, status, notes, verified_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'READY', ?, '')
            """,
            (
                student_name,
                dorm_room,
                carrier,
                item_type,
                now_str(),
                pin_code,
                token,
                qr_path,
                notes,
            ),
        )

        parcel_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        create_notification(
            conn,
            parcel_id,
            student_name,
            dorm_room,
            "우편물 도착 안내",
            f"{carrier} {item_type} 1건이 도착했습니다. 수령 PIN {pin_code} 또는 QR 코드를 확인해 주세요.",
        )

        add_audit(conn, parcel_id, "admin", "생활관 담당자", "등록", f"{carrier} / {dorm_room}")

    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/confirm-pickup")
def admin_confirm_pickup(parcel_id: int = Form(...)):
    with db() as conn:
        row = conn.execute("SELECT * FROM parcels WHERE id = ?", (parcel_id,)).fetchone()
        if row and row["status"] != "PICKED":
            conn.execute(
                """
                UPDATE parcels
                SET status = 'PICKED', picked_up_at = ?, verified_by = '생활관 담당자'
                WHERE id = ?
                """,
                (now_str(), parcel_id),
            )
            add_audit(conn, parcel_id, "admin", "생활관 담당자", "수령 완료", "관리자 확인 처리")

    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/mark-overdue")
def admin_mark_overdue(parcel_id: int = Form(...)):
    with db() as conn:
        conn.execute(
            "UPDATE parcels SET status = 'OVERDUE' WHERE id = ? AND status = 'READY'",
            (parcel_id,),
        )
        add_audit(conn, parcel_id, "admin", "생활관 담당자", "미수령 분류", "일정 기간 미수령 물품 분류")

    return RedirectResponse("/admin", status_code=303)


@app.get("/student", response_class=HTMLResponse)
def student(request: Request):
    user = current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse("/", status_code=303)

    with db() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT * FROM parcels
                WHERE student_name = ? OR dorm_room = ?
                ORDER BY id DESC
                """,
                (user["student_name"], user["dorm_room"]),
            ).fetchall()
        ]

        notices = [
            dict(r)
            for r in conn.execute(
                """
                SELECT * FROM notifications
                WHERE student_name = ? OR dorm_room = ?
                ORDER BY id DESC
                """,
                (user["student_name"], user["dorm_room"]),
            ).fetchall()
        ]

    return templates.TemplateResponse(
        "student.html",
        {
            "request": request,
            "user": user,
            "rows": rows,
            "notices": notices,
        },
    )


@app.post("/student/pickup/pin")
def student_pickup_pin(
    request: Request,
    parcel_id: int = Form(...),
    pin_code: str = Form(...),
):
    user = current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse("/", status_code=303)

    with db() as conn:
        row = conn.execute("SELECT * FROM parcels WHERE id = ?", (parcel_id,)).fetchone()

        if row and row["pin_code"] == pin_code and row["status"] != "PICKED":
            conn.execute(
                """
                UPDATE parcels
                SET status = 'PICKED', picked_up_at = ?, verified_by = ?
                WHERE id = ?
                """,
                (now_str(), user["student_name"], parcel_id),
            )
            add_audit(conn, parcel_id, "student", user["student_name"], "수령 완료", "PIN 확인 후 처리")

    return RedirectResponse("/student", status_code=303)


@app.get("/student/pickup/qr/{token}")
def student_pickup_qr(request: Request, token: str):
    user = current_user(request)
    if not user or user["role"] != "student":
        return RedirectResponse("/", status_code=303)

    with db() as conn:
        row = conn.execute("SELECT * FROM parcels WHERE pickup_token = ?", (token,)).fetchone()

        if row and row["status"] != "PICKED":
            conn.execute(
                """
                UPDATE parcels
                SET status = 'PICKED', picked_up_at = ?, verified_by = ?
                WHERE id = ?
                """,
                (now_str(), user["student_name"], row["id"]),
            )
            add_audit(conn, row["id"], "student", user["student_name"], "수령 완료", "QR 확인 후 처리")

    return RedirectResponse("/student", status_code=303)


@app.post("/student/read-notice")
def student_read_notice(notification_id: int = Form(...)):
    with db() as conn:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
    return RedirectResponse("/student", status_code=303)


@app.get("/logs", response_class=HTMLResponse)
def logs(request: Request):
    with db() as conn:
        log_rows = [dict(r) for r in conn.execute("SELECT * FROM pickup_audit ORDER BY id DESC").fetchall()]

    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "user": current_user(request), "logs": log_rows, **dashboard()},
    )


@app.get("/api/parcels")
def api():
    return JSONResponse(dashboard())