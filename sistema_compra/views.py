from abc import ABC, abstractmethod

from models import Cliente, Producto, Venta, Proveedor ,Compra
from shared.json_manager import GestorJSON


# =====================================================================
# LA INTERFAZ DEL CRUD: clase abstracta con la lógica común
# =====================================================================
class CrudBase(ABC):
    """Define QUÉ hace todo controlador y ya implementa el CÓMO que se repite."""

    MODELO = None            # clase del modelo (Cliente, Producto, Venta...)
    ARCHIVO = None           # ruta del JSON
    NOMBRE = "registro"      # para los mensajes
    CAMPOS_BUSCABLES = ()

    def __init__(self):
        if self.MODELO is None or self.ARCHIVO is None:
            raise ValueError("El controlador debe definir MODELO y ARCHIVO")
        self._gestor = GestorJSON(self.ARCHIVO)

    # ---------- MÉTODO ABSTRACTO: cada controlador pone SUS reglas ----------
    @abstractmethod
    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""

    # ---------- GANCHO: se puede sobrescribir, pero tiene versión por defecto ----------
    def preparar(self, datos):
        """Deja los datos listos para el constructor del Modelo."""
        return {campo: datos.get(campo, "") for campo in self.MODELO.CAMPOS}

    # ---------- LÓGICA COMÚN: se hereda sin tocar ----------
    def registros(self):
        return self._gestor.leer()

    def siguiente_id(self):
        ids = [registro["id"] for registro in self.registros()]
        return max(ids) + 1 if ids else 1

    def listar(self):
        return [self.MODELO.desde_diccionario(r) for r in self.registros()]

    def obtener(self, id_registro):
        for objeto in self.listar():
            if objeto.id == id_registro:
                return objeto
        return None

    def existe(self, id_registro):
        return any(r["id"] == id_registro for r in self.registros())

    def buscar(self, termino):
        termino = str(termino).strip().lower()
        if not termino:
            return []
        encontrados = []
        for registro in self.registros():
            for campo in self.CAMPOS_BUSCABLES:
                if termino in str(registro.get(campo, "")).lower():
                    encontrados.append(self.MODELO.desde_diccionario(registro))
                    break
        return encontrados

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        try:
            objeto = self.MODELO(self.siguiente_id(), **self.preparar(datos))
        except ValueError as excepcion:
            return False, str(excepcion)

        registros = self.registros()
        registros.append(objeto.a_diccionario())
        if not self._gestor.guardar(registros):
            return False, "No se pudo escribir el archivo"
        return True, f"{self.NOMBRE.capitalize()} creado: {objeto.etiqueta()}"

    def actualizar(self, id_registro, cambios):
        desconocidos = set(cambios) - set(self.MODELO.CAMPOS)
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        if not cambios:
            return False, "No se indicó ningún cambio"

        objeto = self.obtener(id_registro)
        if objeto is None:
            return False, f"No existe {self.NOMBRE} con id {id_registro}"

        error = self.validar(cambios, id_actual=id_registro)
        if error:
            return False, error

        try:
            for campo, valor in cambios.items():
                setattr(objeto, campo, valor)     # cada setter valida
        except ValueError as excepcion:
            return False, str(excepcion)

        registros = self.registros()
        for indice, registro in enumerate(registros):
            if registro["id"] == id_registro:
                registros[indice] = objeto.a_diccionario()
                break
        self._gestor.guardar(registros)
        return True, f"{self.NOMBRE.capitalize()} {id_registro} actualizado"

    def eliminar(self, id_registro):
        registros = self.registros()
        quedan = [r for r in registros if r["id"] != id_registro]
        if len(quedan) == len(registros):
            return False, f"No existe {self.NOMBRE} con id {id_registro}"
        self._gestor.guardar(quedan)
        return True, f"{self.NOMBRE.capitalize()} {id_registro} eliminado"


# =====================================================================
class ClienteController(CrudBase):
    MODELO = Cliente
    ARCHIVO = "data/clientes.json"
    NOMBRE = "cliente"
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "telefono", "ciudad")

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            faltantes = [c for c in self.MODELO.OBLIGATORIOS
                         if not str(datos.get(c, "")).strip()]
            if faltantes:
                return f"Faltan campos obligatorios: {', '.join(faltantes)}"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            usados = {r["email"].lower() for r in self.registros()
                      if r["id"] != id_actual}
            if email in usados:
                return "Ese email ya está registrado"
        return None

#======================================================================


class ProveedorController(CrudBase):
    MODELO = Proveedor
    ARCHIVO = "data/proveedor.json"
    NOMBRE = "proveedor"
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "ruc", "empresa")

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            faltantes = [
                campo for campo in self.MODELO.OBLIGATORIOS
                if not str(datos.get(campo, "")).strip()
            ]

            if faltantes:
                return (
                    "Faltan campos obligatorios: "
                    + ", ".join(faltantes)
                )

        if "email" in datos:
            email = str(datos["email"]).strip().lower()

            usados = {
                r["email"].lower()
                for r in self.registros()
                if r["id"] != id_actual
            }

            if email in usados:
                return "Ese email ya está registrado"

        if "ruc" in datos:
            ruc = str(datos["ruc"]).strip()

            usados = {
                str(r.get("ruc", ""))
                for r in self.registros()
                if r["id"] != id_actual
            }

            if ruc in usados:
                return "Ese RUC ya está registrado"

        return None

# =====================================================================
class ProductoController(CrudBase):
    MODELO = Producto
    ARCHIVO = "data/productos.json"
    NOMBRE = "producto"
    CAMPOS_BUSCABLES = ("nombre",)

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            faltantes = [c for c in self.MODELO.OBLIGATORIOS
                         if not str(datos.get(c, "")).strip()]
            if faltantes:
                return f"Faltan campos obligatorios: {', '.join(faltantes)}"

        if "nombre" in datos and str(datos["nombre"]).strip():
            nombre = str(datos["nombre"]).strip().title()
            usados = {r["nombre"].title() for r in self.registros()
                      if r["id"] != id_actual}
            if nombre in usados:
                return f"Ya existe un producto llamado {nombre}"
        return None

    def preparar(self, datos):
        valores = super().preparar(datos)
        valores["stock"] = valores.get("stock") or 0
        return valores

    # --- propio de productos ---
    def descontar_stock(self, producto_id, cantidad):
        producto = self.obtener(producto_id)
        if producto is None:
            return False, f"No existe producto con id {producto_id}"
        try:
            producto.descontar_stock(cantidad)
        except ValueError as excepcion:
            return False, str(excepcion)
        return self.actualizar(producto_id, {"stock": producto.stock})
    

    def aumentar_stock(self, producto_id, cantidad):
        producto = self.obtener(producto_id)

        if producto is None:
            return False, f"No existe producto con id {producto_id}"

        try:
            producto.aumentar_stock(cantidad)
        except (ValueError, TypeError) as excepcion:
            return False, str(excepcion)

        return self.actualizar(
            producto_id,
            {"stock": producto.stock}
        )

    def con_stock_bajo(self, minimo=5):
        return [p for p in self.listar() if p.stock <= minimo]


# =====================================================================
class VentaController(CrudBase):
    """Depende de los otros dos controladores: ASOCIACIÓN entre controladores."""

    MODELO = Venta
    ARCHIVO = "data/ventas.json"
    NOMBRE = "venta"
    CAMPOS_BUSCABLES = ("fecha",)

    def __init__(self, clientes=None, productos=None):
        super().__init__()
        self.clientes = clientes or ClienteController()
        self.productos = productos or ProductoController()

    def validar(self, datos, id_actual=None):
        try:
            cliente_id = int(datos.get("cliente_id", 0))
        except (TypeError, ValueError):
            return "El cliente_id debe ser un número"

        if not self.clientes.existe(cliente_id):
            return f"No existe un cliente con id {cliente_id}"

        items = datos.get("items", [])
        if not items:
            return "La venta debe tener al menos un producto"

        for item in items:
            producto = self.productos.obtener(int(item["producto_id"]))
            if producto is None:
                return f"No existe producto con id {item['producto_id']}"
            if not producto.hay_stock(int(item["cantidad"])):
                return (f"Stock insuficiente de {producto.nombre}: "
                        f"hay {producto.stock}, piden {item['cantidad']}")
        return None

    def crear(self, datos):
        """Sobrescribe al padre: una venta se arma con sus detalles y mueve stock."""
        error = self.validar(datos)
        if error:
            return False, error
        try:
            venta = Venta(self.siguiente_id(), datos["cliente_id"], datos.get("fecha", ""))
            for item in datos["items"]:
                producto = self.productos.obtener(int(item["producto_id"]))
                venta.agregar_detalle(producto, int(item["cantidad"]))
        except ValueError as excepcion:
            return False, str(excepcion)

        for detalle in venta.detalles:
            exito, mensaje = self.productos.descontar_stock(detalle.producto_id,
                                                            detalle.cantidad)
            if not exito:
                return False, mensaje

        registros = self.registros()
        registros.append(venta.a_diccionario())
        self._gestor.guardar(registros)
        return True, f"Venta {venta.id} registrada por ${venta.total:.2f}"

    def factura(self, id_venta):
        """Texto de la factura: junta venta + cliente + detalles."""
        venta = self.obtener(id_venta)
        if venta is None:
            return None
        cliente = self.clientes.obtener(venta.cliente_id)
        lineas = [
            f"FACTURA #{venta.id}   fecha: {venta.fecha}",
            f"Cliente: {cliente.nombre_completo if cliente else 'eliminado'}",
            "-" * 46,
        ]
        for detalle in venta.detalles:
            lineas.append(f"  {detalle}")
        lineas.append("-" * 46)
        lineas.append(f"  TOTAL: ${venta.total:.2f}  ({venta.cantidad_items} ítems)")
        return "\n".join(lineas)

    def ventas_de_cliente(self, cliente_id):
        return [v for v in self.listar() if v.cliente_id == cliente_id]
    

class CompraController(CrudBase):
    """Controlador para registrar compras y actualizar el inventario."""

    MODELO = Compra
    ARCHIVO = "data/compra.json"
    NOMBRE = "compra"
    CAMPOS_BUSCABLES = ("fecha",)

    def __init__(self, proveedor=None, productos=None):
        super().__init__()
        self.proveedor = proveedor or ProveedorController()
        self.productos = productos or ProductoController()

    def validar(self, datos, id_actual=None):
        try:
            proveedor_id = int(datos.get("proveedor_id", 0))
        except (TypeError, ValueError):
            return "El id del proveedor debe ser numérico"

        if not self.proveedor.existe(proveedor_id):
            return f"No existe un proveedor con id {proveedor_id}"

        items = datos.get("items", [])

        if not items:
            return "La compra debe tener al menos un producto"

        for item in items:
            try:
                producto_id = int(item["producto_id"])
                cantidad = int(item["cantidad"])
                costo = float(item["costo_unitario"])
            except (KeyError, TypeError, ValueError):
                return "Los datos del producto o del costo son inválidos"

            if self.productos.obtener(producto_id) is None:
                return f"No existe producto con id {producto_id}"

            if cantidad <= 0:
                return "La cantidad debe ser mayor a 0"

            if costo <= 0:
                return "El costo unitario debe ser mayor a 0"

        return None

    def crear(self, datos):
        error = self.validar(datos)

        if error:
            return False, error

        try:
            compra = Compra(
                self.siguiente_id(),
                datos["proveedor_id"],
                datos.get("fecha", "")
            )

            for item in datos["items"]:
                producto = self.productos.obtener(
                    int(item["producto_id"])
                )

                compra.agregar_detalle(
                    producto,
                    int(item["cantidad"]),
                    float(item["costo_unitario"])
                )

        except (ValueError, KeyError, TypeError) as excepcion:
            return False, str(excepcion)

        # Guardar primero el registro de la compra.
        registros = self.registros()
        registros.append(compra.a_diccionario())

        if not self._gestor.guardar(registros):
            return False, "No se pudo guardar la compra en el archivo JSON"

        # Actualizar el stock de los productos comprados.
        for detalle in compra.detalles:
            exito, mensaje = self.productos.aumentar_stock(
                detalle.producto_id,
                detalle.cantidad
            )

            if not exito:
                return False, (
                    f"La compra {compra.id} se guardó, pero hubo un "
                    f"problema al actualizar el inventario: {mensaje}"
                )

        return True, (
            f"Compra {compra.id} registrada correctamente "
            f"por ${compra.total:.2f}"
        )

    def factura(self, id_compra):
        """Genera el detalle de una compra registrada."""

        compra = self.obtener(id_compra)

        if compra is None:
            return None

        proveedor = self.proveedor.obtener(compra.proveedor_id)

        lineas = [
            f"FACTURA DE COMPRA #{compra.id}   Fecha: {compra.fecha}",
            (
                "Proveedor: "
                + (
                    proveedor.nombre_completo
                    if proveedor
                    else "Proveedor eliminado"
                )
            ),
            "-" * 50,
        ]

        for detalle in compra.detalles:
            lineas.append(f"  {detalle}")

        lineas.append("-" * 50)
        lineas.append(
            f"  TOTAL: ${compra.total:.2f} "
            f"({compra.cantidad_items} unidades)"
        )

        return "\n".join(lineas)
