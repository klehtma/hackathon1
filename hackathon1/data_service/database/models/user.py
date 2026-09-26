from base import Base, StatusType, UserType
from sqlalchemy import Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from typing import Optional, List


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True) #ettevõte table

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False) #user_id --> (users) company_id
    
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    account_status: Mapped[StatusType] = mapped_column(nullable=False, default=StatusType.INACTIVE)

    user_role: Mapped[UserType] = mapped_column(nullable=False, default=UserType.CHILD_USER)

    verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    password_hash: Mapped[str] = mapped_column(String(60), nullable=False) #
    remember_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp())
    
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp())


    #-------------
    #Relationships
    #-------------

    products: Mapped[List["Product"]] = relationship(back_populates="user")

    followings: Mapped[List["Follow"]] = relationship(back_populates="user")

    followers: Mapped[List["Follow"]] = relationship(back_populates="target_user")

    company: Mapped["Company"] = relationship(back_populates="users")



    
    