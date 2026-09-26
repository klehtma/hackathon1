from base import Base, StatusType
from sqlalchemy import TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from typing import Optional


class Follow(Base):
    __tablename__ = "follows"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) #user_id --> (follows) target_user_id

    target_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)

    status: Mapped[StatusType] = mapped_column(
        nullable=False, 
        default=StatusType.ACTIVE)

    started_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp())

    

    #-------------
    #Relationships
    #-------------

    
    user: Mapped["User"] = relationship(back_populates="followings", foreign_keys=[user_id])

    target_user: Mapped[Optional["User"]] = relationship(back_populates="followers", foreign_keys=[target_user_id])

    category: Mapped[Optional["Category"]] = relationship(back_populates="followers")

