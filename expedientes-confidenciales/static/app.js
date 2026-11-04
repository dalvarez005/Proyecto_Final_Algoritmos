// Vista previa del cifrado César y confirmación al eliminar.
// Usa la misma lógica que algoritmos/cesar.py.

(function () {
    "use strict";

    var LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    function desplazar(codigo, base, d) {
        return String.fromCharCode(((codigo - base + d) % 26 + 26) % 26 + base);
    }

    function cifrar(texto, d) {
        var salida = "";
        for (var i = 0; i < texto.length; i++) {
            var c = texto.charCodeAt(i);
            if (c >= 97 && c <= 122) salida += desplazar(c, 97, d);
            else if (c >= 65 && c <= 90) salida += desplazar(c, 65, d);
            else salida += texto[i];
        }
        return salida;
    }

    document.querySelectorAll("[data-cifrado]").forEach(function (bloque) {
        var form = bloque.closest("form");
        var texto = form.querySelector("[data-cifrado-texto]");
        var rango = bloque.querySelector("[data-cifrado-desplazamiento]");
        var valor = bloque.querySelector("[data-cifrado-valor]");
        var salida = bloque.querySelector("[data-cifrado-salida]");
        var alfabeto = bloque.querySelector("[data-alfabeto]");
        var celdas = [];

        for (var i = 0; i < 26; i++) {
            var celda = document.createElement("span");
            celda.className = "letra";
            celda.innerHTML = '<span class="letra-plana"></span><span class="letra-cifrada"></span>';
            celda.firstChild.textContent = LETRAS[i];
            alfabeto.appendChild(celda);
            celdas.push(celda);
        }

        function actualizar() {
            var d = parseInt(rango.value, 10) || 0;
            var usadas = texto.value.toUpperCase();

            valor.textContent = "+" + d;
            salida.textContent = cifrar(texto.value, d);

            celdas.forEach(function (celda, i) {
                celda.lastChild.textContent = desplazar(65 + i, 65, d);
                celda.classList.toggle("en-uso", usadas.indexOf(LETRAS[i]) !== -1);
            });
        }

        rango.addEventListener("input", actualizar);
        texto.addEventListener("input", actualizar);
        actualizar();
    });

    document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
        form.addEventListener("submit", function (evento) {
            if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
        });
    });
})();
