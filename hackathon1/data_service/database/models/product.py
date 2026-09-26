from base import Base, UnitType
from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from typing import Optional


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    quantity: Mapped[int] = mapped_column(nullable=False)

    #price

    unit: Mapped[UnitType] = mapped_column(nullable=False)

    #price per unit

    description: Mapped[Optional[str]] = mapped_column(String(250))

    #asukoht

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp())

    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp())

    
    #---------------
    #Relationships
    #---------------
    
    #ManyToMany
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="products")


    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="products")
