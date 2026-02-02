from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QStackedWidget, QMessageBox, QDialog
)
from student import Student, GRADES
from student_dialog import StudentDialog
from schedule_generator import ScheduleGenerator, ScheduleBlock
from timetable_widget import TimetableWidget, GRADE_COLORS
import db


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.students: list[Student] = []
        self.blocks: list[ScheduleBlock] = []
        self.student_list = QListWidget()
        self.stack = QStackedWidget()
        self.timetable_widget = TimetableWidget()
        self._setup_ui()
        self._load_students_from_db()
        self.setWindowTitle("시간표 관리 프로그램")
        self.resize(1000, 700)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 학생 목록 페이지
        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("학생 목록"))
        add_btn = QPushButton("+ 학생 추가")
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self._add_student)
        top_bar.addWidget(add_btn)
        edit_btn = QPushButton("수정")
        edit_btn.setFixedWidth(80)
        edit_btn.clicked.connect(self._edit_student)
        top_bar.addWidget(edit_btn)
        remove_btn = QPushButton("삭제")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(self._remove_student)
        top_bar.addWidget(remove_btn)
        top_bar.addStretch()
        list_layout.addLayout(top_bar)

        self.student_list.setMinimumHeight(150)
        self.student_list.itemDoubleClicked.connect(self._edit_student)
        list_layout.addWidget(self.student_list)

        schedule_bar = QHBoxLayout()
        gen_btn = QPushButton("시간표 짜기")
        gen_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px 20px; }")
        gen_btn.clicked.connect(self._generate_schedule)
        schedule_bar.addWidget(gen_btn)
        schedule_bar.addStretch()
        list_layout.addLayout(schedule_bar)

        list_layout.addWidget(QLabel(
            "※ '시간표 짜기'를 누르면 오른쪽에 학생별 블록이 생깁니다. 블록을 끌어다 시간표에 놓으면 됩니다.\n"
            "  블록을 누르거나 드래그하면 해당 학생의 가능한 시간이 하이라이트됩니다."
        ))
        list_layout.addStretch()

        self.stack.addWidget(list_page)

        # 시간표 페이지
        timetable_page = QWidget()
        timetable_layout = QVBoxLayout(timetable_page)
        back_btn = QPushButton("← 학생 목록으로")
        back_btn.clicked.connect(self._show_student_list)
        timetable_layout.addWidget(back_btn)
        # 학년별 색상 범례
        legend_layout = QHBoxLayout()
        for g in GRADES:
            lbl = QLabel(f" {g} ")
            rgb = GRADE_COLORS.get(g, (200, 200, 200))
            lbl.setStyleSheet(f"background-color: rgb({rgb[0]},{rgb[1]},{rgb[2]}); padding: 2px 8px; border-radius: 3px;")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        timetable_layout.addLayout(legend_layout)
        self.timetable_widget.setMinimumSize(800, 500)
        timetable_layout.addWidget(self.timetable_widget)
        self.stack.addWidget(timetable_page)

        main_layout.addWidget(self.stack)

    def _load_students_from_db(self):
        self.students = db.load_all_students()
        self._update_student_list()

    def _add_student(self):
        dlg = StudentDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            s = dlg.get_student()
            if not s.name.strip():
                QMessageBox.warning(self, "오류", "이름을 입력해주세요.")
                return
            new_id = db.insert_student(s)
            s.id = new_id
            self.students.append(s)
            self._update_student_list()

    def _edit_student(self):
        row = self.student_list.currentRow()
        if row < 0 or row >= len(self.students):
            QMessageBox.warning(self, "알림", "수정할 학생을 선택해주세요.")
            return
        s = self.students[row]
        dlg = StudentDialog(self)
        dlg.setWindowTitle("학생 수정")
        dlg.set_student(s)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_student()
            if not updated.name.strip():
                QMessageBox.warning(self, "오류", "이름을 입력해주세요.")
                return
            updated.id = s.id
            db.update_student(updated)
            self.students[row] = updated
            self._update_student_list()

    def _remove_student(self):
        row = self.student_list.currentRow()
        if 0 <= row < len(self.students):
            s = self.students[row]
            if s.id is not None:
                db.delete_student(s.id)
            self.students.pop(row)
            self._update_student_list()

    def _update_student_list(self):
        self.student_list.clear()
        for s in self.students:
            sessions = getattr(s, 'sessions_per_week', 1)
            grade = getattr(s, 'grade', '중1') or '중1'
            self.student_list.addItem(f"{s.name} ({grade}) - {s.class_duration_minutes}분 수업, 주 {sessions}회")

    def _generate_schedule(self):
        if not self.students:
            QMessageBox.warning(self, "오류", "학생을 먼저 추가해주세요.")
            return
        gen = ScheduleGenerator(self.students)
        gen.set_time_range(9, 21)
        self.blocks = gen.generate()
        self.timetable_widget.set_students(self.students)
        self.timetable_widget.set_blocks(self.blocks)
        self._show_timetable()

    def _show_timetable(self):
        self.stack.setCurrentIndex(1)

    def _show_student_list(self):
        self.stack.setCurrentIndex(0)

    def closeEvent(self, e):
        self.timetable_widget.cleanup()
        super().closeEvent(e)
