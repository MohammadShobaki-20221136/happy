from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:1234@localhost:5432/happy_db"
engine = create_engine(DATABASE_URL, echo=True)