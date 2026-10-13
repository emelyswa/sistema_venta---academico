
"""Controladores del sistema académico."""

from views import CrudBase
from models_academico import (
    Estudiante,
    Docente,
    Materia,
    Matricula,
)


# =========================================================
# CONTROLADOR DE ESTUDIANTES
# =========================================================
class EstudianteController(CrudBase):
    MODELO = Estudiante
    ARCHIVO = "data/estudiantes.json"
    NOMBRE = "estudiante"
    CAMPOS_BUSCABLES = (
        "nombre", "apellido", "email", "carnet"
    )

    def validar(self, datos, id_actual=None):
        carnet = str(datos.get("carnet", "")).strip().upper()

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

        if carnet:
            usados = {
                str(registro.get("carnet", "")).strip().upper()
                for registro in self.registros()
                if registro["id"] != id_actual
            }
            if carnet in usados:
                return "Ese carnet ya está registrado"

        return None


# =========================================================
# CONTROLADOR DE DOCENTES
# =========================================================
class DocenteController(CrudBase):
    MODELO = Docente
    ARCHIVO = "data/docentes.json"
    NOMBRE = "docente"
    CAMPOS_BUSCABLES = (
        "nombre", "apellido", "email",
        "titulo", "especialidad"
    )

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

        email = str(datos.get("email", "")).strip().lower()

        if email:
            usados = {
                str(registro.get("email", "")).strip().lower()
                for registro in self.registros()
                if registro["id"] != id_actual
            }
            if email in usados:
                return "Ese email ya está registrado para otro docente"

        return None


# =========================================================
# CONTROLADOR DE MATERIAS
# =========================================================
class MateriaController(CrudBase):
    MODELO = Materia
    ARCHIVO = "data/materias.json"
    NOMBRE = "materia"
    CAMPOS_BUSCABLES = ("nombre", "codigo")

    def __init__(self, docentes=None):
        super().__init__()
        self.docentes = docentes or DocenteController()

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

        codigo = str(datos.get("codigo", "")).strip().upper()

        if codigo:
            usados = {
                str(registro.get("codigo", "")).strip().upper()
                for registro in self.registros()
                if registro["id"] != id_actual
            }
            if codigo in usados:
                return "Ese código de materia ya está registrado"

        if "creditos" in datos:
            try:
                creditos = int(datos["creditos"])
            except (TypeError, ValueError):
                return "Los créditos deben ser un número entero"

            if not 0 <= creditos <= 10:
                return "Los créditos deben estar entre 0 y 10"

        docente_id = datos.get("docente_id")

        if docente_id not in (None, "", 0, "0"):
            try:
                docente_id = int(docente_id)
            except (TypeError, ValueError):
                return "El ID del docente debe ser un número"

            if not self.docentes.existe(docente_id):
                return f"No existe un docente con id {docente_id}"

        return None


# =========================================================
# CONTROLADOR DE MATRÍCULAS
# =========================================================
class MatriculaController(CrudBase):
    MODELO = Matricula
    ARCHIVO = "data/matriculas.json"
    NOMBRE = "matrícula"
    CAMPOS_BUSCABLES = ("periodo",)

    def __init__(
        self,
        estudiantes=None,
        materias=None
    ):
        super().__init__()
        self.estudiantes = estudiantes or EstudianteController()
        self.materias = materias or MateriaController()

    def validar(self, datos, id_actual=None):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
        except (TypeError, ValueError):
            return "El ID del estudiante debe ser un número"

        try:
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "El ID de la materia debe ser un número"

        if not self.estudiantes.existe(estudiante_id):
            return f"No existe un estudiante con id {estudiante_id}"

        if not self.materias.existe(materia_id):
            return f"No existe una materia con id {materia_id}"

        periodo = str(datos.get("periodo", "")).strip()

        if not periodo:
            return "El periodo académico es obligatorio"

        for registro in self.registros():
            if registro["id"] == id_actual:
                continue

            misma_matricula = (
                int(registro.get("estudiante_id", 0)) == estudiante_id
                and int(registro.get("materia_id", 0)) == materia_id
                and str(registro.get("periodo", "")).strip() == periodo
            )

            if misma_matricula:
                return (
                    "El estudiante ya está matriculado en esa "
                    "materia durante ese periodo"
                )

        return None

    def crear(self, datos):
        """Registra la matrícula sin notas iniciales."""
        error = self.validar(datos)

        if error:
            return False, error

        try:
            matricula = Matricula(
                self.siguiente_id(),
                datos["estudiante_id"],
                datos["materia_id"],
                datos.get("periodo", "2026-1")
            )
        except (ValueError, TypeError) as excepcion:
            return False, str(excepcion)

        registros = self.registros()
        registros.append(matricula.a_diccionario())
        self._gestor.guardar(registros)

        return True, f"Matrícula {matricula.id} registrada correctamente"

    def agregar_nota(self, matricula_id, tipo, valor, peso=1):
        """Agrega una nota y guarda la matrícula completa."""
        matricula = self.obtener(matricula_id)

        if matricula is None:
            return False, f"No existe una matrícula con id {matricula_id}"

        try:
            matricula.agregar_nota(tipo, valor, peso)
        except (ValueError, TypeError) as excepcion:
            return False, str(excepcion)

        registros = self.registros()

        for indice, registro in enumerate(registros):
            if registro["id"] == matricula_id:
                registros[indice] = matricula.a_diccionario()
                self._gestor.guardar(registros)
                return True, (
                    f"Nota agregada correctamente. "
                    f"Promedio actual: {matricula.promedio:.2f}"
                )

        return False, "No se pudo guardar la matrícula"

    def boletin(self, estudiante_id):
        """Genera el boletín con las materias y promedios del estudiante."""
        estudiante = self.estudiantes.obtener(estudiante_id)

        if estudiante is None:
            return f"No existe un estudiante con id {estudiante_id}"

        matriculas = [
            matricula for matricula in self.listar()
            if matricula.estudiante_id == estudiante_id
        ]

        if not matriculas:
            return (
                f"BOLETÍN ACADÉMICO\n"
                f"Estudiante: {estudiante.nombre_completo}\n"
                "El estudiante no tiene matrículas registradas."
            )

        lineas = [
            "BOLETÍN ACADÉMICO",
            f"Estudiante: {estudiante.nombre_completo}",
            f"Carnet: {estudiante.carnet}",
            "-" * 45
        ]

        promedios = []

        for matricula in matriculas:
            materia = self.materias.obtener(matricula.materia_id)

            nombre_materia = (
                materia.nombre if materia is not None
                else f"Materia ID {matricula.materia_id}"
            )

            if matricula.notas:
                promedio = matricula.promedio
                estado = matricula.estado
                promedios.append(promedio)
                promedio_texto = f"{promedio:.2f}"
            else:
                estado = "Sin notas"
                promedio_texto = "Pendiente"

            lineas.append(
                f"Materia: {nombre_materia}\n"
                f"Periodo: {matricula.periodo}\n"
                f"Promedio: {promedio_texto}\n"
                f"Estado: {estado}\n"
                + "-" * 45
            )

        if promedios:
            promedio_general = sum(promedios) / len(promedios)
            lineas.append(
                f"Promedio general: {promedio_general:.2f}"
            )
        else:
            lineas.append("Promedio general: Pendiente")

        return "\n".join(lineas)
