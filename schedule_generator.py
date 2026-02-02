from dataclasses import dataclass
from typing import List
from student import Student


@dataclass
class ScheduleBlock:
    student_index: int
    day_of_week: int
    start_minutes: int
    duration_minutes: int


class ScheduleGenerator:
    def __init__(self, students: List[Student]):
        self.students = students
        self.start_hour = 9
        self.end_hour = 21
        self.min_slot_minutes = 30

    def set_time_range(self, start_hour: int, end_hour: int):
        self.start_hour = start_hour
        self.end_hour = end_hour

    def generate(self) -> List[ScheduleBlock]:
        """학생별 블록을 미배정(day=-1)으로 생성 → 오른쪽 풀에서 끌어다 배치"""
        blocks = []
        for si, s in enumerate(self.students):
            duration = max(s.class_duration_minutes, self.min_slot_minutes)
            sessions = getattr(s, 'sessions_per_week', 1)
            for _ in range(sessions):
                blocks.append(ScheduleBlock(si, -1, -1, duration))  # 미배정
        return blocks
