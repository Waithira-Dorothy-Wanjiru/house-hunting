from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db import Base  # make sure this points to your Base

# ----- USER MODEL -----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)  # optional phone number
    password = Column(String, nullable=False)  # plaintext for now (consider hashing)
    role = Column(
        Enum("agent", "admin", "user", name="user_roles"),
        default="agent",
        nullable=False
    )
    properties = relationship("Property", back_populates="owner")


# ----- PROPERTY MODEL -----
class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="properties")
    media = relationship("Media", back_populates="property")


# ----- MEDIA MODEL -----
class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    file_path = Column(String, nullable=False)
    property = relationship("Property", back_populates="media")
