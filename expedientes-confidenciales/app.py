import json
import os
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

from flask import Flask, flash, redirect, render_template, request, url_for

from algoritmos.busqueda import busqueda_binaria, busqueda_secuencial
from algoritmos.cesar import cifrar, descifrar
from algoritmos.ordenamiento import burbuja, seleccion

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-local-desarrollo")

CARPETA_STATIC = Path(__file__).parent / "static"


@app.context_processor
def version_static():
    """Agrega ?v=<fecha de modificación> a CSS y JS para que el navegador no use copias viejas."""
    def estatico(nombre):
        try:
            version = int((CARPETA_STATIC / nombre).stat().st_mtime)
        except OSError:
            version = 0
        return url_for("static", filename=nombre, v=version)
    return {"estatico": estatico}


@app.route("/salud")
def salud():
    return {"estado": "ok"}

ARCHIVO_JSON = Path(
    os.environ.get(
        "EXPEDIENTES_JSON",
        Path(__file__).parent / "data" / "expedientes.json",
    )
)

CAMPOS = ["codigo", "nombre", "apellido", "fecha", "descripcion", "desplazamiento"]
CAMPOS_ORDENABLES = ["codigo", "nombre"]
DESPLAZAMIENTO_DEFECTO = 3

ALGORITMOS_ORDEN = {
    "burbuja": ("Burbuja", burbuja),
    "seleccion": ("Selección", seleccion),
}
ALGORITMOS_BUSQUEDA = {
    "secuencial": "Secuencial",
    "binaria": "Binaria",
}


# ==========================================
# ALMACENAMIENTO JSON
# ==========================================

def cargar_expedientes():
    """Lee el JSON, valida su estructura y migra registros antiguos."""
    ARCHIVO_JSON.parent.mkdir(parents=True, exist_ok=True)

    if not ARCHIVO_JSON.exists():
        ARCHIVO_JSON.write_text("[]", encoding="utf-8")

    try:
        datos = json.loads(ARCHIVO_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            "El archivo expedientes.json está vacío o tiene formato inválido."
        ) from error

    if not isinstance(datos, list):
        raise ValueError("El archivo expedientes.json debe contener una lista.")

    migrado = False

    for expediente in datos:
        if not isinstance(expediente, dict):
            raise ValueError("Hay registros inválidos en expedientes.json.")

        # Registros creados antes de guardar el desplazamiento: se cifran con 3.
        if "desplazamiento" not in expediente and "descripcion" in expediente:
            expediente["descripcion"] = cifrar(
                str(expediente["descripcion"]), DESPLAZAMIENTO_DEFECTO
            )
            expediente["desplazamiento"] = DESPLAZAMIENTO_DEFECTO
            migrado = True

        if any(campo not in expediente for campo in CAMPOS):
            raise ValueError("Un expediente tiene campos incompletos.")

        try:
            expediente["desplazamiento"] = int(expediente["desplazamiento"])
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"El expediente {expediente['codigo']} tiene un desplazamiento inválido."
            ) from error

    if migrado:
        guardar_expedientes(datos)

    return datos


def guardar_expedientes(expedientes):
    """Escribe a un archivo temporal y lo reemplaza, para no dejar el JSON a medias."""
    ARCHIVO_JSON.parent.mkdir(parents=True, exist_ok=True)

    temporal = ARCHIVO_JSON.with_suffix(".tmp")
    temporal.write_text(
        json.dumps(expedientes, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    temporal.replace(ARCHIVO_JSON)


def preparar_expediente(expediente):
    copia = expediente.copy()
    copia["descripcion_visible"] = descifrar(
        copia["descripcion"], int(copia["desplazamiento"])
    )
    return copia


def leer_formulario():
    """Devuelve (datos, error). Valida campos obligatorios, fecha y desplazamiento."""
    datos = {
        campo: request.form.get(campo, "").strip()
        for campo in ["codigo", "nombre", "apellido", "fecha", "descripcion"]
    }

    if not all(datos.values()):
        return datos, "Todos los campos son obligatorios."

    if "/" in datos["codigo"]:
        return datos, "El código no puede contener el carácter «/»."

    try:
        date.fromisoformat(datos["fecha"])
    except ValueError:
        return datos, "La fecha no es válida."

    try:
        desplazamiento = int(request.form.get("desplazamiento", DESPLAZAMIENTO_DEFECTO))
    except ValueError:
        return datos, "El desplazamiento debe ser un número entero."

    if not 0 <= desplazamiento <= 25:
        return datos, "El desplazamiento debe estar entre 0 y 25."

    datos["desplazamiento"] = desplazamiento
    return datos, None


def buscar_por_codigo(expedientes, codigo):
    for expediente in expedientes:
        if expediente["codigo"].casefold() == codigo.casefold():
            return expediente
    return None


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

PARAMETROS_VISTA = ["ordenar", "campo_orden", "buscar", "metodo", "campo_busqueda"]


def parametros_vista(origen):
    """Conserva solo los parámetros de orden y búsqueda (para volver a la misma vista)."""
    return {k: origen[k] for k in PARAMETROS_VISTA if origen.get(k)}


def parametros_desde_volver():
    return parametros_vista(dict(parse_qsl(request.form.get("volver", ""))))


def pagina_inicio(args, editar=None, borrador=None, error_edicion=None, estado=200, eliminar=None):
    ordenar = args.get("ordenar", "")
    campo_orden = args.get("campo_orden", "codigo")
    buscar = args.get("buscar", "").strip()
    metodo = args.get("metodo", "secuencial")
    campo_busqueda = args.get("campo_busqueda", "codigo")

    if ordenar not in ALGORITMOS_ORDEN:
        ordenar = ""
    if campo_orden not in CAMPOS_ORDENABLES:
        campo_orden = "codigo"
    if metodo not in ALGORITMOS_BUSQUEDA:
        metodo = "secuencial"
    if campo_busqueda not in CAMPOS_ORDENABLES:
        campo_busqueda = "codigo"

    vista = parametros_vista(args)

    contexto = {
        "expedientes": [],
        "error_archivo": None,
        "comparaciones": None,
        "resultado": None,
        "comparaciones_busqueda": None,
        "error_busqueda": None,
        "ordenar": ordenar,
        "campo_orden": campo_orden,
        "buscar": buscar,
        "metodo": metodo,
        "campo_busqueda": campo_busqueda,
        "nombres_orden": {k: v[0] for k, v in ALGORITMOS_ORDEN.items()},
        "nombres_busqueda": ALGORITMOS_BUSQUEDA,
        "hoy": date.today().isoformat(),
        "editar": (editar or "").casefold(),
        "eliminar": (eliminar or "").casefold(),
        "borrador": borrador,
        "error_edicion": error_edicion,
        "vista": vista,
        "volver": urlencode(vista),
    }

    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        contexto["error_archivo"] = str(error)
        return render_template("index.html", **contexto), estado

    if ordenar:
        _, algoritmo = ALGORITMOS_ORDEN[ordenar]
        expedientes, contexto["comparaciones"] = algoritmo(expedientes, campo_orden)

    if buscar:
        resultado = None

        if metodo == "binaria":
            if not ordenar:
                contexto["error_busqueda"] = (
                    "Primero ordena los expedientes para usar la búsqueda binaria."
                )
            elif campo_orden != campo_busqueda:
                contexto["error_busqueda"] = (
                    "Ordena por el mismo campo que quieres buscar "
                    "para usar la búsqueda binaria."
                )
            else:
                resultado, contexto["comparaciones_busqueda"] = busqueda_binaria(
                    expedientes, campo_busqueda, buscar
                )
        else:
            # Recorre la lista en el mismo orden en que se muestra.
            resultado, contexto["comparaciones_busqueda"] = busqueda_secuencial(
                expedientes, campo_busqueda, buscar
            )

        if resultado:
            contexto["resultado"] = preparar_expediente(resultado)

    contexto["expedientes"] = [preparar_expediente(e) for e in expedientes]
    return render_template("index.html", **contexto), estado


@app.route("/")
def inicio():
    return pagina_inicio(
        request.args,
        editar=request.args.get("editar"),
        eliminar=request.args.get("eliminar"),
    )


# ==========================================
# CREAR EXPEDIENTE
# ==========================================

@app.route("/crear", methods=["POST"])
def crear():
    datos, error = leer_formulario()
    if error:
        flash(error, "error")
        return redirect(url_for("inicio"))

    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    if buscar_por_codigo(expedientes, datos["codigo"]):
        flash(f"El código {datos['codigo']} ya existe.", "error")
        return redirect(url_for("inicio"))

    datos["descripcion"] = cifrar(datos["descripcion"], datos["desplazamiento"])
    expedientes.append(datos)
    guardar_expedientes(expedientes)

    flash(f"Expediente {datos['codigo']} registrado.", "exito")
    return redirect(url_for("inicio"))


# ==========================================
# EDITAR EXPEDIENTE (dentro de la tabla)
# ==========================================

@app.route("/editar/<path:codigo>", methods=["GET", "POST"])
def editar(codigo):
    if request.method == "GET":
        # La edición vive en la tabla; esta ruta solo abre la fila.
        return redirect(url_for("inicio", editar=codigo, _anchor="editando"))

    vista = parametros_desde_volver()

    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio", **vista))

    expediente = buscar_por_codigo(expedientes, codigo)

    if expediente is None:
        flash("Expediente no encontrado.", "error")
        return redirect(url_for("inicio", **vista))

    datos, error = leer_formulario()

    if not error:
        otro = buscar_por_codigo(expedientes, datos["codigo"])
        if otro is not None and otro is not expediente:
            error = f"El código {datos['codigo']} ya está registrado."

    if error:
        # Vuelve a mostrar la fila abierta con lo que escribió el usuario.
        borrador = dict(datos)
        borrador["descripcion_visible"] = datos["descripcion"]
        borrador.setdefault("desplazamiento", request.form.get("desplazamiento", ""))
        return pagina_inicio(
            vista, editar=codigo, borrador=borrador,
            error_edicion=error, estado=422,
        )

    datos["descripcion"] = cifrar(datos["descripcion"], datos["desplazamiento"])
    expediente.update(datos)
    guardar_expedientes(expedientes)

    flash(f"Expediente {datos['codigo']} actualizado.", "exito")
    return redirect(url_for("inicio", **vista))


# ==========================================
# ELIMINAR EXPEDIENTE
# ==========================================

@app.route("/eliminar/<path:codigo>", methods=["POST"])
def eliminar(codigo):
    vista = parametros_desde_volver()

    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio", **vista))

    expediente = buscar_por_codigo(expedientes, codigo)

    if expediente is None:
        flash("No se encontró el expediente.", "error")
    else:
        expedientes.remove(expediente)
        guardar_expedientes(expedientes)
        flash(f"Expediente {expediente['codigo']} eliminado.", "exito")

    return redirect(url_for("inicio", **vista))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
