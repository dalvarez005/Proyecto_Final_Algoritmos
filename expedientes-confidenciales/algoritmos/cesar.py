
def cifrar(texto, desplazamiento):
    resultado = ""

    for caracter in texto:
        if 'a' <= caracter <= 'z':
            nueva = (ord(caracter) - ord('a') + desplazamiento) % 26
            resultado += chr(nueva + ord('a'))

        elif 'A' <= caracter <= 'Z':
            nueva = (ord(caracter) - ord('A') + desplazamiento) % 26
            resultado += chr(nueva + ord('A'))

        else:
            resultado += caracter

    return resultado


def descifrar(texto, desplazamiento):
    return cifrar(texto, -desplazamiento)
