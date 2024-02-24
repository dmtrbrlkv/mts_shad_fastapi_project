from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi import Response
from icecream import ic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import IncomingSeller, ReturnedSeller, ReturnedAllSellers
from src.schemas.sellers import BaseSeller, ReturnedSellerWithBooks

sellers_router = APIRouter(tags=["sellers"], prefix="/seller")

# Больше не симулируем хранилище данных. Подключаемся к реальному, через сессию.
DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о книге в БД. Возвращает созданную книгу.
@sellers_router.post("/", response_model=ReturnedSeller,
                     status_code=status.HTTP_201_CREATED)  # Прописываем модель ответа
async def create_seller(
        seller: IncomingSeller, session: DBSession
):
    new_seller = Seller(
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email,
        password=seller.password,
    )
    session.add(new_seller)
    await session.flush()

    return new_seller


@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    res = await session.execute(query)
    sellers = res.scalars().all()
    return {"sellers": sellers}


# Ручка для получения книги по ее ИД
@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_seller(seller_id: int, session: DBSession):
    # В таком виде чрез постман работает, через pytest ошибка -
    # Error extracting attribute: MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
    # Was IO attempted in an unexpected place? (Background on this error at: https://sqlalche.me/e/20/xd2s)
    # if seller := await session.get(Seller, seller_id, options=[selectinload(Seller.books)]):
    #     return seller
    # return Response(status_code=status.HTTP_404_NOT_FOUND)

    res = await session.execute(
        select(Seller).where(Seller.id == seller_id).options(selectinload(Seller.books))
    )
    if seller := res.scalars().first():
        return seller
    return Response(status_code=status.HTTP_404_NOT_FOUND)

@sellers_router.delete("/{seller_id}")
async def delete_seller(seller_id: int, session: DBSession):
    if deleted_seller := await session.get(Seller, seller_id):
        await session.delete(deleted_seller)
        await session.flush()
        return Response(status_code=status.HTTP_204_NO_CONTENT)  # Response может вернуть текст и метаданные.
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, new_data: BaseSeller, session: DBSession):
    # Оператор "морж", позволяющий одновременно и присвоить значение и проверить его.
    if updated_seller := await session.get(Seller, seller_id):
        updated_seller.first_name = new_data.first_name
        updated_seller.last_name = new_data.last_name
        updated_seller.email = new_data.email
        await session.flush()
        return updated_seller

    return Response(status_code=status.HTTP_404_NOT_FOUND)
