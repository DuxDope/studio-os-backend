from app.database import SessionLocal
from app import models, auth
import uuid

def crear_usuario():
    db = SessionLocal()
    try:
        # Definimos tus credenciales
        email_nuevo = "admin@supertrebol.cl"
        password_plana = "admin123" # <--- Cambia esta clave si quieres
        
        # Encriptamos la clave usando tu función de auth.py
        password_encriptada = auth.obtener_hash_password(password_plana)
        
        nuevo_usuario = models.Usuario(
            id=str(uuid.uuid4()),
            email=email_nuevo,
            nombre="Admin Super Trebol",
            password_hashed=password_encriptada,
            activo=True
        )
        
        db.add(nuevo_usuario)
        db.commit()
        print(f"✅ Usuario creado con éxito!")
        print(f"📧 Email: {email_nuevo}")
        print(f"🔑 Password: {password_plana}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_usuario()