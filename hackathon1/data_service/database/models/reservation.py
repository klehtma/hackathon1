from base import Base
from sqlalchemy import TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    reserved_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp())

    #-------------
    #Relationships
    #-------------

    user: Mapped["User"] = relationship(back_populates="reservations")

    product: Mapped["Product"] = relationship(back_populates="reservations")