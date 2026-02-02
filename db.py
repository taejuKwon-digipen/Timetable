"""SQLite DB로 학생 목록 저장/불러오기"""
import sys
import sqlite3
from pathlib import Path
from student import Student, UnavailableSlot, AvailableSlot


def _db_path() -> Path:
    """실행 환경에 따라 DB 경로 결정 (빌드된 exe는 exe와 같은 폴더)"""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent
    return base / "timetable.db"


def get_connection():
    path = _db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """테이블 생성 (없을 때만)"""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL DEFAULT 0,
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                class_duration_minutes INTEGER NOT NULL DEFAULT 60,
                sessions_per_week INTEGER NOT NULL DEFAULT 1
            )
        """)
        try:
            conn.execute("ALTER TABLE students ADD COLUMN grade TEXT DEFAULT '중1'")
        except sqlite3.OperationalError:
            pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS unavailable_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_hour INTEGER NOT NULL,
                start_min INTEGER NOT NULL,
                end_hour INTEGER NOT NULL,
                end_min INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS available_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_hour INTEGER NOT NULL,
                start_min INTEGER NOT NULL,
                end_hour INTEGER NOT NULL,
                end_min INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    finally:
        conn.close()


def load_all_students() -> list[Student]:
    """DB에서 전체 학생 목록 + 불가 시간대 로드"""
    init_db()
    conn = get_connection()
    result = []
    try:
        cur = conn.execute(
            "SELECT id, name, age, grade, phone, address, class_duration_minutes, sessions_per_week FROM students ORDER BY id"
        )
        for row in cur:
            sid = row["id"]
            unavail_cur = conn.execute(
                "SELECT day_of_week, start_hour, start_min, end_hour, end_min FROM unavailable_slots WHERE student_id = ?",
                (sid,),
            )
            unavail_slots = [
                UnavailableSlot(
                    day_of_week=r["day_of_week"],
                    start_hour=r["start_hour"],
                    start_min=r["start_min"],
                    end_hour=r["end_hour"],
                    end_min=r["end_min"],
                )
                for r in unavail_cur
            ]
            avail_cur = conn.execute(
                "SELECT day_of_week, start_hour, start_min, end_hour, end_min FROM available_slots WHERE student_id = ?",
                (sid,),
            )
            avail_slots = [
                AvailableSlot(
                    day_of_week=r["day_of_week"],
                    start_hour=r["start_hour"],
                    start_min=r["start_min"],
                    end_hour=r["end_hour"],
                    end_min=r["end_min"],
                )
                for r in avail_cur
            ]
            grade_val = row["grade"] if "grade" in row.keys() and row["grade"] else None
            if not grade_val:
                a = row["age"] or 0
                if 7 <= a <= 12:
                    grade_val = ["초1","초2","초3","초4","초5","초6"][a - 7]
                elif 13 <= a <= 15:
                    grade_val = ["중1","중2","중3"][a - 13]
                elif 16 <= a <= 18:
                    grade_val = ["고1","고2","고3"][a - 16]
                else:
                    grade_val = "초1"
            result.append(
                Student(
                    id=sid,
                    name=row["name"] or "",
                    grade=grade_val,
                    age=row["age"] or 0,
                    phone=row["phone"] or "",
                    address=row["address"] or "",
                    class_duration_minutes=row["class_duration_minutes"] or 60,
                    sessions_per_week=row["sessions_per_week"] or 1,
                    unavailable=unavail_slots,
                    available=avail_slots,
                )
            )
    finally:
        conn.close()
    return result


def insert_student(s: Student) -> int:
    """학생 추가 후 새 id 반환"""
    conn = get_connection()
    try:
        grade = getattr(s, 'grade', '중1') or '중1'
        cur = conn.execute(
            """INSERT INTO students (name, age, grade, phone, address, class_duration_minutes, sessions_per_week)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (s.name, s.age, grade, s.phone or "", s.address or "", s.class_duration_minutes, s.sessions_per_week),
        )
        sid = cur.lastrowid
        for slot in s.unavailable:
            conn.execute(
                """INSERT INTO unavailable_slots (student_id, day_of_week, start_hour, start_min, end_hour, end_min)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, slot.day_of_week, slot.start_hour, slot.start_min, slot.end_hour, slot.end_min),
            )
        for slot in s.available:
            conn.execute(
                """INSERT INTO available_slots (student_id, day_of_week, start_hour, start_min, end_hour, end_min)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, slot.day_of_week, slot.start_hour, slot.start_min, slot.end_hour, slot.end_min),
            )
        conn.commit()
        return sid
    finally:
        conn.close()


def update_student(s: Student) -> None:
    """학생 수정 (id 필수). 불가 시간대는 기존 삭제 후 전부 다시 삽입."""
    if s.id is None:
        raise ValueError("update_student requires Student.id")
    conn = get_connection()
    try:
        grade = getattr(s, 'grade', '중1') or '중1'
        conn.execute(
            """UPDATE students SET name=?, age=?, grade=?, phone=?, address=?, class_duration_minutes=?, sessions_per_week=?
               WHERE id=?""",
            (s.name, s.age, grade, s.phone or "", s.address or "", s.class_duration_minutes, s.sessions_per_week, s.id),
        )
        conn.execute("DELETE FROM unavailable_slots WHERE student_id = ?", (s.id,))
        conn.execute("DELETE FROM available_slots WHERE student_id = ?", (s.id,))
        for slot in s.unavailable:
            conn.execute(
                """INSERT INTO unavailable_slots (student_id, day_of_week, start_hour, start_min, end_hour, end_min)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (s.id, slot.day_of_week, slot.start_hour, slot.start_min, slot.end_hour, slot.end_min),
            )
        for slot in s.available:
            conn.execute(
                """INSERT INTO available_slots (student_id, day_of_week, start_hour, start_min, end_hour, end_min)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (s.id, slot.day_of_week, slot.start_hour, slot.start_min, slot.end_hour, slot.end_min),
            )
        conn.commit()
    finally:
        conn.close()


def delete_student(student_id: int) -> None:
    """학생 삭제 (관련 불가 시간대는 CASCADE로 함께 삭제)"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.execute("DELETE FROM unavailable_slots WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM available_slots WHERE student_id = ?", (student_id,))
        conn.commit()
    finally:
        conn.close()
