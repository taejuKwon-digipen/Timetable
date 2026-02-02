from dataclasses import dataclass, field
from typing import List


@dataclass
class UnavailableSlot:
    """불가능한 시간대: 요일(0=일~6=토), 시작/끝 시·분"""
    day_of_week: int
    start_hour: int
    start_min: int
    end_hour: int
    end_min: int


@dataclass
class AvailableSlot:
    """가능한 시간대: 요일(0=일~6=토), 시작/끝 시·분 (비어있으면 모든 시간 가능)"""
    day_of_week: int
    start_hour: int
    start_min: int
    end_hour: int
    end_min: int


GRADES = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]


@dataclass
class Student:
    id: int | None = None  # DB 저장용 (None이면 신규)
    name: str = ""
    grade: str = "중1"  # 중1, 중2, 중3, 고1, 고2, 고3
    age: int = 0  # 하위 호환용 (DB), grade 우선
    phone: str = ""
    address: str = ""
    class_duration_minutes: int = 60
    sessions_per_week: int = 1  # 주당 수업 횟수
    unavailable: List[UnavailableSlot] = field(default_factory=list)
    available: List[AvailableSlot] = field(default_factory=list)

    def _age_to_grade(self) -> str:
        """age로 grade 추정 (기존 DB 호환)"""
        a = self.age
        if 7 <= a <= 12:
            return ["초1", "초2", "초3", "초4", "초5", "초6"][a - 7]
        if 13 <= a <= 15:
            return ["중1", "중2", "중3"][a - 13]
        if 16 <= a <= 18:
            return ["고1", "고2", "고3"][a - 16]
        return "초1"

    def _in_slot(self, check_minutes: int, slot) -> bool:
        slot_start = slot.start_hour * 60 + slot.start_min
        slot_end = slot.end_hour * 60 + slot.end_min
        return slot_start <= check_minutes < slot_end

    def _slot_matches_day(self, slot_day: int, check_day: int) -> bool:
        """슬롯의 요일이 check_day와 일치하는지 (7=평일, 8=주말)"""
        if 0 <= slot_day <= 6:
            return slot_day == check_day
        if slot_day == 7:  # 평일 (월~금)
            return 1 <= check_day <= 5
        if slot_day == 8:  # 주말 (일, 토)
            return check_day in (0, 6)
        return False

    def is_available(self, day_of_week: int, hour: int, min: int) -> bool:
        """가능/불가능 시간대를 모두 고려해 해당 시각에 수업 가능 여부 반환
        
        - 불가만 있고 가능 비움: 불가 제외한 모든 시간 가능
        - 가능만 있고 불가 비움: 가능 시간만 가능 (나머지 전부 불가)
        - 둘 다 있음: 가능 AND 불가 아님
        - 둘 다 비움: 모든 시간 가능 (학교 시간 고려 안 함)
        """
        check_minutes = hour * 60 + min
        has_avail = bool(self.available)
        has_unavail = bool(self.unavailable)

        if has_avail and not has_unavail:
            # 가능 시간만 있음 → 가능 시간 안에 있어야 함
            for slot in self.available:
                if self._slot_matches_day(slot.day_of_week, day_of_week) and self._in_slot(check_minutes, slot):
                    return True
            return False

        if not has_avail and has_unavail:
            # 불가만 있음 → 불가 제외한 모든 시간 가능
            for slot in self.unavailable:
                if self._slot_matches_day(slot.day_of_week, day_of_week) and self._in_slot(check_minutes, slot):
                    return False
            return True

        if has_avail and has_unavail:
            # 둘 다 있음 → 가능 AND 불가 아님
            for slot in self.unavailable:
                if self._slot_matches_day(slot.day_of_week, day_of_week) and self._in_slot(check_minutes, slot):
                    return False
            for slot in self.available:
                if self._slot_matches_day(slot.day_of_week, day_of_week) and self._in_slot(check_minutes, slot):
                    return True
            return False

        # 둘 다 비움 → 모든 시간 가능 (학교 시간 고려 안 함)
        return True

    def can_place_block(self, day_of_week: int, start_minutes: int, duration_minutes: int) -> bool:
        """해당 요일·시작·길이로 수업 배치 가능한지 (30분 단위로 검사)"""
        for offset in range(0, duration_minutes, 30):
            m = start_minutes + offset
            h, mn = divmod(m, 60)
            if not self.is_available(day_of_week, h, mn):
                return False
        # 끝 시각도 검사
        end_m = start_minutes + duration_minutes
        eh, em = divmod(end_m, 60)
        return self.is_available(day_of_week, eh, em)
