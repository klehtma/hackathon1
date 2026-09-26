from base import Base
from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    company_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp())
    
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp())

    #-------------
    #Relationships
    #-------------

    users: Mapped[list["User"]] = relationship(back_populates="company")


