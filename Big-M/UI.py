import customtkinter as ctk
from tkinter import messagebox
from fractions import Fraction
from typing import List, Callable, Optional

# Clase para almacenar el modelo de programación lineal
class LPModel:
    def __init__(self):
        self.sense = None       # 'max' o 'min'
        self.vector_c = []
        self.matrix_A = []
        self.vector_b = []
        self.vector_x = []
        self.rel = []           # '<=', '>=' o '='
        self.n = 0
        self.m = 0

# ──────────────────────────────────────────────────────────
# Ventana principal para ingresar dimensiones y lanzar el proceso simplex
# ──────────────────────────────────────────────────────────
class SimplexUI(ctk.CTk):
    def __init__(self, solve_callback: Optional[Callable] = None):
        super().__init__()
        self.n = None
        self.m = None
        self.solve_callback = solve_callback   # función solve(model) -> Result
        self.title("Método Simplex")
        self.geometry("500x300")
        self.ingresar_dimensiones()

    # Construye formulario para ingresar n y m
    def ingresar_dimensiones(self):
        self.label = ctk.CTkLabel(self, text="Ingresa el número de variables y restricciones")
        self.label.pack(pady=20)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, padx=20, pady=20)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        self.label_n = ctk.CTkLabel(container, text="Variables (n):")
        self.entry_n = ctk.CTkEntry(container, width=100, justify="center")
        self.label_m = ctk.CTkLabel(container, text="Restricciones (m):")
        self.entry_m = ctk.CTkEntry(container, width=100, justify="center")

        self.label_n.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_n.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.label_m.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_m.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.ok_button = ctk.CTkButton(self, text="Aceptar", command=self.start_simplex)
        self.ok_button.pack(pady=20)

    # Valida n y m, luego abre la ventana de ingresar los datos del modelo
    def start_simplex(self):
        try:
            n = int(self.entry_n.get().strip())
            m = int(self.entry_m.get().strip())
            if n <= 0 or m <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "n y m deben ser enteros positivos.")
            return

        self.n, self.m = n, m
        self.withdraw()
        self.modal = Ingresar_valores(
            self, n=self.n, m=self.m,
            solve_callback=self.solve_callback
        )


# ──────────────────────────────────────────────────────────
# Ventana 2 de ingreso de datos
# ──────────────────────────────────────────────────────────


class Ingresar_valores(ctk.CTkToplevel):
    def __init__(self, master, n: int, m: int, solve_callback=None):
        super().__init__(master)
        self.n = n
        self.m = m
        self.solve_callback = solve_callback

        self.title("Ingresar valores - Simplex")
        self.geometry("900x700")
        self.grab_set() # Hace esta ventana modal

        self.entries_A: List[List[ctk.CTkEntry]] = []
        self.entries_b: List[ctk.CTkEntry] = []
        self.rel_vars: List[ctk.StringVar] = []
        self.entries_c: List[ctk.CTkEntry] = []
        self.model = LPModel()

        # ── Header ──────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Ingresa función objetivo y restricciones",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))

        # ── Función objetivo ─────────────────────────────────────
        obj_frame = ctk.CTkFrame(self)
        obj_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(obj_frame, text="Función objetivo:",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.sense_var = ctk.StringVar(value="max")
        ctk.CTkOptionMenu(obj_frame, values=["max", "min"],
                          variable=self.sense_var).grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(obj_frame, text="Z =").grid(row=0, column=2, padx=(20, 5), pady=10, sticky="e")

        c_frame = ctk.CTkFrame(obj_frame, fg_color="transparent")
        c_frame.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        for j in range(self.n):
            e = ctk.CTkEntry(c_frame, width=70, justify="center", placeholder_text="0")
            e.grid(row=0, column=2 * j, padx=(0, 4))
            self.entries_c.append(e)
            ctk.CTkLabel(c_frame, text=f"·x{j+1}").grid(row=0, column=2 * j + 1, padx=(0, 10))

        # ── Restricciones ────────────────────────────────────────
        cons_frame = ctk.CTkFrame(self)
        cons_frame.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(cons_frame, text="Restricciones:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w", columnspan=10)

        grid_frame = ctk.CTkFrame(cons_frame, fg_color="transparent")
        grid_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        for j in range(self.n):
            ctk.CTkLabel(grid_frame, text=f"x{j+1}").grid(row=0, column=j, padx=3, pady=3)
        ctk.CTkLabel(grid_frame, text="rel").grid(row=0, column=self.n, padx=8, pady=3)
        ctk.CTkLabel(grid_frame, text="b").grid(row=0, column=self.n + 1, padx=3, pady=3)

        for i in range(self.m):
            fila = []
            for j in range(self.n):
                e = ctk.CTkEntry(grid_frame, width=70, justify="center", placeholder_text="0")
                e.grid(row=i + 1, column=j, padx=3, pady=3)
                fila.append(e)
            self.entries_A.append(fila)

            rel_var = ctk.StringVar(value="<=")
            ctk.CTkOptionMenu(grid_frame, values=["<=", ">=", "="],
                              variable=rel_var, width=80).grid(
                row=i + 1, column=self.n, padx=8, pady=3)
            self.rel_vars.append(rel_var)

            eb = ctk.CTkEntry(grid_frame, width=70, justify="center", placeholder_text="0")
            eb.grid(row=i + 1, column=self.n + 1, padx=3, pady=3)
            self.entries_b.append(eb)

        # ── Botones ──────────────────────────────────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=15)
        ctk.CTkButton(btns, text="Resolver", command=self._validar_y_resolver).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btns, text="Cancelar", command=self._cancelar,
                      fg_color="gray40").grid(row=0, column=1, padx=10)

    def _cancelar(self):
        self.destroy()
        self.master.deiconify()

    def _validar_y_resolver(self):
        """Valida entradas, llena el modelo y llama al solver."""
        try:
            sense = self.sense_var.get().strip()
            if sense not in ("max", "min"):
                raise ValueError("Sense inválido")

            c = [Fraction(e.get().strip() or "0") for e in self.entries_c]
            A = [[Fraction(e.get().strip() or "0") for e in fila] for fila in self.entries_A]
            rel = [v.get() for v in self.rel_vars]

            for r in rel:
                if r not in ("<=", ">=", "="):
                    raise ValueError("Relación inválida")

            b = [Fraction(e.get().strip() or "0") for e in self.entries_b]

        except Exception:
            messagebox.showerror(
                "Error de entrada",
                "Revisa tus valores.\n"
                "Usa números válidos: 3, -2, 1/4.\n"
                "No dejes campos con texto inválido."
            )
            return

        # Llenar modelo
        self.model.sense    = sense
        self.model.vector_c = c
        self.model.matrix_A = A
        self.model.vector_b = b
        self.model.rel      = rel
        self.model.n        = self.n
        self.model.m        = self.m

        # Resolver
        if self.solve_callback is None:
            messagebox.showwarning("Sin solver", "No hay solver conectado.")
            return

        try:
            result = self.solve_callback(self.model)
        except Exception as e:
            messagebox.showerror("Error en el solver", str(e))
            return

        # Mostrar resultados
        self.withdraw()
        ResultWindow(self, result, self.model)


# ──────────────────────────────────────────────────────────
# Ventana de resultados
# ──────────────────────────────────────────────────────────

class ResultWindow(ctk.CTkToplevel):
    def __init__(self, master, result, model: LPModel):
        super().__init__(master)
        self.title("Resultado - Simplex")
        self.geometry("520x420")
        self.grab_set()
        self.resizable(False, False)

        ctk.CTkLabel(
            self, text="Resultado del Método Simplex",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        # ── Panel de estado ──────────────────────────────────────
        status_colors = {
            "Optimal":    ("green", "✓ Solución Óptima"),
            "Unbounded":  ("orange", "⚠ Problema No Acotado"),
            "Infeasible": ("red",    "✗ Problema Infactible"),
        }
        color, label = status_colors.get(result.status, ("gray", result.status))

        ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=color
        ).pack(pady=5)

        # ── Cuerpo de resultados ─────────────────────────────────
        body = ctk.CTkFrame(self)
        body.pack(padx=30, pady=10, fill="both", expand=True)

        if result.status == "Optimal":
            # Valor óptimo
            z_label = "Z (mín)" if model.sense == "min" else "Z (máx)"
            self._row(body, 0, z_label, str(result.z))

            # Variables
            for i, xi in enumerate(result.x):
                self._row(body, i + 1, f"x{i+1}", str(xi))

            # Iteraciones
            self._row(body, len(result.x) + 1, "Iteraciones", str(result.iterations))

        elif result.status == "Unbounded":
            ctk.CTkLabel(
                body,
                text="La función objetivo crece sin límite.\n"
                     "Verifica que las restricciones sean suficientes.",
                wraplength=400, justify="left"
            ).pack(padx=15, pady=20)

        elif result.status == "Infeasible":
            ctk.CTkLabel(
                body,
                text="No existe solución factible.\n"
                     "Las restricciones son contradictorias.",
                wraplength=400, justify="left"
            ).pack(padx=15, pady=20)

        # ── Botón cerrar ─────────────────────────────────────────
        ctk.CTkButton(
            self, text="Cerrar", width=120,
            command=self._cancelar
        ).pack(pady=15)


    def _cancelar(self):
        self.destroy()
        self.master.deiconify()

    @staticmethod
    def _row(parent, row_idx, label, value):
        """Dibuja una fila label / valor en el grid de resultados."""
        ctk.CTkLabel(
            parent, text=label + ":",
            font=ctk.CTkFont(weight="bold"), anchor="e"
        ).grid(row=row_idx, column=0, padx=(20, 10), pady=6, sticky="e")

        ctk.CTkLabel(
            parent, text=value, anchor="w"
        ).grid(row=row_idx, column=1, padx=(0, 20), pady=6, sticky="w")
