from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

router_abono = APIRouter(prefix="/abono", tags=["Abono"])

class AbonoRequest(BaseModel):
    cliente_id:  int
    monto:       int       # en pesos CLP, entero
    descripcion: str = ""

# ── Ver saldo ──────────────────────────────────────────────────────────────
@router_abono.get("/saldo/{cliente_id}")
def get_saldo(cliente_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    movimientos = (
        db.query(AbonoMovimiento)
        .filter(AbonoMovimiento.cliente_id == cliente_id)
        .order_by(AbonoMovimiento.fecha.desc())
        .limit(20)
        .all()
    )
    return {
        "saldo":       cliente.saldo_abono,
        "movimientos": [
            {
                "id":          m.id,
                "monto":       m.monto,
                "tipo":        m.tipo,
                "descripcion": m.descripcion,
                "fecha":       m.fecha.isoformat(),
            }
            for m in movimientos
        ],
    }

# ── Cargar abono ───────────────────────────────────────────────────────────
@router_abono.post("/cargar")
def cargar_abono(data: AbonoRequest, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cliente.saldo_abono += data.monto
    mov = AbonoMovimiento(
        cliente_id=data.cliente_id,
        monto=data.monto,
        tipo="carga",
        descripcion=data.descripcion or "Carga de saldo",
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Saldo cargado", "nuevo_saldo": cliente.saldo_abono}

# ── Descontar abono ────────────────────────────────────────────────────────
@router_abono.post("/descontar")
def descontar_abono(data: AbonoRequest, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if cliente.saldo_abono < data.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    cliente.saldo_abono -= data.monto
    mov = AbonoMovimiento(
        cliente_id=data.cliente_id,
        monto=data.monto,
        tipo="descuento",
        descripcion=data.descripcion or "Pago con abono",
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"mensaje": "Descuento aplicado", "nuevo_saldo": cliente.saldo_abono}