// Vista previa del cifrado César, edición en la tabla y confirmación al eliminar.
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

    // ---------- Paneles bajo cada fila: editar y confirmar borrado ----------
    // Solo uno abierto a la vez. Sin JavaScript, los enlaces abren el panel desde el servidor.

    function botonDe(panel) {
        return document.querySelector('[data-panel="' + panel.id + '"]');
    }

    function cerrarPanel(panel) {
        if (panel.hidden) return;
        panel.hidden = true;
        var fila = panel.previousElementSibling;
        while (fila && fila.classList.contains("fila-panel")) fila = fila.previousElementSibling;
        if (fila) fila.classList.remove("editando", "borrando");
        var boton = botonDe(panel);
        if (boton) boton.setAttribute("aria-expanded", "false");

        var form = panel.classList.contains("fila-edicion") && panel.querySelector("form");
        if (form) {
            form.reset();
            var aviso = form.querySelector(".aviso");
            if (aviso) aviso.remove();
            form.querySelectorAll("[data-cifrado-texto]").forEach(function (t) {
                t.dispatchEvent(new Event("input"));
            });
        }
    }

    function abrirPanel(panel, boton) {
        document.querySelectorAll(".fila-panel:not([hidden])").forEach(cerrarPanel);
        panel.hidden = false;
        var fila = panel.previousElementSibling;
        while (fila && fila.classList.contains("fila-panel")) fila = fila.previousElementSibling;
        var esEdicion = panel.classList.contains("fila-edicion");
        if (fila) fila.classList.add(esEdicion ? "editando" : "borrando");
        boton.setAttribute("aria-expanded", "true");

        var destino = esEdicion
            ? panel.querySelector("input:not([type=hidden])")
            : panel.querySelector("[data-cerrar-panel]");
        if (destino) destino.focus({ preventScroll: true });
        panel.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }

    function limpiarURL(href) {
        if (/[?&](editar|eliminar)=/.test(location.search)) {
            history.replaceState(null, "", href);
        }
    }

    document.querySelectorAll("[data-panel]").forEach(function (boton) {
        boton.addEventListener("click", function (evento) {
            var panel = document.getElementById(boton.dataset.panel);
            if (!panel) return;
            evento.preventDefault();
            if (panel.hidden) abrirPanel(panel, boton);
            else cerrarPanel(panel);
        });
    });

    document.querySelectorAll("[data-cerrar-panel]").forEach(function (enlace) {
        enlace.addEventListener("click", function (evento) {
            var panel = document.getElementById(enlace.dataset.cerrarPanel);
            if (!panel) return;
            evento.preventDefault();
            cerrarPanel(panel);
            var boton = botonDe(panel);
            if (boton) boton.focus();
            limpiarURL(enlace.getAttribute("href"));
        });
    });

    document.addEventListener("keydown", function (evento) {
        if (evento.key !== "Escape") return;
        document.querySelectorAll(".fila-borrar:not([hidden])").forEach(function (panel) {
            cerrarPanel(panel);
            var boton = botonDe(panel);
            if (boton) boton.focus();
        });
    });
})();
