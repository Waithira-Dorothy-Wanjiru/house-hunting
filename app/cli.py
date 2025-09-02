import click
from getpass import getpass
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from contextlib import contextmanager
import os
import shutil

# ----- DATABASE SETUP -----
Base = declarative_base()
engine = create_engine("sqlite:///house_hunting.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

# ----- MODELS -----
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    password = Column(String, nullable=False)
    role = Column(String, default="agent")  # 'agent', 'admin', or 'user'
    properties = relationship("Property", back_populates="owner")

class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="properties")
    media = relationship("Media", back_populates="property")

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    file_path = Column(String, nullable=False)
    property = relationship("Property", back_populates="media")

Base.metadata.create_all(bind=engine)

# ----- SESSION CONTEXT -----
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ----- DEFAULT ADMIN SETUP -----
def ensure_default_admin(session):
    admin = session.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", email="admin@homly.com", phone="", password="adminme", role="admin")
        session.add(admin)
        session.flush()
        click.echo("Default admin account created (username: admin, password: adminme).")

# ----- SIGNUP / SIGNIN -----
def signup(session):
    click.echo("=== Sign Up ===")
    username = input("Username: ")
    email = input("Email: ")
    phone = input("Phone: ")
    password = getpass("Password: ")
    role = input("Role (agent/admin/user, default agent): ").lower() or "agent"

    if session.query(User).filter_by(username=username).first():
        click.echo("Username already exists!")
        return None
    user = User(username=username, email=email, phone=phone, password=password, role=role)
    session.add(user)
    session.flush()
    click.echo(f"User '{username}' created with ID {user.id} (role={user.role})")
    return user

def signin(session):
    click.echo("=== Sign In ===")
    username = input("Username: ")
    password = getpass("Password: ")
    user = session.query(User).filter_by(username=username, password=password).first()
    if not user:
        click.echo("Invalid credentials!")
        return None
    click.echo(f"Welcome {user.username}!")
    return user

# ----- AGENT DASHBOARD -----
def agent_menu(user, session):
    while True:
        click.echo(f"\nHello, {user.username} ({user.email}, {user.phone})")
        click.echo("1. Post Property")
        click.echo("2. View My Properties")
        click.echo("3. Search My Properties")
        click.echo("4. Logout")
        choice = input("Select: ")

        if choice == "1":
            post_property(user, session)
            list_my_properties(user, session)
        elif choice == "2":
            list_my_properties(user, session)
        elif choice == "3":
            search_agent_properties(user, session)
        elif choice == "4":
            break
        else:
            click.echo("Invalid option.")

# ----- USER DASHBOARD -----
def user_menu(user, session):
    while True:
        click.echo(f"\nWelcome, {user.username} ({user.email})")
        click.echo("1. Search Properties")
        click.echo("2. Logout")
        choice = input("Select: ")

        if choice == "1":
            search_properties(session)
        elif choice == "2":
            break
        else:
            click.echo("Invalid option.")

# ----- ADMIN DASHBOARD -----
def admin_menu(user, session):
    while True:
        click.echo(f"\nAdmin Panel ({user.username})")
        click.echo("1. Add User")
        click.echo("2. Delete User")
        click.echo("3. Add Property")
        click.echo("4. Delete Property")
        click.echo("5. List Users")
        click.echo("6. Search Users")
        click.echo("7. List Properties")
        click.echo("8. Search Properties")
        click.echo("9. Logout")
        choice = input("Select: ")

        if choice == "1":
            signup(session)
        elif choice == "2":
            delete_user(session)
        elif choice == "3":
            post_property(user, session)
        elif choice == "4":
            delete_property(session)
        elif choice == "5":
            list_users(session)
        elif choice == "6":
            search_users(session)
        elif choice == "7":
            list_properties(session)
        elif choice == "8":
            search_properties(session)
        elif choice == "9":
            break
        else:
            click.echo("Invalid option.")

# ----- PROPERTY / MEDIA FUNCTIONS -----
def post_property(user, session):
    click.echo("=== Post Property ===")
    name = input("Property name: ")
    location = input("Location: ")

    uploads_folder = "uploads"
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

    prop = Property(name=name, location=location, owner_id=user.id)
    session.add(prop)
    session.flush()
    click.echo(f"Property '{name}' added with ID {prop.id}")

    while True:
        file_path = input("Add image/video file path (or 'done' to finish): ")
        if file_path.lower() == "done":
            break
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(uploads_folder, filename)
            shutil.copy(file_path, dest_path)
            media = Media(property_id=prop.id, file_path=dest_path)
            session.add(media)
            session.flush()
            click.echo(f"Media '{filename}' added to uploads folder and database.")
        else:
            click.echo("File does not exist. Try again.")

def list_my_properties(user, session):
    props = session.query(Property).filter_by(owner_id=user.id).all()
    if not props:
        click.echo("No properties found.")
        return
    for p in props:
        click.echo(f"{p.id}: {p.name} in {p.location}")
        for m in p.media:
            click.echo(f" - Media: {m.file_path}")

def search_agent_properties(user, session):
    term = input("Enter property name/location to search: ").lower()
    props = session.query(Property).filter_by(owner_id=user.id).all()
    results = [p for p in props if term in p.name.lower() or term in p.location.lower()]
    if not results:
        click.echo("No matching properties found.")
        return
    for p in results:
        click.echo(f"{p.id}: {p.name} in {p.location}")
        for m in p.media:
            click.echo(f" - Media: {m.file_path}")

# ----- ADMIN FUNCTIONS -----
def list_users(session):
    users = session.query(User).all()
    for u in users:
        click.echo(f"{u.id}: {u.username} ({u.email}, {u.phone}, role={u.role})")

def list_properties(session):
    props = session.query(Property).all()
    for p in props:
        click.echo(f"{p.id}: {p.name} in {p.location} (owner {p.owner.username})")
        for m in p.media:
            click.echo(f" - Media: {m.file_path}")

def delete_user(session):
    list_users(session)
    uid = input("Enter user ID to delete: ")
    user = session.query(User).filter_by(id=uid).first()
    if user:
        session.delete(user)
        click.echo(f"User {uid} deleted.")
    else:
        click.echo("User not found.")

def delete_property(session):
    list_properties(session)
    pid = input("Enter property ID to delete: ")
    prop = session.query(Property).filter_by(id=pid).first()
    if prop:
        session.delete(prop)
        click.echo(f"Property {pid} deleted.")
    else:
        click.echo("Property not found.")

# ----- SEARCH FUNCTIONS -----
def search_users(session):
    term = input("Enter username/email to search: ").lower()
    users = session.query(User).all()
    results = [u for u in users if term in u.username.lower() or term in u.email.lower()]
    if not results:
        click.echo("No matching users found.")
    for u in results:
        click.echo(f"{u.id}: {u.username} ({u.email}, {u.phone}, role={u.role})")

def search_properties(session):
    term = input("Enter property name/location to search: ").lower()
    props = session.query(Property).all()
    results = [p for p in props if term in p.name.lower() or term in p.location.lower()]
    if not results:
        click.echo("No matching properties found.")
    for p in results:
        click.echo(f"{p.id}: {p.name} in {p.location} (owner {p.owner.username})")
        for m in p.media:
            click.echo(f" - Media: {m.file_path}")

# ----- MAIN LOOP -----
def main():
    click.echo("Welcome to Homly!\n")
    with get_session() as session:
        ensure_default_admin(session)
        while True:
            click.echo("1. Sign Up")
            click.echo("2. Sign In")
            click.echo("3. Exit")
            choice = input("Select: ")

            if choice == "1":
                user = signup(session)
                if user:
                    if user.role == "agent":
                        agent_menu(user, session)
                    elif user.role == "admin":
                        admin_menu(user, session)
                    elif user.role == "user":
                        user_menu(user, session)
            elif choice == "2":
                user = signin(session)
                if user:
                    if user.role == "agent":
                        
                        agent_menu(user, session)
                    elif user.role == "admin":
                        admin_menu(user, session)
                    elif user.role == "user":
                        user_menu(user, session)
            elif choice == "3":
                click.echo("Goodbye!")
                break
            else:
                click.echo("Invalid option.")

if __name__ == "__main__":
    main()
