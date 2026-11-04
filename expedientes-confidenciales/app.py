import json
import os
from datetime import date
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from algoritmos.busqueda import busqueda_binaria, busqueda_secuencial
from algoritmos.cesar import cifrar, descifrar
from algoritmos.ordenamiento import burbuja, seleccion

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-local-desarrollo")

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

@app.route("/")
def inicio():
    ordenar = request.args.get("ordenar", "")
    campo_orden = request.args.get("campo_orden", "codigo")
    buscar = request.args.get("buscar", "").strip()
    metodo = request.args.get("metodo", "secuencial")
    campo_busqueda = request.args.get("campo_busqueda", "codigo")

    if ordenar not in ALGORITMOS_ORDEN:
        ordenar = ""
    if campo_orden not in CAMPOS_ORDENABLES:
        campo_orden = "codigo"
    if metodo not in ALGORITMOS_BUSQUEDA:
        metodo = "secuencial"
    if campo_busqueda not in CAMPOS_ORDENABLES:
        campo_busqueda = "codigo"

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
    }

    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        contexto["error_archivo"] = str(error)
        return render_template("index.html", **contexto)

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
    return render_template("index.html", **contexto)


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
# EDITAR EXPEDIENTE
# ==========================================

@app.route("/editar/<path:codigo>", methods=["GET", "POST"])
def editar(codigo):
    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    expediente = buscar_por_codigo(expedientes, codigo)

    if expediente is None:
        flash("Expediente no encontrado.", "error")
        return redirect(url_for("inicio"))

    if request.method == "POST":
        datos, error = leer_formulario()
        if error:
            flash(error, "error")
            return redirect(url_for("editar", codigo=codigo))

        otro = buscar_por_codigo(expedientes, datos["codigo"])
        if otro is not None and otro is not expediente:
            flash(f"El código {datos['codigo']} ya está registrado.", "error")
            return redirect(url_for("editar", codigo=codigo))

        datos["descripcion"] = cifrar(datos["descripcion"], datos["desplazamiento"])
        expediente.update(datos)
        guardar_expedientes(expedientes)

        flash(f"Expediente {datos['codigo']} actualizado.", "exito")
        return redirect(url_for("inicio"))

    return render_template("editar.html", expediente=preparar_expediente(expediente))


# ==========================================
# ELIMINAR EXPEDIENTE
# ==========================================

@app.route("/eliminar/<path:codigo>", methods=["POST"])
def eliminar(codigo):
    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    expediente = buscar_por_codigo(expedientes, codigo)

    if expediente is None:
        flash("No se encontró el expediente.", "error")
    else:
        expedientes.remove(expediente)
        guardar_expedientes(expedientes)
        flash(f"Expediente {expediente['codigo']} eliminado.", "exito")

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
