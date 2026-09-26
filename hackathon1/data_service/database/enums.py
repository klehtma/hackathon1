import enum

class StatusType(enum.Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"

class UnitType(enum.Enum):
    KG = "kilogram"
    T = "tonne"
    L = "litre"

class UserType(enum.Enum):
    CHILD_USER = "child_user"
    PARENT_USER = "parent_user"
    ADMIN = "admin"

#user type
