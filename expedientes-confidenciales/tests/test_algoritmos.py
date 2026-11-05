from algoritmos.busqueda import busqueda_binaria, busqueda_secuencial
from algoritmos.cesar import cifrar, descifrar
from algoritmos.ordenamiento import burbuja, seleccion

DATOS = [
    {"codigo": "EXP-003", "nombre": "carla"},
    {"codigo": "EXP-001", "nombre": "Ana"},
    {"codigo": "EXP-002", "nombre": "beto"},
]


def test_cesar_ida_y_vuelta():
    texto = "Hola Mundo, año 2026!"
    assert cifrar(texto, 3) == "Krod Pxqgr, dñr 2026!"
    assert descifrar(cifrar(texto, 25), 25) == texto


def test_cesar_da_la_vuelta_al_alfabeto():
    assert cifrar("xyz XYZ", 3) == "abc ABC"
    assert cifrar("abc", 0) == "abc"


def test_ordenamientos_coinciden_y_no_mutan():
    original = [d.copy() for d in DATOS]
    for algoritmo in (burbuja, seleccion):
        ordenados, comparaciones = algoritmo(DATOS, "nombre")
        assert [d["nombre"] for d in ordenados] == ["Ana", "beto", "carla"]
        assert comparaciones == 3  # n(n-1)/2 con n = 3
    assert DATOS == original


def test_ordenar_listas_cortas():
    assert burbuja([], "codigo") == ([], 0)
    assert seleccion([{"codigo": "A"}], "codigo") == ([{"codigo": "A"}], 0)


def test_busqueda_secuencial():
    encontrado, comparaciones = busqueda_secuencial(DATOS, "codigo", "exp-002")
    assert encontrado["nombre"] == "beto"
    assert comparaciones == 3
    assert busqueda_secuencial(DATOS, "codigo", "nada") == (None, 3)


def test_busqueda_binaria():
    ordenados, _ = burbuja(DATOS, "codigo")
    encontrado, comparaciones = busqueda_binaria(ordenados, "codigo", "EXP-002")
    assert encontrado["nombre"] == "beto"
    assert comparaciones == 1
    assert busqueda_binaria(ordenados, "codigo", "EXP-999")[0] is None
    assert busqueda_binaria([], "codigo", "x") == (None, 0)
