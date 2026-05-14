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