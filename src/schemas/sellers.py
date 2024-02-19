from pydantic import BaseModel, Field, EmailStr

__all__ = ["IncomingSeller", "ReturnedSeller", "ReturnedAllSellers"]


class BaseSeller(BaseModel):
    first_name: str = Field(min_length=3)
    last_name: str = Field(min_length=3)
    e_mail: EmailStr() = Field(alias="e-mail")

    class Config:
        populate_by_name = True


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
class IncomingSeller(BaseSeller):
    password: str = Field(min_length=6)


class ReturnedSeller(BaseSeller):
    id: int


class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]
