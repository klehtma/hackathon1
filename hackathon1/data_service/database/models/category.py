from base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, func, TIMESTAMP, String
import datetime
from typing import List

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        )

    #--------------
    #Relationships
    #--------------

    products: Mapped[List["Product"]] = relationship(back_populates="category")

    subscribers: Mapped[List["Subscription"]] = relationship(back_populates="category")