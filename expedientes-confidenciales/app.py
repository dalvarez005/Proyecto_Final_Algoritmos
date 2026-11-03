
from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import json

from algoritmos.ordenamiento import burbuja, seleccion
from algoritmos.busqueda import busqueda_secuencial, busqueda_binaria
from algoritmos.cesar import cifrar, descifrar

app = Flask(__name__)
app.secret_key = "clave-local-desarrollo"

ARCHIVO_JSON = Path(__file__).parent / "data" / "expedientes.json"


# ==========================================
# ALMACENAMIENTO JSON---
# ==========================================

def cargar_expedientes():
    ARCHIVO_JSON.parent.mkdir(parents=True, exist_ok=True)

    if not ARCHIVO_JSON.exists():
        ARCHIVO_JSON.write_text("[]", encoding="utf-8")

    try:
        contenido = ARCHIVO_JSON.read_text(encoding="utf-8")
        datos = json.loads(contenido)

        if not isinstance(datos, list):
            raise ValueError("El JSON debe contener una lista.")

        for expediente in datos:
            if not isinstance(expediente, dict):
                raise ValueError("Hay registros inválidos en el JSON.")

            campos = [
                "codigo", "nombre", "apellido",
                "fecha", "descripcion", "desplazamiento"
            ]

            if any(campo not in expediente for campo in campos):
                raise ValueError("Un expediente tiene campos incompletos.")

        return datos

    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            "El archivo expedientes.json está vacío o tiene formato inválido."
        ) from error


def guardar_expedientes(expedientes):
    ARCHIVO_JSON.parent.mkdir(parents=True, exist_ok=True)

    temporal = ARCHIVO_JSON.with_suffix(".tmp")

    temporal.write_text(
        json.dumps(expedientes, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    temporal.replace(ARCHIVO_JSON)


def preparar_expediente(expediente):
    copia = expediente.copy()

    copia["descripcion_visible"] = descifrar(
        copia["descripcion"],
        int(copia["desplazamiento"])
    )

    return copia


# ==========================================
# PÁGINA PRINCIPAL---
# ==========================================

@app.route("/")
def inicio():
    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        return render_template(
            "index.html",
            expedientes=[],
            error_archivo=str(error),
            comparaciones=None,
            resultado=None,
            ordenar="",
            campo_orden="codigo",
            buscar="",
            metodo="secuencial",
            campo_busqueda="codigo"
        )

    ordenar = request.args.get("ordenar", "")
    campo_orden = request.args.get("campo_orden", "codigo")

    comparaciones = None

    if campo_orden not in ["codigo", "nombre"]:
        campo_orden = "codigo"

    if ordenar == "burbuja":
        expedientes, comparaciones = burbuja(
            expedientes, campo_orden
        )

    elif ordenar == "seleccion":
        expedientes, comparaciones = seleccion(
            expedientes, campo_orden
        )

    buscar = request.args.get("buscar", "").strip()
    metodo = request.args.get("metodo", "secuencial")
    campo_busqueda = request.args.get("campo_busqueda", "codigo")

    resultado = None
    comparaciones_busqueda = None
    error_busqueda = None

    if campo_busqueda not in ["codigo", "nombre"]:
        campo_busqueda = "codigo"

    if buscar:
        if metodo == "binaria":

            if ordenar not in ["burbuja", "seleccion"]:
                error_busqueda = (
                    "Primero debes ordenar los expedientes "
                    "para utilizar la búsqueda binaria."
                )

            elif campo_orden != campo_busqueda:
                error_busqueda = (
                    "Debes ordenar por el mismo campo que deseas buscar."
                )

            else:
                resultado, comparaciones_busqueda = busqueda_binaria(
                    expedientes, campo_busqueda, buscar
                )

        else:
            resultado, comparaciones_busqueda = busqueda_secuencial(
                cargar_expedientes(), campo_busqueda, buscar
            )

    expedientes_visibles = [
        preparar_expediente(e) for e in expedientes
    ]

    resultado_visible = (
        preparar_expediente(resultado) if resultado else None
    )

    return render_template(
        "index.html",
        expedientes=expedientes_visibles,
        error_archivo=None,
        comparaciones=comparaciones,
        resultado=resultado_visible,
        comparaciones_busqueda=comparaciones_busqueda,
        error_busqueda=error_busqueda,
        ordenar=ordenar,
        campo_orden=campo_orden,
        buscar=buscar,
        metodo=metodo,
        campo_busqueda=campo_busqueda
    )


# ==========================================
# CREAR EXPEDIENTE----
# ==========================================

@app.route("/crear", methods=["POST"])
def crear():
    codigo = request.form.get("codigo", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    fecha = request.form.get("fecha", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    try:
        desplazamiento = int(request.form.get("desplazamiento", "3"))
    except ValueError:
        flash("El desplazamiento debe ser un número entero.", "error")
        return redirect(url_for("inicio"))

    if not all([codigo, nombre, apellido, fecha, descripcion]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for("inicio"))

    if not 0 <= desplazamiento <= 25:
        flash("El desplazamiento debe estar entre 0 y 25.", "error")
        return redirect(url_for("inicio"))

    try:
        migrado = False

        for expediente in datos:
            if not isinstance(expediente, dict):
                raise ValueError("Hay registros inválidos en el JSON.")

            campos = [
                "codigo", "nombre", "apellido",
                "fecha", "descripcion"
            ]

            if any(campo not in expediente for campo in campos):
                raise ValueError("Un expediente tiene campos incompletos.")

            if "desplazamiento" not in expediente:
                expediente["descripcion"] = cifrar(
                    expediente["descripcion"], 3
                )
                expediente["desplazamiento"] = 3
                migrado = True

        if migrado:
            guardar_expedientes(datos)

    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    for expediente in expedientes:
        if expediente["codigo"].casefold() == codigo.casefold():
            flash("El código ya existe.", "error")
            return redirect(url_for("inicio"))

    nuevo = {
        "codigo": codigo,
        "nombre": nombre,
        "apellido": apellido,
        "fecha": fecha,
        "descripcion": cifrar(descripcion, desplazamiento),
        "desplazamiento": desplazamiento
    }

    expedientes.append(nuevo)
    guardar_expedientes(expedientes)

    flash("Expediente registrado correctamente.", "exito")
    return redirect(url_for("inicio"))


# ==========================================
# EDITAR EXPEDIENTE
# ==========================================

@app.route("/editar/<codigo>", methods=["GET", "POST"])
def editar(codigo):
    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    expediente = None

    for registro in expedientes:
        if registro["codigo"].casefold() == codigo.casefold():
            expediente = registro
            break

    if expediente is None:
        flash("Expediente no encontrado.", "error")
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nuevo_codigo = request.form.get("codigo", "").strip()
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        fecha = request.form.get("fecha", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        try:
            desplazamiento = int(
                request.form.get("desplazamiento", "3")
            )
        except ValueError:
            flash("El desplazamiento debe ser un número entero.", "error")
            return redirect(url_for("editar", codigo=codigo))

        if not all([
            nuevo_codigo, nombre, apellido, fecha, descripcion
        ]):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("editar", codigo=codigo))

        if not 0 <= desplazamiento <= 25:
            flash("El desplazamiento debe estar entre 0 y 25.", "error")
            return redirect(url_for("editar", codigo=codigo))

        for registro in expedientes:
            if (
                registro["codigo"].casefold() == nuevo_codigo.casefold()
                and registro is not expediente
            ):
                flash("El nuevo código ya está registrado.", "error")
                return redirect(url_for("editar", codigo=codigo))

        expediente.update({
            "codigo": nuevo_codigo,
            "nombre": nombre,
            "apellido": apellido,
            "fecha": fecha,
            "descripcion": cifrar(descripcion, desplazamiento),
            "desplazamiento": desplazamiento
        })

        guardar_expedientes(expedientes)

        flash("Expediente actualizado correctamente.", "exito")
        return redirect(url_for("inicio"))

    expediente_visible = preparar_expediente(expediente)

    return render_template(
        "editar.html",
        expediente=expediente_visible
    )


# ==========================================
# ELIMINAR EXPEDIENTE
# ==========================================

@app.route("/eliminar/<codigo>", methods=["POST"])
def eliminar(codigo):
    try:
        expedientes = cargar_expedientes()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("inicio"))

    nuevos = []
    encontrado = False

    for expediente in expedientes:
        if expediente["codigo"].casefold() == codigo.casefold():
            encontrado = True
        else:
            nuevos.append(expediente)

    if encontrado:
        guardar_expedientes(nuevos)
        flash("Expediente eliminado correctamente.", "exito")
    else:
        flash("No se encontró el expediente.", "error")

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)

