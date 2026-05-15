from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import engine
from . import models
from .routers import clientes, cotizaciones, promociones, usuarios, citas
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
os.makedirs("uploads", exist_ok=True) # Crea la carpeta si no existe
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Crear la carpeta uploads si no existe para que no de error
if not os.path.exists("uploads"):
    os.makedirs("uploads")

if __name__ == "__main__":
    # Esto lee el puerto que Railway te da, o usa 8000 si estás en local
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)

# Permitir que el frontend vea las fotos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.router)
app.include_router(cotizaciones.router)
app.include_router(promociones.router)
app.include_router(usuarios.router)
app.include_router(citas.router)
