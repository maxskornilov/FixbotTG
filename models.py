from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    tariff: str
    registration_date: datetime = None
    
    @classmethod
    def from_db_row(cls, row):
        if not row:
            return None
        return cls(
            user_id=row[0],
            username=row[1],
            first_name=row[2],
            last_name=row[3],
            tariff=row[4],
            registration_date=row[5] if len(row) > 5 else None
        )


@dataclass
class Feedback:
    id: int
    user_id: int
    message: str
    sent_date: datetime = None
    
    @classmethod
    def from_db_row(cls, row):
        if not row:
            return None
        return cls(
            id=row[0],
            user_id=row[1],
            message=row[2],
            sent_date=row[3] if len(row) > 3 else None
        )


@dataclass
class ModuleProgress:
    user_id: int
    module_id: int
    completed: bool
    completion_date: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row):
        if not row:
            return None
        return cls(
            user_id=row[0],
            module_id=row[1],
            completed=bool(row[2]),
            completion_date=row[3] if len(row) > 3 else None
        )


@dataclass
class HomeworkSubmission:
    id: int
    user_id: int
    module_id: int
    submission: str
    submitted_date: datetime = None
    feedback: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row):
        if not row:
            return None
        return cls(
            id=row[0],
            user_id=row[1],
            module_id=row[2],
            submission=row[3],
            submitted_date=row[4] if len(row) > 4 else None,
            feedback=row[5] if len(row) > 5 else None
        )
