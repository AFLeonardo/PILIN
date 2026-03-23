"""
Método Simplex en gran M para resolver Programación Lineal.
Soporta: Max/Min, restricciones <=, >= y =, coeficientes negativos y b<0.
Usa aritmética exacta con Fraction para resultados sin error de punto flotante.
"""

from fractions import Fraction
from UI import SimplexUI, LPModel


# ──────────────────────────────────────────────
# Clase resultado
# ──────────────────────────────────────────────

class Result:
    def __init__(self):
        self.status = None      # 'Optimal' | 'Unbounded' | 'Infeasible'
        self.x = []             # Valores de las variables de decisión
        self.z = None           # Valor óptimo de la función objetivo
        self.iterations = 0     # Total de iteraciones (Fase 1 + Fase 2)

    def __str__(self):
        if self.status == "Optimal":
            xs = ", ".join(f"x{i+1}={v}" for i, v in enumerate(self.x))
            return f"Óptimo | Z={self.z} | {xs} | iteraciones={self.iterations}"
        return f"Estado: {self.status}"


# ──────────────────────────────────────────────
# Solver
# ──────────────────────────────────────────────

class SimplexSolver:
    
    BIG_M = Fraction(10**6)
    MAX_ITER = 500

    def __init__(self, model: LPModel):
        self.model = model
        self.result = Result()

    # ── Punto de entrada ───────────────────────────────────────────────────

    def solve(self) -> Result:
        n = self.model.n
        m = self.model.m

        if self.model.sense == "min":
            c_obj = [-ci for ci in self.model.vector_c]
        else:
            c_obj = list(self.model.vector_c)

        tableau, basis, obj, n_slack, n_art, art_indices = self._build_tableau(n, m, c_obj)


        tableau.append(obj)
        self._simplex_iterations(tableau, basis, m, allowed_cols=list(range(n + n_slack + n_art)))
        
        # Detectar infactibilidad: artificial con valor > 0 en base
        for i, bv in enumerate(basis):
            if bv in art_indices and tableau[i][-1] > Fraction(0):
                self.result.status = "Infeasible"
                return self.result

        self.result.status = "Optimal"
        x = [Fraction(0)] * n
        for i, bv in enumerate(basis):
            if bv < n:
                x[bv] = tableau[i][-1]
        self.result.x = x
        self.result.z = tableau[-1][-1]
        if self.model.sense == "min":
            self.result.z = -self.result.z

        tableau.pop()
        return self.result

    # ── Construcción del tableau ───────────────────────────────────────────

    def _build_tableau(self, n, m, c_obj):
        """
        Construye el tableau inicial.
        """
        A   = self.model.matrix_A
        b   = self.model.vector_b
        rel = self.model.rel
        flip = {"<=": ">=", ">=": "<=", "=": "="}

        # Normalizar: garantizar b_norm >= 0
        A_n, b_n, rel_n = [], [], []
        for i in range(m):
            if b[i] < 0:
                A_n.append([-Fraction(a) for a in A[i]])
                b_n.append(-Fraction(b[i]))
                rel_n.append(flip[rel[i]])
            else:
                A_n.append([Fraction(a) for a in A[i]])
                b_n.append(Fraction(b[i]))
                rel_n.append(rel[i])

        n_art   = sum(1 for r in rel_n if r in (">=", "="))
        n_slack = m
        cols    = n + n_slack + n_art + 1

        tableau     = []
        art_indices = []
        art_count   = 0

        for i in range(m):
            row = [Fraction(0)] * cols
            for j in range(n):
                row[j] = A_n[i][j]
            if rel_n[i] == "<=":
                row[n + i] = Fraction(1)
            elif rel_n[i] == ">=":
                row[n + i] = Fraction(-1)
            if rel_n[i] in (">=", "="):
                ac = n + n_slack + art_count
                row[ac] = Fraction(1)
                art_indices.append(ac)
                art_count += 1
            row[-1] = b_n[i]
            tableau.append(row)

        basis   = []
        art_ptr = 0
        for i in range(m):
            if rel_n[i] == "<=":
                basis.append(n + i)
            else:
                basis.append(art_indices[art_ptr])
                art_ptr += 1

        cols = n + n_slack + n_art + 1
        obj = [Fraction(0)] * cols
        
        for j in range(n):
            obj[j] = -c_obj[j]          # coeficientes originales
        for ac in art_indices:
            obj[ac] = self.BIG_M        # penalización +M (tableau maximiza con signo negativo)
        
        # Eliminar básicas artificiales de la fila objetivo
        for i, bv in enumerate(basis):
            if bv in art_indices:
                for k in range(cols):
                    obj[k] -= self.BIG_M * tableau[i][k]
        
        return tableau, basis, obj, n_slack, n_art, art_indices

    # ── Núcleo iterativo ───────────────────────────────────────────────────

    def _simplex_iterations(self, tableau, basis, m, allowed_cols=None):
        """
        obj = tableau[-1]` se reasigna al inicio de CADA
        iteración para que siempre refleje el estado actual del tableau.

        allowed_cols: columnas candidatas a entrar (None = todas menos RHS).
        """
        cols = len(tableau[0])
        if allowed_cols is None:
            allowed_cols = list(range(cols - 1))

        for _ in range(self.MAX_ITER):
            self.result.iterations += 1

            obj = tableau[-1]   # re-leer en cada iteración
            pivot_col = -1
            min_val   = Fraction(0)
            for j in allowed_cols:
                if obj[j] < min_val:
                    min_val   = obj[j]
                    pivot_col = j

            if pivot_col == -1:
                break   # Óptimo

            # Prueba de razón mínima
            pivot_row = -1
            min_ratio = None
            for i in range(m):
                if tableau[i][pivot_col] > 0:
                    ratio = tableau[i][-1] / tableau[i][pivot_col]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        pivot_row = i

            if pivot_row == -1:
                self.result.status = "Unbounded"
                return

            self._pivot(tableau, basis, pivot_row, pivot_col, m)

    # ── Pivoteo ────────────────────────────────────────────────────────────

    def _pivot(self, tableau, basis, pr, pc, m):
        """Normaliza la fila pivote y elimina la columna pivote en las demás."""
        pv   = tableau[pr][pc]
        cols = len(tableau[0])

        tableau[pr] = [x / pv for x in tableau[pr]]

        for i in range(len(tableau)):
            if i != pr:
                f = tableau[i][pc]
                if f != 0:
                    tableau[i] = [
                        tableau[i][k] - f * tableau[pr][k]
                        for k in range(cols)
                    ]

        basis[pr] = pc


# ──────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────

def solve(model: LPModel) -> Result:
    if not hasattr(model, "n") or not model.n:
        model.n = len(model.vector_c)
    if not hasattr(model, "m") or not model.m:
        model.m = len(model.vector_b)
    return SimplexSolver(model).solve()


# ──────────────────────────────────────────────
# Tests con ejercicios de clase
# ──────────────────────────────────────────────

def _run_tests():
    sep = "─" * 60

    def test(name, model, exp_status, exp_z=None):
        r = solve(model)
        ok = (r.status == exp_status) and (
            exp_z is None or (r.z is not None and r.z == Fraction(exp_z))
        )
        print(f"{'✓' if ok else '✗'} {name}")
        print(f"  {r}")
        if not ok:
            print(f"  FALLÓ — esperado: status={exp_status}, Z={exp_z}")
        print()
        return ok

    print(sep)
    print("TESTS DEL SOLVER SIMPLEX CON PROBLEMAS VISTO EN CLASE")
    print(sep)
    results = []

    # Test 1 — 2 variables, Max <=
    # Max Z=10x1+20x2 | 3x1+x2<=90, x1+x2<=50, x2<=35 | Óptimo: Z=850
    m = LPModel(); m.sense="max"; m.n,m.m=2,3
    m.vector_c=[Fraction(10),Fraction(20)]
    m.matrix_A=[[Fraction(3),Fraction(1)],[Fraction(1),Fraction(1)],[Fraction(0),Fraction(1)]]
    m.vector_b=[Fraction(90),Fraction(50),Fraction(35)]; m.rel=["<=","<=","<="]
    results.append(test("2 variables — Max Z=10x1+20x2 (<=)", m, "Optimal", 850))

    # Test 2 — 3 variables, Max <=
    # Max Z=2000x1+3000x2 | x1+x2<=20, x1+2x2<=30, | Óptimo: Z=50000
    m = LPModel(); m.sense="max"; m.n,m.m=2,2
    m.vector_c=[Fraction(2000),Fraction(3000)]
    m.matrix_A=[[Fraction(1),Fraction(1)],
                [Fraction(1),Fraction(2)]]
    m.vector_b=[Fraction(20),Fraction(30)]; m.rel=["<=","<="]
    results.append(test("2 variables — Max Z=2000x1+3000x2 (<=)", m, "Optimal", 50000))

    # Test 3 — Minimización con >=
    # Min Z=2x1+3x2 | x1+x2>=4, x1+3x2>=6 | Óptimo: x1=3,x2=1, Z=9
    m = LPModel(); m.sense="min"; m.n,m.m=2,2
    m.vector_c=[Fraction(2),Fraction(3)]
    m.matrix_A=[[Fraction(1),Fraction(1)],[Fraction(1),Fraction(3)]]
    m.vector_b=[Fraction(4),Fraction(6)]; m.rel=[">=",">="]
    results.append(test("Minimización — Min Z=2x1+3x2 (>=)", m, "Optimal", 9))

    # Test 4 - Minimización de 3 variables
    # Min Z=2x1-x2-5x3 | 3x1+2x2+7x3<=25 | 5x1+x2+9x3 <= 55 | Óptimo: Z=-125/7
    m = LPModel(); m.sense="min"; m.n,m.m=3,2
    m.vector_c=[Fraction(2),Fraction(-1),Fraction(-5)]
    m.matrix_A=[[Fraction(3),Fraction(2),Fraction(7)],
                [Fraction(5),Fraction(1),Fraction(9)]]
    m.vector_b=[Fraction(25),Fraction(55)]; m.rel=["<=","<="]
    results.append(test("Minimización - 3 variables — Min Z=2x1-x2-5x3 (<=)", m, "Optimal", Fraction(-125, 7)))

    print(sep)
    print(f"Resultado: {sum(results)}/{len(results)} tests pasaron")
    print(sep)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    import sys
    if "--test" in sys.argv:
        _run_tests()
        return
    app = SimplexUI(solve_callback=solve)
    app.mainloop()


if __name__ == "__main__":
    main()