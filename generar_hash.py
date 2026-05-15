import bcrypt

# Pon tu contraseña real aquí
nueva_clave = "Rusvel1012"

# Generar el hash de forma directa
password_bytes = nueva_clave.encode('utf-8')
salt = bcrypt.gensalt()
hash_generado = bcrypt.hashpw(password_bytes, salt)

print(f"\nCopia este código hash EXACTAMENTE (incluyendo los $):\n")
print(hash_generado.decode('utf-8'))
print("\n")