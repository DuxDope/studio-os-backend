from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models, database
from datetime import datetime

router = APIRouter(prefix="/abono", tags=["Abono"])

class AbonoRequest(BaseModel):
    cliente_id: int
    monto: int
    descripcion: str = ""

@router.get("/saldo/{cliente_id}")
def get_saldo(cliente_id: int, db: Session = Depends(database.get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    movimientos = (
        db.query(models.AbonoMovimiento)
        .filter(models.AbonoMovimiento.cliente_id == cliente_id)
        .order_by(models.AbonoMovimiento.fecha.desc())
        .limit(20)
        .all()
    )
    return {
        "saldo": cliente.saldo_abono,
        "movimientos": [
            {
                "id": m.id,
                "monto": m.monto,
                "tipo": m.tipo,
                "descripcion": m.descripcion,
                "fecha": m.fecha.isoformat(),
            }
            for m in movimientos
        ],
    }

@router.post("/cargar")
def cargar_abono(data: AbonoRequest, db: Session = Depends(database.get_db)):
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
        
    cliente = db.query(models.Cliente).filter(models.Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    cliente.saldo_abono += data.monto
    mov = models.AbonoMovimiento(
        cliente_id=data.cliente_id,
        monto=data.monto,
        tipo="carga",
        descripcion=data.descripcion or "Carga de saldo",
        fecha=datetime.utcnow()
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Saldo cargado", "nuevo_saldo": cliente.saldo_abono}

@router.post("/descontar")
def descontar_abono(data: AbonoRequest, db: Session = Depends(database.get_db)):
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
        
    cliente = db.query(models.Cliente).filter(models.Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    if cliente.saldo_abono < data.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
        
    cliente.saldo_abono -= data.monto
    mov = models.AbonoMovimiento(
        cliente_id=data.cliente_id,
        monto=data.monto,
        tipo="descuento",
        descripcion=data.descripcion or "Pago con abono",
        fecha=datetime.utcnow()
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Descuento aplicado", "nuevo_saldo": cliente.saldo_abono}