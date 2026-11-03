
def busqueda_secuencial(expedientes, campo, valor):
    comparaciones = 0
    valor = str(valor).casefold()

    for expediente in expedientes:
        comparaciones += 1

        if str(expediente[campo]).casefold() == valor:
            return expediente, comparaciones

    return None, comparaciones


def busqueda_binaria(expedientes, campo, valor):
    izquierda = 0
    derecha = len(expedientes) - 1
    comparaciones = 0
    valor = str(valor).casefold()

    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2

        comparaciones += 1
        actual = str(expedientes[medio][campo]).casefold()

        if actual == valor:
            return expedientes[medio], comparaciones

        if actual < valor:
            izquierda = medio + 1
        else:
            derecha = medio - 1

    return None, comparaciones
