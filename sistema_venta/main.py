
import os

from shared.herramientas import (
    imprimir_titulo,
    imprimir_exito,
    imprimir_error,
    imprimir_info,
    confirmar
)

from views import ClienteController, ProductoController, VentaController

from views_academico import (
    EstudianteController,
    DocenteController,
    MateriaController,
    MatriculaController
)


# =====================================================================
# MENÚ CRUD GENERAL: POLIMORFISMO
# =====================================================================
class MenuCRUD:

    def __init__(self, controlador, titulo):
        self._controlador = controlador
        self._titulo = titulo
        self._activo = True

        self._opciones = {
            "1": (f"Crear {controlador.NOMBRE}", self.crear),
            "2": ("Ver todos", self.listar),
            "3": ("Buscar", self.buscar),
            "4": ("Ver por id", self.ver_por_id),
            "5": ("Actualizar", self.actualizar),
            "6": ("Eliminar", self.eliminar),
            "0": ("Volver", self.volver),
        }

    # ---------- utilidades ----------
    @staticmethod
    def pausa():
        input("\nPresione Enter para continuar...")
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def pedir_entero(etiqueta):
        try:
            return int(input(etiqueta))
        except ValueError:
            return None

    @staticmethod
    def mostrar_resultado(exito, mensaje):
        if exito:
            imprimir_exito(mensaje)
        else:
            imprimir_error(mensaje)

    # ---------- operaciones CRUD ----------
    def pedir_datos(self):
        datos = {}

        for campo in self._controlador.MODELO.CAMPOS:
            datos[campo] = input(
                f"{campo.replace('_', ' ').capitalize()}: "
            ).strip()

        return datos

    def crear(self):
        imprimir_titulo(f"CREAR {self._controlador.NOMBRE.upper()}")

        self.mostrar_resultado(
            *self._controlador.crear(self.pedir_datos())
        )

        self.pausa()

    def listar(self):
        imprimir_titulo(self._titulo.upper())
        objetos = self._controlador.listar()

        if not objetos:
            imprimir_info("No hay registros todavía.")
        else:
            for objeto in objetos:
                print(f"  {objeto}")

            imprimir_info(f"Total: {len(objetos)}")

        self.pausa()

    def buscar(self):
        imprimir_titulo(f"BUSCAR {self._controlador.NOMBRE.upper()}")
        termino = input("Término: ").strip()
        encontrados = self._controlador.buscar(termino)

        if not encontrados:
            imprimir_info(f"Sin coincidencias para '{termino}'.")
        else:
            for objeto in encontrados:
                print(f"  {objeto}")

        self.pausa()

    def ver_por_id(self):
        imprimir_titulo(f"VER {self._controlador.NOMBRE.upper()}")
        id_registro = self.pedir_entero("Id: ")

        objeto = (
            self._controlador.obtener(id_registro)
            if id_registro is not None
            else None
        )

        if objeto is None:
            imprimir_error("No encontrado")
        else:
            for clave, valor in objeto.a_diccionario().items():
                print(f"  {str(clave).capitalize():<14}: {valor}")

        self.pausa()

    def actualizar(self):
        imprimir_titulo(
            f"ACTUALIZAR {self._controlador.NOMBRE.upper()}"
        )

        id_registro = self.pedir_entero("Id: ")

        objeto = (
            self._controlador.obtener(id_registro)
            if id_registro is not None
            else None
        )

        if objeto is None:
            imprimir_error("No encontrado")
            return self.pausa()

        imprimir_info(f"Editando: {objeto.etiqueta()}")
        print("Deje en blanco lo que no quiera cambiar.\n")

        cambios = {}

        for campo in self._controlador.MODELO.CAMPOS:
            actual = getattr(objeto, campo, "")
            nuevo = input(f"{campo.capitalize()} [{actual}]: ").strip()

            if nuevo:
                cambios[campo] = nuevo

        self.mostrar_resultado(
            *self._controlador.actualizar(id_registro, cambios)
        )

        self.pausa()

    def eliminar(self):
        imprimir_titulo(
            f"ELIMINAR {self._controlador.NOMBRE.upper()}"
        )

        id_registro = self.pedir_entero("Id: ")

        objeto = (
            self._controlador.obtener(id_registro)
            if id_registro is not None
            else None
        )

        if objeto is None:
            imprimir_error("No encontrado")
            return self.pausa()

        imprimir_info(f"Se eliminará: {objeto.etiqueta()}")

        if confirmar("¿Confirma?"):
            self.mostrar_resultado(
                *self._controlador.eliminar(id_registro)
            )
        else:
            imprimir_info("Operación cancelada")

        self.pausa()

    def volver(self):
        self._activo = False

    # ---------- bucle del menú ----------
    def mostrar_menu(self):
        imprimir_titulo(self._titulo)

        for tecla, (texto, _metodo) in self._opciones.items():
            print(f"  {tecla}. {texto}")

        print()

    def ejecutar(self):
        self._activo = True

        while self._activo:
            self.mostrar_menu()
            tecla = input("Opción: ").strip()

            if tecla not in self._opciones:
                imprimir_error("Opción no válida")
                self.pausa()
                continue

            self._opciones[tecla][1]()


# =====================================================================
# MENÚ ESPECIAL DE VENTAS: HERENCIA Y SOBRESCRITURA
# =====================================================================
class MenuVentas(MenuCRUD):

    def __init__(self, controlador):
        super().__init__(controlador, "VENTAS")

        self._opciones["1"] = ("Registrar venta", self.crear)
        self._opciones["7"] = ("Ver factura", self.ver_factura)

    def crear(self):
        imprimir_titulo("REGISTRAR VENTA")

        cliente_id = self.pedir_entero("Id del cliente: ")

        if cliente_id is None:
            imprimir_error("El id debe ser un número")
            return self.pausa()

        imprimir_info("Productos disponibles:")

        for producto in self._controlador.productos.listar():
            print(f"  {producto}")

        items = []

        while True:
            producto_id = self.pedir_entero(
                "\nId del producto (0 para terminar): "
            )

            if producto_id == 0:
                break

            if producto_id is None or producto_id < 0:
                imprimir_error("Id de producto inválido")
                continue

            cantidad = self.pedir_entero("Cantidad: ")

            if cantidad is None or cantidad <= 0:
                imprimir_error("La cantidad debe ser mayor que cero")
                continue

            items.append({
                "producto_id": producto_id,
                "cantidad": cantidad
            })

        self.mostrar_resultado(
            *self._controlador.crear({
                "cliente_id": cliente_id,
                "items": items
            })
        )

        self.pausa()

    def ver_factura(self):
        imprimir_titulo("FACTURA")

        id_venta = self.pedir_entero("Id de la venta: ")

        texto = (
            self._controlador.factura(id_venta)
            if id_venta is not None
            else None
        )

        if texto is None:
            imprimir_error("No existe esa venta")
        else:
            print(texto)

        self.pausa()


# =====================================================================
# MENÚ ESPECIAL DE MATRÍCULAS
# =====================================================================
class MenuMatriculas(MenuCRUD):

    def __init__(self, controlador):
        super().__init__(controlador, "MATRÍCULAS")

        self._opciones["1"] = ("Registrar matrícula", self.crear)
        self._opciones["7"] = ("Agregar nota", self.agregar_nota)
        self._opciones["8"] = ("Ver boletín", self.ver_boletin)

    def crear(self):
        imprimir_titulo("REGISTRAR MATRÍCULA")

        estudiante_id = self.pedir_entero("Id del estudiante: ")

        if estudiante_id is None:
            imprimir_error("El id debe ser un número")
            return self.pausa()

        materia_id = self.pedir_entero("Id de la materia: ")

        if materia_id is None:
            imprimir_error("El id debe ser un número")
            return self.pausa()

        periodo = input(
            "Período académico (ej. 2026-1): "
        ).strip()

        datos = {
            "estudiante_id": estudiante_id,
            "materia_id": materia_id,
            "periodo": periodo
        }

        self.mostrar_resultado(
            *self._controlador.crear(datos)
        )

        self.pausa()

    def agregar_nota(self):
        imprimir_titulo("AGREGAR NOTA")

        matricula_id = self.pedir_entero("Id de la matrícula: ")

        if matricula_id is None:
            imprimir_error("El id debe ser un número")
            return self.pausa()

        imprimir_info("Tipos permitidos: deber, lección, examen")

        tipo = input("Tipo de nota: ").strip().lower()

        try:
            valor = float(input("Valor de la nota (0 a 20): "))

            peso_texto = input(
                "Peso (Enter para usar 1): "
            ).strip()

            peso = float(peso_texto) if peso_texto else 1

        except ValueError:
            imprimir_error("El valor y el peso deben ser numéricos")
            return self.pausa()

        self.mostrar_resultado(
            *self._controlador.agregar_nota(
                matricula_id, tipo, valor, peso
            )
        )

        self.pausa()

    def ver_boletin(self):
        imprimir_titulo("BOLETÍN ACADÉMICO")

        estudiante_id = self.pedir_entero("Id del estudiante: ")

        if estudiante_id is None:
            imprimir_error("El id debe ser un número")
            return self.pausa()

        texto = self._controlador.boletin(estudiante_id)

        if texto:
            print(texto)
        else:
            imprimir_info(
                "No hay información para generar el boletín."
            )

        self.pausa()


# =====================================================================
# MENÚ DEL SISTEMA DE VENTAS
# =====================================================================
class MenuVentasPrincipal:

    def __init__(self):
        clientes = ClienteController()
        productos = ProductoController()
        ventas = VentaController(clientes, productos)

        self._activo = True

        self._menus = {
            "1": MenuCRUD(clientes, "CLIENTES"),
            "2": MenuCRUD(productos, "PRODUCTOS"),
            "3": MenuVentas(ventas),
        }

    def ejecutar(self):
        self._activo = True

        while self._activo:
            imprimir_titulo("SISTEMA DE VENTAS")

            print("  1. Clientes")
            print("  2. Productos")
            print("  3. Ventas")
            print("  0. Volver al menú principal\n")

            tecla = input("Opción: ").strip()

            if tecla == "0":
                self._activo = False
                os.system("cls" if os.name == "nt" else "clear")

            elif tecla in self._menus:
                self._menus[tecla].ejecutar()

            else:
                imprimir_error("Opción no válida")
                MenuCRUD.pausa()


# =====================================================================
# MENÚ DEL SISTEMA ACADÉMICO
# =====================================================================
class MenuAcademico:

    def __init__(self):
        estudiantes = EstudianteController()
        docentes = DocenteController()
        materias = MateriaController(docentes)
        matriculas = MatriculaController(estudiantes, materias)

        self._activo = True

        self._menus = {
            "1": MenuCRUD(estudiantes, "ESTUDIANTES"),
            "2": MenuCRUD(docentes, "DOCENTES"),
            "3": MenuCRUD(materias, "MATERIAS"),
            "4": MenuMatriculas(matriculas),
        }

        self._materias = materias
        self._matriculas = matriculas

    def reporte_promedio_por_materia(self):
        imprimir_titulo("PROMEDIO GENERAL POR MATERIA")

        materias = self._materias.listar()
        matriculas = self._matriculas.listar()

        if not materias:
            imprimir_info("No hay materias registradas.")
            return MenuCRUD.pausa()

        for materia in materias:
            promedios = []

            for matricula in matriculas:
                if (
                    matricula.materia_id == materia.id
                    and matricula.notas
                ):
                    promedios.append(matricula.promedio)

            print(f"\nMateria: {materia.nombre}")

            if promedios:
                promedio_general = sum(promedios) / len(promedios)
                print(f"  Promedio general: {promedio_general:.2f}/20")
            else:
                print("  Todavía no hay notas registradas.")

        MenuCRUD.pausa()

    def ejecutar(self):
        self._activo = True

        while self._activo:
            imprimir_titulo("SISTEMA ACADÉMICO")

            print("  1. Estudiantes")
            print("  2. Docentes")
            print("  3. Materias")
            print("  4. Matrículas")
            print("  5. Reporte de promedio por materia")
            print("  0. Volver al menú principal\n")

            tecla = input("Opción: ").strip()

            if tecla == "0":
                self._activo = False
                os.system("cls" if os.name == "nt" else "clear")

            elif tecla in self._menus:
                self._menus[tecla].ejecutar()

            elif tecla == "5":
                self.reporte_promedio_por_materia()

            else:
                imprimir_error("Opción no válida")
                MenuCRUD.pausa()


# =====================================================================
# MENÚ PRINCIPAL: AMBOS SISTEMAS
# =====================================================================
class MenuPrincipal:

    def __init__(self):
        self._activo = True
        self._ventas = MenuVentasPrincipal()
        self._academico = MenuAcademico()

    def ejecutar(self):
        while self._activo:
            imprimir_titulo("SISTEMA GENERAL")

            print("  1. Sistema de Ventas")
            print("  2. Sistema Académico")
            print("  0. Salir\n")

            tecla = input("Opción: ").strip()

            if tecla == "1":
                self._ventas.ejecutar()

            elif tecla == "2":
                self._academico.ejecutar()

            elif tecla == "0":
                imprimir_info("¡Hasta luego!")
                self._activo = False

            else:
                imprimir_error("Opción no válida")
                MenuCRUD.pausa()


# =====================================================================
# EJECUCIÓN DEL PROGRAMA
# =====================================================================
if __name__ == "__main__":
    try:
        MenuPrincipal().ejecutar()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
