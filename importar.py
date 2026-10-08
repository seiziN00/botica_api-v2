import csv
from pathlib import Path
from sqlmodel import Session, select
from app.db.session import engine
from app.models import SQLModel, ProductoModel, LoteModel, ProductoPresentacion

CSV_FILE = Path("productos.csv")


def importar_productos():
    # Verificar y crear tablas si no existen
    SQLModel.metadata.create_all(engine)
    
    try:
        with Session(engine) as session:
            # Verificar si ya existen productos para evitar duplicados
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
                    
                    # Limpiar y convertir precio de venta
                    try:
                        precio = float(
                            fila["P. VENTA"]
                            .strip()
                            .replace(",", ".")
                        )
                    except (ValueError, KeyError):
                        precio = 0.0
                    
                    # Limpiar y convertir stock
                    try:
                        stock = int(
                            fila["TOTAL/ STOCK"].strip()
                        )
                    except (ValueError, KeyError):
                        stock = 0

                    # 1. Crear el Producto
                    producto_obj = ProductoModel(
                        producto=nombre,
                    )
                    session.add(producto_obj)
                    session.flush() # Genera el ID del producto en memoria para usarlo abajo
                    
                    # 2. Crear el Lote Inicial vinculado al producto
                    lote_obj = LoteModel(
                        producto_id=producto_obj.id,
                        codigo="LOTE-INICIAL",
                        stock=stock
                    )
                    session.add(lote_obj)

                    # 3. Crear la Presentación 'unidad' con su Precio de Venta
                    presentacion_obj = ProductoPresentacion(
                        producto_id=producto_obj.id,
                        tipo="unidad",
                        unidades_base=1,
                        precio_venta=precio,
                        predeterminada=True
                    )
                    session.add(presentacion_obj)

                    contador += 1

                # Confirmar todos los cambios en la base de datos de un solo golpe
                session.commit()
                print(f"✅ Importación completada: {contador} productos, lotes y precios configurados con éxito.")

    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
        raise


if __name__ == "__main__":
    importar_productos()