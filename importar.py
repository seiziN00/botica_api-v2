import csv
from pathlib import Path
from sqlmodel import Session, select
from app.database import engine
from app.models import SQLModel, ProductoModel, LoteModel

CSV_FILE = Path("productos.csv")


def importar_productos():
    # Verificar y crear tablas si no existen
    SQLModel.metadata.create_all(engine)
    
    try:
        with Session(engine) as session:
            existe_producto = session.exec(select(ProductoModel)).first()
            if existe_producto:
                print("⚠️ La base de datos ya contiene productos. No se realizó la importación masiva.")
                return

            if not CSV_FILE.exists():
                print(f"❌ No se encontró el archivo {CSV_FILE}")
                return

            with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as archivo:
                reader = csv.DictReader(archivo, delimiter=",")
                contador = 0

                for fila in reader:
                    nombre = fila["PRODUCTO FORMATEADO"].strip()
                    
                    precio = float(
                        fila["P. VENTA"]
                        .strip()
                        .replace(",", ".")
                    )
                    
                    stock = int(
                        fila["TOTAL/ STOCK"].strip()
                    )

                    producto_obj = ProductoModel(
                        producto=nombre,
                        precio_venta=precio,
                    )
                    session.add(producto_obj)
                    
                    session.flush()
                    
                    lote_obj = LoteModel(
                        producto_id=producto_obj.id,
                        codigo="LOTE-INICIAL",
                        stock=stock
                    )
                    session.add(lote_obj)
                    contador += 1

                session.commit()
                print(f"✅ Importación completada: {contador} productos y sus lotes iniciales guardados con éxito.")

    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
        raise


if __name__ == "__main__":
    importar_productos()