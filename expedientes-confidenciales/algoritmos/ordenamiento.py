
def burbuja(expedientes, campo):
    datos = expedientes.copy()
    comparaciones = 0
    n = len(datos)

    for i in range(n - 1):
        for j in range(n - i - 1):
            comparaciones += 1

            valor1 = str(datos[j][campo]).casefold()
            valor2 = str(datos[j + 1][campo]).casefold()

            if valor1 > valor2:
                datos[j], datos[j + 1] = datos[j + 1], datos[j]

    return datos, comparaciones


def seleccion(expedientes, campo):
    datos = expedientes.copy()
    comparaciones = 0
    n = len(datos)

    for i in range(n - 1):
        minimo = i

        for j in range(i + 1, n):
            comparaciones += 1

            valor1 = str(datos[j][campo]).casefold()
            valor2 = str(datos[minimo][campo]).casefold()

            if valor1 < valor2:
                minimo = j

        if minimo != i:
            datos[i], datos[minimo] = datos[minimo], datos[i]

    return datos, comparaciones
