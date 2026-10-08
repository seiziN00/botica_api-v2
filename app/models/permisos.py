# app/models/permisos.py

from enum import Enum


class RolEnum(str, Enum):
    STAFF = "staff"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class PermisoEnum(str, Enum):
    # Catálogo
    CATALOGO_VER = "catalogo:ver"

    # Ventas
    VENTA_CREAR = "venta:crear"
    VENTA_VER = "venta:ver"
    VENTA_VER_DIA = "venta:ver_dia"

    # Inventario y lotes
    INVENTARIO_VER = "inventario:ver"
    LOTE_CREAR = "lote:crear"
    LOTE_EDITAR = "lote:editar"
    KARDEX_VER = "kardex:ver"

    # Productos y precios
    PRODUCTO_CREAR = "producto:crear"
    PRODUCTO_EDITAR = "producto:editar"
    PRECIO_EDITAR = "precio:editar"

    # Usuarios
    STAFF_GESTIONAR = "staff:gestionar"
    ADMIN_CREAR = "admin:crear"
    ADMIN_ELIMINAR = "admin:eliminar"

    # Reportes y auditoría
    REPORTE_FINANCIERO_VER = "reporte_financiero:ver"
    AUDITORIA_VER = "auditoria:ver"

    # Permisos temporales
    PERMISO_OTORGAR = "permiso:otorgar"

    # Facturas / OCR
    FACTURA_PROCESAR = "factura:procesar"


PERMISOS_POR_ROL: dict[RolEnum, set[PermisoEnum]] = {
    RolEnum.STAFF: {
        PermisoEnum.CATALOGO_VER,
        PermisoEnum.VENTA_CREAR,
    },
    RolEnum.ADMIN: {
        PermisoEnum.CATALOGO_VER,
        PermisoEnum.VENTA_CREAR,
        PermisoEnum.VENTA_VER,
        PermisoEnum.VENTA_VER_DIA,
        PermisoEnum.INVENTARIO_VER,
        PermisoEnum.LOTE_CREAR,
        PermisoEnum.LOTE_EDITAR,
        PermisoEnum.KARDEX_VER,
        PermisoEnum.PRODUCTO_CREAR,
        PermisoEnum.PRODUCTO_EDITAR,
        PermisoEnum.STAFF_GESTIONAR,
        PermisoEnum.FACTURA_PROCESAR,
    },
    RolEnum.SUPERADMIN: set(PermisoEnum),
}
