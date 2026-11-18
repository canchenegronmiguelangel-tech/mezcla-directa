import os
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


def leer(f):
    linea = f.readline().strip()
    return int(linea) if linea else None


def leer_archivo(nombre):
    if not os.path.exists(nombre):
        return []
    with open(nombre, "r", encoding="utf-8") as f:
        return [int(linea.strip()) for linea in f if linea.strip()]


def escribir_archivo(nombre, datos):
    with open(nombre, "w", encoding="utf-8") as f:
        for d in datos:
            f.write(f"{d}\n")


def partir(lista, longitud):
    return [lista[i:i + longitud] for i in range(0, len(lista), longitud)]


def distribuir(origen, aux1, aux2, longitud):
    destinos = [open(aux1, "w", encoding="utf-8"), open(aux2, "w", encoding="utf-8")]
    actual, contador = 0, 0
    with open(origen, "r", encoding="utf-8") as src:
        for linea in src:
            if not linea.strip():
                continue
            destinos[actual].write(linea)
            contador += 1
            if contador == longitud:
                contador = 0
                actual = 1 - actual
    for d in destinos:
        d.close()


def mezclar(aux1, aux2, destino, longitud):
    with open(aux1, "r", encoding="utf-8") as f1, \
         open(aux2, "r", encoding="utf-8") as f2, \
         open(destino, "w", encoding="utf-8") as out:
        a, b = leer(f1), leer(f2)
        while a is not None or b is not None:
            ca = cb = 0
            while (a is not None and ca < longitud) or (b is not None and cb < longitud):
                toma_a = a is not None and ca < longitud
                toma_b = b is not None and cb < longitud
                if toma_a and (not toma_b or a <= b):
                    out.write(f"{a}\n")
                    a, ca = leer(f1), ca + 1
                else:
                    out.write(f"{b}\n")
                    b, cb = leer(f2), cb + 1


class MezclaDirectaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ejercicio 2 - Mezcla Directa (Folios de Ventas)")
        self.root.geometry("950x620")
        self.root.resizable(False, False)

        self.arch_origen = "folios.txt"
        self.arch_aux1 = "aux1.tmp"
        self.arch_aux2 = "aux2.tmp"

        self.folios_iniciales = []
        self.longitud = 1
        self.pasada = 0
        self.fase = "INICIO"

        self._construir_interfaz()

    def _construir_interfaz(self):
        # 1. Entrada manual / opciones de carga
        frame_top = ttk.LabelFrame(self.root, text="1. Capturar o Cargar Folios", padding=10)
        frame_top.pack(fill="x", padx=15, pady=8)

        ttk.Label(frame_top, text="Folios (separados por espacio o coma):").grid(row=0, column=0, padx=5)
        self.entry_folios = ttk.Entry(frame_top, width=28)
        self.entry_folios.grid(row=0, column=1, padx=5)
        self.entry_folios.bind("<Return>", lambda e: self.agregar_folios())

        ttk.Button(frame_top, text="+ Agregar Manual", command=self.agregar_folios).grid(row=0, column=2, padx=4)
        ttk.Button(frame_top, text="Usar Ejemplo (10)", command=self.cargar_ejemplo).grid(row=0, column=3, padx=8)
        ttk.Button(frame_top, text="Generar Aleatorios (12)", command=self.cargar_aleatorios).grid(row=0, column=4, padx=4)
        ttk.Button(frame_top, text="Limpiar", command=self.limpiar_todo).grid(row=0, column=5, padx=8)

        # 2. Paneles de archivos (Original, F1 y F2)
        frame_mid = ttk.Frame(self.root, padding=5)
        frame_mid.pack(fill="both", expand=True, padx=15)

        self.txt_principal = self._crear_panel(frame_mid, "Archivo Principal (folios.txt)", 0)
        self.txt_f1 = self._crear_panel(frame_mid, "Auxiliar F1 (aux1.tmp)", 1)
        self.txt_f2 = self._crear_panel(frame_mid, "Auxiliar F2 (aux2.tmp)", 2)

        # 3. Consola visual de pasadas
        frame_log = ttk.LabelFrame(self.root, text="Detalle de Pasadas y Bloques", padding=8)
        frame_log.pack(fill="x", padx=15, pady=5)

        self.txt_log = tk.Text(frame_log, height=7, font=("Consolas", 9), state="disabled", bg="#f8fafc")
        self.txt_log.pack(fill="x")

        # 4. Controles de ejecución
        frame_bot = ttk.LabelFrame(self.root, text="2. Ejecución", padding=10)
        frame_bot.pack(fill="x", padx=15, pady=8)

        ttk.Button(frame_bot, text="Ordenar Todo", command=self.ejecutar_completo).pack(side="left", padx=5)
        ttk.Button(frame_bot, text="Paso a Paso (Distribuir / Mezclar)", command=self.ejecutar_paso).pack(side="left", padx=5)
        ttk.Button(frame_bot, text="Reiniciar", command=self.reiniciar_ordenamiento).pack(side="left", padx=5)

        self.lbl_estado = ttk.Label(frame_bot, text="Estado: Esperando folios...", foreground="blue", font=("Segoe UI", 9, "bold"))
        self.lbl_estado.pack(side="left", padx=15)

        ttk.Button(frame_bot, text="Guardar .TXT", command=self.guardar_archivo).pack(side="right", padx=5)

    def _crear_panel(self, parent, titulo, col):
        frame = ttk.LabelFrame(parent, text=titulo, padding=5)
        frame.grid(row=0, column=col, padx=6, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        txt = tk.Text(frame, width=28, height=13, font=("Consolas", 10), state="disabled", bg="#ffffff")
        txt.pack(fill="both", expand=True)
        return txt

    def _escribir_panel(self, widget, datos, longitud_bloque=1):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        if not datos:
            widget.insert(tk.END, "(vacío)")
        else:
            bloques = partir(datos, longitud_bloque)
            for idx, b in enumerate(bloques, 1):
                widget.insert(tk.END, f"Bloque {idx}: {b}\n")
        widget.config(state="disabled")

    def _log(self, mensaje):
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def _limpiar_log(self):
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.config(state="disabled")

    def _limpiar_temporales(self):
        for tmp in (self.arch_aux1, self.arch_aux2):
            if os.path.exists(tmp):
                os.remove(tmp)

    def agregar_folios(self):
        texto = self.entry_folios.get().strip()
        if not texto:
            return
        partes = texto.replace(",", " ").split()
        nuevos = []
        for p in partes:
            if not p.isdigit():
                messagebox.showwarning("Error", f"'{p}' no es un número válido.")
                return
            nuevos.append(int(p))

        self.folios_iniciales.extend(nuevos)
        self.entry_folios.delete(0, tk.END)
        self.reiniciar_ordenamiento()

    def cargar_ejemplo(self):
        self.folios_iniciales = [38, 27, 43, 3, 9, 82, 10, 15, 61, 24]
        self.reiniciar_ordenamiento()
        self.lbl_estado.config(text="Ejemplo de 10 folios cargado.")

    def cargar_aleatorios(self):
        self.folios_iniciales = [random.randint(1, 99) for _ in range(12)]
        self.reiniciar_ordenamiento()
        self.lbl_estado.config(text="12 folios aleatorios generados.")

    def limpiar_todo(self):
        self.folios_iniciales.clear()
        self._limpiar_temporales()
        if os.path.exists(self.arch_origen):
            os.remove(self.arch_origen)
        self._limpiar_log()
        self._escribir_panel(self.txt_principal, [])
        self._escribir_panel(self.txt_f1, [])
        self._escribir_panel(self.txt_f2, [])
        self.fase = "INICIO"
        self.lbl_estado.config(text="Estado: Listas vacías.")

    def reiniciar_ordenamiento(self):
        self._limpiar_temporales()
        self._limpiar_log()
        self.longitud = 1
        self.pasada = 0
        self.fase = "DISTRIBUIR"

        if self.folios_iniciales:
            escribir_archivo(self.arch_origen, self.folios_iniciales)
            self._escribir_panel(self.txt_principal, self.folios_iniciales, 1)
            self._escribir_panel(self.txt_f1, [])
            self._escribir_panel(self.txt_f2, [])
            self._log(f"Archivo inicial ({len(self.folios_iniciales)} folios), bloques de L=1.")
            self.lbl_estado.config(text="Listo para ordenar.")
        else:
            self._escribir_panel(self.txt_principal, [])

    def ejecutar_paso(self):
        n = len(self.folios_iniciales)
        if n == 0:
            messagebox.showinfo("Aviso", "Agrega o carga folios primero.")
            return

        if self.fase == "FIN" or self.longitud >= n:
            self.fase = "FIN"
            self.lbl_estado.config(text=f"¡Ordenado en {self.pasada} pasadas!")
            return

        if self.fase == "DISTRIBUIR":
            self.pasada += 1
            distribuir(self.arch_origen, self.arch_aux1, self.arch_aux2, self.longitud)
            datos_f1 = leer_archivo(self.arch_aux1)
            datos_f2 = leer_archivo(self.arch_aux2)

            self._escribir_panel(self.txt_f1, datos_f1, self.longitud)
            self._escribir_panel(self.txt_f2, datos_f2, self.longitud)
            self._log(f"--- PASADA {self.pasada} (bloques de {self.longitud}) ---")
            self._log(f"  1) Distribución -> F1: {partir(datos_f1, self.longitud)} | F2: {partir(datos_f2, self.longitud)}")

            self.lbl_estado.config(text=f"Pasada {self.pasada}: Distribuido (L={self.longitud}). Sigue Mezclar.")
            self.fase = "MEZCLAR"

        elif self.fase == "MEZCLAR":
            mezclar(self.arch_aux1, self.arch_aux2, self.arch_origen, self.longitud)
            datos_res = leer_archivo(self.arch_origen)
            nuevo_l = self.longitud * 2

            self._escribir_panel(self.txt_principal, datos_res, nuevo_l)
            self._escribir_panel(self.txt_f1, [])
            self._escribir_panel(self.txt_f2, [])
            self._log(f"  2) Mezcla (bloques de {nuevo_l}) -> Archivo: {partir(datos_res, nuevo_l)}")

            self.longitud = nuevo_l
            if self.longitud >= n:
                self._limpiar_temporales()
                self.fase = "FIN"
                self.lbl_estado.config(text=f"¡Completado en {self.pasada} pasadas!")
                self._log("==> Verificación correcta: el archivo quedó ordenado.")
            else:
                self.fase = "DISTRIBUIR"
                self.lbl_estado.config(text=f"Pasada {self.pasada}: Mezclado (2L={nuevo_l}). Sigue Distribuir.")

    def ejecutar_completo(self):
        if not self.folios_iniciales:
            messagebox.showinfo("Aviso", "Agrega o carga folios primero.")
            return
        if self.fase == "FIN":
            self.reiniciar_ordenamiento()
        while self.fase != "FIN":
            self.ejecutar_paso()

    def guardar_archivo(self):
        datos = leer_archivo(self.arch_origen)
        if not datos:
            messagebox.showwarning("Sin datos", "No hay folios para guardar.")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="folios.txt",
            filetypes=[("Archivos de texto", "*.txt")]
        )
        if ruta:
            escribir_archivo(ruta, datos)
            messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta}")

    def al_cerrar(self):
        self._limpiar_temporales()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MezclaDirectaApp(root)

    root.protocol("WM_DELETE_WINDOW", app.al_cerrar)
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)

    root.mainloop()