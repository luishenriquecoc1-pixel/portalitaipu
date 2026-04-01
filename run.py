import uvicorn
from app.main import app
from app.database import engine, Base
from app.models import *
from app.seed import seed_admin

Base.metadata.create_all(bind=engine)
seed_admin()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5050, reload=True)
