from dataclasses import dataclass
from helpers.time_utils import to_days, to_utc_date


@dataclass
class Schedule:
    sett: str
    token: str
    initialTokensLocked: int
    startTime: int
    endTime: int
    duration: int

    def __repr__(self):
        return (
            f"Schedule(sett={self.sett},"
            f"token={self.token},"
            f"initalTokensLocked={self.initialTokensLocked},"
            f"startTime={to_utc_date(self.startTime)},"
            f"duration={to_days(self.duration)} days,"
            f"endTime={to_utc_date(self.endTime)}"
        )
