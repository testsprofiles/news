from pydantic import BaseModel, field_validator

class CommentCreate(BaseModel):
    post_id: int
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Izoh matni bo'sh bo'lishi mumkin emas!")
        if len(v) < 5:
            raise ValueError("Kamida 5 ta belgi bo'lishi kerak!")
        if len(v) > 1000:
            raise ValueError("Maksimal 1000 ta belgi ruxsat etilgan.")
        return v