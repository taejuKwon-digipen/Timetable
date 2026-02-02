from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QSpinBox, QPushButton, QLabel, QTableWidget, QComboBox
)
from PyQt6.QtCore import Qt
from student import Student, UnavailableSlot, AvailableSlot, GRADES

DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토", "평일", "주말"]
AGE_BY_GRADE = {"초1":7,"초2":8,"초3":9,"초4":10,"초5":11,"초6":12,"중1":13,"중2":14,"중3":15,"고1":16,"고2":17,"고3":18}


class StudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unavailable_slots: list[UnavailableSlot] = []
        self.available_slots: list[AvailableSlot] = []
        self._setup_ui()
        self.setWindowTitle("학생 추가")
        self.resize(550, 600)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("예: 홍길동")
        form.addRow("이름:", self.name_edit)

        self.grade_combo = QComboBox()
        self.grade_combo.addItems(GRADES)
        form.addRow("학년:", self.grade_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("예: 010-1234-5678")
        form.addRow("전화번호:", self.phone_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("예: 서울시 강남구 ...")
        form.addRow("주소:", self.address_edit)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(30, 180)
        self.duration_spin.setSingleStep(30)
        self.duration_spin.setValue(60)
        form.addRow("수업 진행 시간(분):", self.duration_spin)

        self.sessions_spin = QSpinBox()
        self.sessions_spin.setRange(1, 14)
        self.sessions_spin.setValue(1)
        self.sessions_spin.setSuffix(" 회/주")
        form.addRow("수업 횟수:", self.sessions_spin)

        layout.addLayout(form)

        layout.addWidget(QLabel("가능한 시간대 (불가만 있으면→불가 제외 전부 가능 / 가능만 있으면→가능 시간만 가능):"))
        self.available_table = QTableWidget(0, 5)
        self.available_table.setHorizontalHeaderLabels(["요일", "시작 시", "시작 분", "끝 시", "끝 분"])
        self.available_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.available_table)

        avail_btn_layout = QHBoxLayout()
        add_avail_btn = QPushButton("가능 시간 추가")
        remove_avail_btn = QPushButton("선택 삭제")
        add_avail_btn.clicked.connect(self._add_available_slot)
        remove_avail_btn.clicked.connect(self._remove_available_slot)
        avail_btn_layout.addWidget(add_avail_btn)
        avail_btn_layout.addWidget(remove_avail_btn)
        avail_btn_layout.addStretch()
        layout.addLayout(avail_btn_layout)

        layout.addWidget(QLabel("불가능한 시간대:"))
        self.unavailable_table = QTableWidget(0, 5)
        self.unavailable_table.setHorizontalHeaderLabels(["요일", "시작 시", "시작 분", "끝 시", "끝 분"])
        self.unavailable_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.unavailable_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("시간대 추가")
        remove_btn = QPushButton("선택 삭제")
        add_btn.clicked.connect(self._add_unavailable_slot)
        remove_btn.clicked.connect(self._remove_unavailable_slot)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog_buttons = QHBoxLayout()
        ok_btn = QPushButton("확인")
        cancel_btn = QPushButton("취소")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(ok_btn)
        dialog_buttons.addWidget(cancel_btn)
        layout.addLayout(dialog_buttons)

    def _sync_available_from_table(self):
        """테이블에 입력된 값을 available_slots에 반영 (추가/삭제 전 호출)"""
        self.available_slots = []
        for i in range(self.available_table.rowCount()):
            day = 0
            combo = self.available_table.cellWidget(i, 0)
            if combo:
                day = min(combo.currentIndex(), 8)  # 0~6 요일, 7=평일, 8=주말
            sh = sm = eh = em = 0
            for col, rng in enumerate([(0, 23), (0, 59), (0, 23), (0, 59)]):
                w = self.available_table.cellWidget(i, col + 1)
                if w:
                    val = w.value()
                    if col == 0: sh = val
                    elif col == 1: sm = val
                    elif col == 2: eh = val
                    else: em = val
            self.available_slots.append(AvailableSlot(day, sh, sm, eh, em))

    def _sync_unavailable_from_table(self):
        """테이블에 입력된 값을 unavailable_slots에 반영"""
        self.unavailable_slots = []
        for i in range(self.unavailable_table.rowCount()):
            day = 0
            combo = self.unavailable_table.cellWidget(i, 0)
            if combo:
                day = min(combo.currentIndex(), 8)
            sh = sm = eh = em = 0
            for col in range(4):
                w = self.unavailable_table.cellWidget(i, col + 1)
                if w:
                    val = w.value()
                    if col == 0: sh = val
                    elif col == 1: sm = val
                    elif col == 2: eh = val
                    else: em = val
            self.unavailable_slots.append(UnavailableSlot(day, sh, sm, eh, em))

    def _add_unavailable_slot(self):
        self._sync_unavailable_from_table()
        self.unavailable_slots.append(UnavailableSlot(1, 9, 0, 12, 0))
        self._load_unavailable_to_table()

    def _add_available_slot(self):
        self._sync_available_from_table()
        self.available_slots.append(AvailableSlot(1, 16, 0, 21, 0))
        self._load_available_to_table()

    def _remove_available_slot(self):
        self._sync_available_from_table()
        row = self.available_table.currentRow()
        if 0 <= row < len(self.available_slots):
            self.available_slots.pop(row)
            self._load_available_to_table()

    def _load_available_to_table(self):
        self.available_table.setRowCount(len(self.available_slots))
        for i, s in enumerate(self.available_slots):
            day_combo = QComboBox()
            day_combo.addItems(DAY_NAMES)
            day_combo.setCurrentIndex(max(0, min(s.day_of_week, 8)))
            self.available_table.setCellWidget(i, 0, day_combo)
            for col, (val, rng) in enumerate([
                (s.start_hour, (0, 23)), (s.start_min, (0, 59)),
                (s.end_hour, (0, 23)), (s.end_min, (0, 59))
            ], 1):
                sp = QSpinBox()
                sp.setRange(*rng)
                sp.setValue(val)
                self.available_table.setCellWidget(i, col, sp)

    def _remove_unavailable_slot(self):
        self._sync_unavailable_from_table()
        row = self.unavailable_table.currentRow()
        if 0 <= row < len(self.unavailable_slots):
            self.unavailable_slots.pop(row)
            self._load_unavailable_to_table()

    def _load_unavailable_to_table(self):
        self.unavailable_table.setRowCount(len(self.unavailable_slots))
        for i, s in enumerate(self.unavailable_slots):
            day_combo = QComboBox()
            day_combo.addItems(DAY_NAMES)
            day_combo.setCurrentIndex(max(0, min(s.day_of_week, 8)))
            self.unavailable_table.setCellWidget(i, 0, day_combo)
            for col, (val, rng) in enumerate([
                (s.start_hour, (0, 23)), (s.start_min, (0, 59)),
                (s.end_hour, (0, 23)), (s.end_min, (0, 59))
            ], 1):
                sp = QSpinBox()
                sp.setRange(*rng)
                sp.setValue(val)
                self.unavailable_table.setCellWidget(i, col, sp)

    def get_student(self) -> Student:
        avail_slots = []
        for i in range(self.available_table.rowCount()):
            day = 0
            combo = self.available_table.cellWidget(i, 0)
            if combo:
                day = min(combo.currentIndex(), 8)
            sh = sm = eh = em = 0
            widgets = [
                self.available_table.cellWidget(i, 1),
                self.available_table.cellWidget(i, 2),
                self.available_table.cellWidget(i, 3),
                self.available_table.cellWidget(i, 4),
            ]
            for col, widget in enumerate(widgets):
                if widget:
                    val = widget.value()
                    if col == 0: sh = val
                    elif col == 1: sm = val
                    elif col == 2: eh = val
                    else: em = val
            avail_slots.append(AvailableSlot(day, sh, sm, eh, em))

        slots = []
        for i in range(self.unavailable_table.rowCount()):
            day = 0
            combo = self.unavailable_table.cellWidget(i, 0)
            if combo:
                day = min(combo.currentIndex(), 8)
            sh = sm = eh = em = 0
            widgets = [
                self.unavailable_table.cellWidget(i, 1),
                self.unavailable_table.cellWidget(i, 2),
                self.unavailable_table.cellWidget(i, 3),
                self.unavailable_table.cellWidget(i, 4),
            ]
            for col, widget in enumerate(widgets):
                if widget:
                    val = widget.value()
                    if col == 0: sh = val
                    elif col == 1: sm = val
                    elif col == 2: eh = val
                    else: em = val
            slots.append(UnavailableSlot(day, sh, sm, eh, em))
        grade_text = self.grade_combo.currentText()
        age = AGE_BY_GRADE.get(grade_text, 13)
        return Student(
            name=self.name_edit.text(),
            grade=grade_text,
            age=age,
            phone=self.phone_edit.text(),
            address=self.address_edit.text(),
            class_duration_minutes=self.duration_spin.value(),
            sessions_per_week=self.sessions_spin.value(),
            unavailable=slots,
            available=avail_slots
        )

    def set_student(self, s: Student):
        self.name_edit.setText(s.name)
        grade = getattr(s, 'grade', None)
        if not grade or grade not in GRADES:
            a = getattr(s, 'age', 13)
            grade = ["초1","초2","초3","초4","초5","초6","중1","중2","중3","고1","고2","고3"][min(max(0, a-7), 11)] if 7<=a<=18 else "초1"
        idx = GRADES.index(grade) if grade in GRADES else 0
        self.grade_combo.setCurrentIndex(idx)
        self.phone_edit.setText(s.phone)
        self.address_edit.setText(s.address)
        self.duration_spin.setValue(s.class_duration_minutes)
        self.sessions_spin.setValue(getattr(s, 'sessions_per_week', 1))
        self.unavailable_slots = list(s.unavailable)
        self.available_slots = list(getattr(s, 'available', []))
        self._load_available_to_table()
        self._load_unavailable_to_table()
