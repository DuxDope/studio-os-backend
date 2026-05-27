from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from .. import models, auth, database

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    # 1. Buscamos al usuario
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    
    # 2. Verificamos existencia y clave
    if not user or not auth.verificar_password(password, user.password_hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    # 3. Generamos el token
    token = auth.crear_token_acceso(data={"sub": user.email, "id": user.id})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"nombre": user.nombre, "email": user.email}
    }

# Agrégalo a tu backend en routers/usuarios.py o donde tengas las rutas de usuarios
@router.get("/lista-tatuadores")
def obtener_tatuadores(db: Session = Depends(database.get_db)):
    # Asumo que tus usuarios tienen un rol o simplemente los traemos a todos
    tatuadores = db.query(models.Usuario).all() 
    return [{"id": t.id, "nombre": t.email} for t in tatuadores] # Ajusta según cómo guardes el nombre