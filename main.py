from fastapi import FastAPI
from app.routes import auth, keys, wallet
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# create tables (for dev; in prod use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(wallet.router)