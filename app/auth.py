from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Configuración secreta (En un SaaS real, esto va en el archivo .env)
SECRET_KEY = "TU_LLAVE_SECRETA_SUPER_SEGURA_123" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # El login dura 1 día

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para encriptar claves
def obtener_hash_password(password):
    return pwd_context.hash(password)

# Función para verificar si la clave es correcta
def verificar_password(password_plano, password_hashed):
    return pwd_context.verify(password_plano, password_hashed)

# Función para crear el token de acceso
def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)