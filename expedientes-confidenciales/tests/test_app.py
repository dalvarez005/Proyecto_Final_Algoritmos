import json

import pytest

import app as modulo


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    archivo = tmp_path / "expedientes.json"
    monkeypatch.setattr(modulo, "ARCHIVO_JSON", archivo)
    modulo.app.config["TESTING"] = True
    with modulo.app.test_client() as c:
        c.archivo = archivo
        yield c


def crear(cliente, codigo="EXP-001", nombre="Ana", descripcion="Hola", desplazamiento=3):
    return cliente.post("/crear", data={
        "codigo": codigo, "nombre": nombre, "apellido": "Pérez",
        "fecha": "2026-11-03", "descripcion": descripcion,
        "desplazamiento": desplazamiento,
    }, follow_redirects=True)


def leer(cliente):
    return json.loads(cliente.archivo.read_text(encoding="utf-8"))


def test_inicio_vacio(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "El archivo está vacío" in r.get_data(as_text=True)


def test_crear_guarda_cifrado(cliente):
    r = crear(cliente)
    assert r.status_code == 200
    assert "registrado" in r.get_data(as_text=True)
    [exp] = leer(cliente)
    assert exp["descripcion"] == "Krod"
    assert exp["desplazamiento"] == 3


def test_crear_rechaza_duplicado_y_datos_invalidos(cliente):
    crear(cliente)
    assert "ya existe" in crear(cliente, codigo="exp-001").get_data(as_text=True)
    assert "entre 0 y 25" in crear(cliente, codigo="X", desplazamiento=30).get_data(as_text=True)
    assert "obligatorios" in crear(cliente, codigo="").get_data(as_text=True)
    assert "«/»" in crear(cliente, codigo="A/B").get_data(as_text=True)
    assert len(leer(cliente)) == 1


def test_editar_y_eliminar(cliente):
    crear(cliente)
    r = cliente.get("/editar/EXP-001")
    assert r.status_code == 302
    assert "editar=EXP-001" in r.headers["Location"]

    html = cliente.get("/?editar=EXP-001").get_data(as_text=True)
    assert 'id="editando"' in html
    assert "confirm(" not in html

    html = cliente.get("/?eliminar=EXP-001").get_data(as_text=True)
    assert 'id="eliminando"' in html and "Sí, eliminar" in html

    cliente.post("/editar/EXP-001", data={
        "codigo": "EXP-010", "nombre": "Ana", "apellido": "Pérez",
        "fecha": "2026-11-04", "descripcion": "abc", "desplazamiento": 1,
    })
    [exp] = leer(cliente)
    assert exp["codigo"] == "EXP-010"
    assert exp["descripcion"] == "bcd"

    cliente.post("/eliminar/EXP-010")
    assert leer(cliente) == []


def test_ordenar_y_buscar(cliente):
    for codigo, nombre in [("C", "Zoe"), ("A", "Luis"), ("B", "Ana")]:
        crear(cliente, codigo=codigo, nombre=nombre)

    html = cliente.get("/?ordenar=burbuja&campo_orden=codigo").get_data(as_text=True)
    assert html.index(">A<") < html.index(">B<") < html.index(">C<")

    html = cliente.get(
        "/?ordenar=seleccion&campo_orden=nombre&buscar=luis&metodo=binaria&campo_busqueda=nombre"
    ).get_data(as_text=True)
    assert 'id="encontrado"' in html

    html = cliente.get("/?buscar=A&metodo=binaria").get_data(as_text=True)
    assert "Primero ordena" in html


def test_json_corrupto_y_migracion(cliente):
    cliente.archivo.write_text("{malo", encoding="utf-8")
    assert "formato inválido" in cliente.get("/").get_data(as_text=True)

    cliente.archivo.write_text(json.dumps([{
        "codigo": "V1", "nombre": "a", "apellido": "b",
        "fecha": "2026-01-01", "descripcion": "abc",
    }]), encoding="utf-8")
    assert cliente.get("/").status_code == 200
    [exp] = leer(cliente)
    assert exp["desplazamiento"] == 3 and exp["descripcion"] == "def"


def test_editar_con_error_conserva_lo_escrito(cliente):
    crear(cliente)
    crear(cliente, codigo="EXP-002")
    r = cliente.post("/editar/EXP-001", data={
        "codigo": "EXP-002", "nombre": "Nuevo nombre", "apellido": "Pérez",
        "fecha": "2026-11-04", "descripcion": "texto nuevo", "desplazamiento": 4,
        "volver": "ordenar=burbuja&campo_orden=nombre&malo=1",
    })
    html = r.get_data(as_text=True)
    assert r.status_code == 422
    assert "ya está registrado" in html
    assert 'value="Nuevo nombre"' in html
    assert "texto nuevo" in html
    assert leer(cliente)[0]["nombre"] == "Ana"


def test_eliminar_vuelve_a_la_misma_vista(cliente):
    crear(cliente)
    r = cliente.post("/eliminar/EXP-001", data={"volver": "ordenar=seleccion&campo_orden=nombre&x=1"})
    assert r.status_code == 302
    assert r.headers["Location"] == "/?ordenar=seleccion&campo_orden=nombre"
    assert leer(cliente) == []


def test_archivo_vacio_muestra_error(cliente):
    cliente.archivo.write_text("", encoding="utf-8")
    html = cliente.get("/").get_data(as_text=True)
    assert "vacío o tiene formato inválido" in html


def test_los_datos_persisten_tras_reiniciar(cliente):
    crear(cliente, codigo="EXP-050", descripcion="HOLA", desplazamiento=3)
    # Simula reiniciar: se vuelve a leer el archivo desde cero.
    [exp] = modulo.cargar_expedientes()
    assert exp["codigo"] == "EXP-050"
    assert exp["descripcion"] == "KROD"


def test_json_de_ejemplo_es_valido(tmp_path, monkeypatch):
    from pathlib import Path
    ejemplo = Path(modulo.__file__).parent / "data" / "expedientes_ejemplo.json"
    destino = tmp_path / "e.json"
    destino.write_text(ejemplo.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(modulo, "ARCHIVO_JSON", destino)
    datos = modulo.cargar_expedientes()
    assert len(datos) == 10
    assert len({d["codigo"] for d in datos}) == 10
