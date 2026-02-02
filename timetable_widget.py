from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QMimeData, QPoint, QEvent
from PyQt6.QtGui import QColor, QDrag
from typing import List
from student import Student
from schedule_generator import ScheduleBlock

# 월~토, 일 (일요일을 토요일 옆에)
DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
# 열 인덱스(1~7) -> day_of_week (0=일, 1=월, ..., 6=토)
COL_TO_DAY = (1, 2, 3, 4, 5, 6, 0)
HOURS_START = 8
HOURS_END = 22
SLOT_HEIGHT = 40

# day_of_week < 0 이면 미배정
UNASSIGNED_DAY = -1

# 학년별 블록 색상 (초1~고3) - QColor 캐시로 반복 생성 방지
GRADE_COLORS = {
    "초1": (255, 228, 196),   # 블랜치드 알몬드
    "초2": (173, 216, 230),   # 하늘색
    "초3": (144, 238, 144),   # 연두색
    "초4": (255, 218, 185),   # 복숭아색
    "초5": (221, 160, 221),   # 자주색
    "초6": (255, 182, 193),   # 연분홍
    "중1": (176, 224, 230),   # 파우더블루
    "중2": (152, 251, 152),   # 민트색
    "중3": (255, 228, 225),   # 미스트 로즈
    "고1": (230, 230, 250),   # 라벤더
    "고2": (245, 245, 220),   # 베이지
    "고3": (240, 248, 255),   # 앨리스블루
}
_GRADE_QCOLORS = {g: QColor(*rgb) for g, rgb in GRADE_COLORS.items()}


class BlockPoolListWidget(QListWidget):
    """미배정 블록 목록 - 커스텀 드래그/드롭 지원"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_pool = None

    def set_parent_pool(self, p):
        self.parent_pool = p

    def dragEnterEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if self.parent_pool and e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            data = e.mimeData().text()[6:]
            parts = data.split(",")
            if len(parts) >= 5:
                block_idx = int(parts[0])
                tt = self.parent_pool.parent_timetable
                if tt and 0 <= block_idx < len(tt.blocks):
                    tt.blocks[block_idx].day_of_week = UNASSIGNED_DAY
                    tt.blocks[block_idx].start_minutes = -1
                    tt._rebuild_all()
            e.acceptProposedAction()
        else:
            super().dropEvent(e)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item:
            return
        block_idx = item.data(Qt.ItemDataRole.UserRole)
        if block_idx is None or not isinstance(block_idx, int):
            return
        tt = self.parent_pool.parent_timetable if self.parent_pool else None
        if not tt or block_idx < 0 or block_idx >= len(tt.blocks):
            return
        blk = tt.blocks[block_idx]
        tt._start_drag_highlight(blk.student_index, blk.duration_minutes, block_idx)
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"BLOCK:{block_idx},{blk.student_index},{blk.day_of_week},{blk.start_minutes},{blk.duration_minutes}")
        drag.setMimeData(mime)
        drag.exec(supported_actions)
        tt._clear_drag_highlight()


class BlockPoolWidget(QFrame):
    """오른쪽 미배정 블록 영역 - 드롭 받기 + 드래그 출발"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_timetable = None
        self.setAcceptDrops(True)
        self.setMinimumWidth(180)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("미배정 블록"))
        self.list_widget = BlockPoolListWidget(self)
        self.list_widget.set_parent_pool(self)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        layout.addWidget(self.list_widget)

    def set_parent(self, p):
        self.parent_timetable = p

    def refresh(self):
        if not self.parent_timetable:
            return
        self.list_widget.clear()
        for bi, b in enumerate(self.parent_timetable.blocks):
            if b.day_of_week < 0:
                if b.student_index >= 0 and b.student_index < len(self.parent_timetable.students):
                    s = self.parent_timetable.students[b.student_index]
                    item = QListWidgetItem(f"{s.name} ({b.duration_minutes}분)")
                else:
                    item = QListWidgetItem(f"블록 #{bi} ({b.duration_minutes}분)")
                item.setData(Qt.ItemDataRole.UserRole, bi)
                self.list_widget.addItem(item)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()

    def dropEvent(self, e):
        if not e.mimeData().hasText() or not e.mimeData().text().startswith("BLOCK:"):
            return
        data = e.mimeData().text()[6:]
        parts = data.split(",")
        if len(parts) < 5:
            return
        block_idx = int(parts[0])
        if self.parent_timetable and 0 <= block_idx < len(self.parent_timetable.blocks):
            self.parent_timetable.blocks[block_idx].day_of_week = UNASSIGNED_DAY
            self.parent_timetable.blocks[block_idx].start_minutes = -1
            self.parent_timetable._rebuild_all()
        e.acceptProposedAction()


class TimetableGrid(QTableWidget):
    """시간표 그리드 - 블록 표시, 드래그/드롭, 가능 시간 하이라이트"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_timetable = None
        self._drag_start_pos = None

    def set_parent(self, p):
        self.parent_timetable = p

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = e.position().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if (e.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_pos is not None:
            if (e.position().toPoint() - self._drag_start_pos).manhattanLength() > 10:
                item = self.itemAt(self._drag_start_pos)
                if item and item.column() > 0:
                    block_idx = item.data(Qt.ItemDataRole.UserRole)
                    if block_idx is not None and isinstance(block_idx, int) and block_idx >= 0:
                        tt = self.parent_timetable
                        if tt and block_idx < len(tt.blocks):
                            blk = tt.blocks[block_idx]
                            if blk.day_of_week >= 0:
                                self._drag_start_pos = None
                                tt._start_drag_highlight(blk.student_index, blk.duration_minutes, block_idx)
                                drag = QDrag(self)
                                mime = QMimeData()
                                mime.setText(f"BLOCK:{block_idx},{blk.student_index},{blk.day_of_week},{blk.start_minutes},{blk.duration_minutes}")
                                drag.setMimeData(mime)
                                drag.exec(Qt.DropAction.MoveAction)
                                tt._clear_drag_highlight()
                                return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_start_pos = None
        super().mouseReleaseEvent(e)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()
            if self.parent_timetable:
                data = e.mimeData().text()[6:]
                parts = data.split(",")
                if len(parts) >= 5:
                    try:
                        bi, si, dur = int(parts[0]), int(parts[1]), int(parts[4])
                        self.parent_timetable._start_drag_highlight(si, dur, bi)
                    except (ValueError, IndexError):
                        pass
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dragLeaveEvent(self, e):
        if self.parent_timetable:
            self.parent_timetable._clear_drag_highlight()
        super().dragLeaveEvent(e)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item or item.column() == 0:
            return
        block_idx = item.data(Qt.ItemDataRole.UserRole)
        if block_idx is None or not isinstance(block_idx, int) or block_idx < 0:
            return
        tt = self.parent_timetable
        if not tt or block_idx >= len(tt.blocks):
            return
        blk = tt.blocks[block_idx]
        if blk.day_of_week < 0:
            return
        tt._start_drag_highlight(blk.student_index, blk.duration_minutes, block_idx)
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"BLOCK:{block_idx},{blk.student_index},{blk.day_of_week},{blk.start_minutes},{blk.duration_minutes}")
        drag.setMimeData(mime)
        drag.exec(supported_actions)
        tt._clear_drag_highlight()

    def dropEvent(self, e):
        if not e.mimeData().hasText() or not e.mimeData().text().startswith("BLOCK:"):
            super().dropEvent(e)
            return
        item = self.itemAt(e.position().toPoint())
        if not item or item.column() == 0:
            super().dropEvent(e)
            return
        data = e.mimeData().text()[6:]
        parts = data.split(",")
        if len(parts) < 5:
            super().dropEvent(e)
            return
        block_idx = int(parts[0])
        col = item.column()
        new_day = COL_TO_DAY[col - 1] if 1 <= col <= 7 else 0
        row = item.row()
        new_start_min = (HOURS_START + row // 2) * 60 + (row % 2) * 30
        tt = self.parent_timetable
        if tt and 0 <= block_idx < len(tt.blocks):
            blk = tt.blocks[block_idx]
            # 가능한 시간대인지 + 다른 블록과 겹치지 않는지 검증
            si = blk.student_index
            dur = blk.duration_minutes
            if 0 <= si < len(tt.students) and tt.students[si].can_place_block(new_day, new_start_min, dur):
                block_end = new_start_min + dur
                overlaps = False
                for bi, b in enumerate(tt.blocks):
                    if b.day_of_week < 0 or bi == block_idx:
                        continue
                    if b.day_of_week != new_day:
                        continue
                    b_end = b.start_minutes + b.duration_minutes
                    if new_start_min < b_end and block_end > b.start_minutes:
                        overlaps = True
                        break
                if not overlaps:
                    blk.day_of_week = new_day
                    blk.start_minutes = new_start_min
            tt._rebuild_all()
        if tt:
            tt._clear_drag_highlight()
        e.acceptProposedAction()


class TimetableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.students: List[Student] = []
        self.blocks: List[ScheduleBlock] = []
        self._highlight_student_idx: int | None = None
        self._highlight_duration: int = 60
        self._highlight_block_idx: int | None = None  # 이동 중인 블록(겹침 제외용)

        layout = QHBoxLayout(self)
        self.grid = TimetableGrid(self)
        self.grid.set_parent(self)
        self.grid.setAcceptDrops(True)
        self.grid.setDragEnabled(True)
        self.grid.setDragDropMode(QTableWidget.DragDropMode.DragDrop)
        self.grid.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.grid.setDragDropOverwriteMode(False)
        self.grid.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.grid.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.grid.verticalHeader().setDefaultSectionSize(SLOT_HEIGHT)
        layout.addWidget(self.grid, stretch=1)

        self.pool = BlockPoolWidget(self)
        self.pool.set_parent(self)
        layout.addWidget(self.pool)

        self._connect_grid_events()

    def _connect_grid_events(self):
        self.grid.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.grid.viewport():
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                self._on_grid_press(event)
        return super().eventFilter(obj, event)

    def _on_grid_press(self, event):
        """블록 위에서 마우스 누르면 가능 시간 하이라이트"""
        pos = event.position().toPoint()
        item = self.grid.itemAt(pos)
        if event.type() == QEvent.Type.MouseButtonPress:
            if item and item.column() > 0:
                bi = item.data(Qt.ItemDataRole.UserRole)
                if bi is not None and isinstance(bi, int) and 0 <= bi < len(self.blocks):
                    blk = self.blocks[bi]
                    if blk.day_of_week >= 0:
                        self._start_drag_highlight(blk.student_index, blk.duration_minutes, bi)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            # 클릭만 하고 드래그 안 했을 때 하이라이트 해제 (드래그 시에는 drop/dragLeave에서 해제)
            if self._highlight_student_idx is not None:
                self._clear_drag_highlight()

    def _start_drag_highlight(self, student_idx: int, duration: int, block_idx: int | None = None):
        self._highlight_student_idx = student_idx
        self._highlight_duration = duration
        self._highlight_block_idx = block_idx
        self._apply_availability_highlight()

    def _clear_drag_highlight(self):
        self._highlight_student_idx = None
        self._highlight_block_idx = None
        self._rebuild_table_cells()

    def _apply_availability_highlight(self):
        """현재 하이라이트 대상 학생의 가능한 시간대를 표시"""
        self._rebuild_table_cells(highlight_only=True)

    def set_students(self, students: List[Student]):
        self.students = students

    def set_blocks(self, blocks: List[ScheduleBlock]):
        self.blocks = blocks
        self._rebuild_all()

    def get_blocks(self) -> List[ScheduleBlock]:
        return list(self.blocks)

    def _rebuild_all(self):
        self._rebuild_table_cells()
        self.pool.refresh()

    def _block_text(self, student_idx: int, duration: int) -> str:
        if student_idx < 0 or student_idx >= len(self.students):
            return "?"
        s = self.students[student_idx]
        return f"{s.name}\n{s.address}"

    def _rebuild_table_cells(self, highlight_only: bool = False):
        cols = 8
        rows = (HOURS_END - HOURS_START) * 2
        if not highlight_only:
            self.grid.setColumnCount(cols)
            self.grid.setRowCount(rows)
            headers = ["시간"] + DAY_NAMES
            self.grid.setHorizontalHeaderLabels(headers)

            for r in range(rows):
                hour = HOURS_START + r // 2
                min = (r % 2) * 30
                time_item = QTableWidgetItem(f"{hour:02d}:{min:02d}")
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
                self.grid.setItem(r, 0, time_item)

        for c in range(1, cols):
            for r in range(rows):
                if highlight_only:
                    item = self.grid.item(r, c)
                    if not item:
                        continue
                else:
                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled)
                    self.grid.setItem(r, c, item)

                day = COL_TO_DAY[c - 1] if 1 <= c <= 7 else 0
                slot_start_min = (HOURS_START + r // 2) * 60 + (r % 2) * 30

                # 하이라이트 모드: 가능 시간 + 미사용 슬롯만 표시
                if self._highlight_student_idx is not None:
                    si = self._highlight_student_idx
                    dur = self._highlight_duration
                    block_end_min = slot_start_min + dur
                    # 다른 블록과 겹치는지 확인 (이 블록 전체 구간 기준)
                    overlaps = False
                    for bi, b in enumerate(self.blocks):
                        if b.day_of_week < 0:
                            continue
                        if self._highlight_block_idx is not None and bi == self._highlight_block_idx:
                            continue
                        if b.day_of_week != day:
                            continue
                        b_end = b.start_minutes + b.duration_minutes
                        if slot_start_min < b_end and block_end_min > b.start_minutes:
                            overlaps = True
                            break
                    if overlaps:
                        item.setBackground(QColor(255, 230, 230))
                        item.setData(Qt.ItemDataRole.UserRole + 1, "unavailable")
                    elif 0 <= si < len(self.students):
                        s = self.students[si]
                        if s.can_place_block(day, slot_start_min, dur):
                            item.setBackground(QColor(200, 255, 200))  # 연두색 = 가능
                            item.setData(Qt.ItemDataRole.UserRole + 1, "available")
                        else:
                            item.setBackground(QColor(255, 230, 230))  # 연한 빨강 = 불가
                            item.setData(Qt.ItemDataRole.UserRole + 1, "unavailable")
                    continue

                # 기본: 블록 그리기
                item.setData(Qt.ItemDataRole.UserRole + 1, None)
                block_found = False
                for bi, b in enumerate(self.blocks):
                    if b.day_of_week < 0:
                        continue
                    if b.day_of_week != day:
                        continue
                    start_slot = (b.start_minutes // 60 - HOURS_START) * 2 + (b.start_minutes % 60) // 30
                    span = (b.duration_minutes + 29) // 30
                    if start_slot <= r < start_slot + span:
                        item.setData(Qt.ItemDataRole.UserRole, bi)
                        grade = getattr(self.students[b.student_index], 'grade', '중1') if b.student_index < len(self.students) else '중1'
                        item.setBackground(_GRADE_QCOLORS.get(grade, QColor(173, 216, 230)))
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
                        if r == start_slot:
                            item.setText(self._block_text(b.student_index, b.duration_minutes))
                        block_found = True
                        break
                if not block_found:
                    item.setData(Qt.ItemDataRole.UserRole, None)
                    item.setBackground(QColor(255, 255, 255))
                    item.setText("")

        for c in range(cols):
            self.grid.setColumnWidth(c, 100)

    def dragEnterEvent(self, e):
        if e.source() != self.grid and e.mimeData().hasText() and e.mimeData().text().startswith("BLOCK:"):
            data = e.mimeData().text()[6:]
            parts = data.split(",")
            if len(parts) >= 5:
                try:
                    bi, si, dur = int(parts[0]), int(parts[1]), int(parts[4])
                    self._start_drag_highlight(si, dur, bi)
                except (ValueError, IndexError):
                    pass
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self._clear_drag_highlight()

    def cleanup(self):
        """이벤트 필터·순환 참조 해제 (메모리 릭 방지)"""
        try:
            if self.grid and self.grid.viewport():
                self.grid.viewport().removeEventFilter(self)
        except Exception:
            pass
        try:
            if self.grid:
                self.grid.set_parent(None)
            if self.pool:
                self.pool.set_parent(None)
                if getattr(self.pool, 'list_widget', None):
                    self.pool.list_widget.set_parent_pool(None)
        except Exception:
            pass
