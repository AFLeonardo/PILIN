# Simplex Solver

Implementación del **Método Simplex en Dos Fases** con interfaz gráfica.
Resuelve problemas de Programación Lineal con soporte para maximización y minimización,
restricciones `<=`, `>=` y `=`, y coeficientes negativos.

---

## Requisitos

- Python 3.10 o superior
- customtkinter

```bash
pip install customtkinter
```

---

## Archivos

| Archivo | Descripción |
|---|---|
| `Simplex.py` | Lógica del solver y punto de entrada |
| `UI.py` | Interfaz gráfica (CustomTkinter) |

---

## Uso

```bash
# Abrir la interfaz gráfica
python Simplex.py

# Correr los tests con ejercicios de clase
python Simplex.py --test
```

---

## Qué soporta

- Maximización y minimización
- Restricciones `<=`, `>=` y `=`
- Coeficientes negativos y `b < 0`
- Aritmética exacta con `Fraction` (sin errores de punto flotante)

---

## Workflow de la GUI

```
SimplexUI  →  (usuario ingresa n, m)
    ↓
Ingresar_valores  →  (usuario llena la tabla)
    ↓
solve_callback(model)  →  (algoritmo externo resuelve)
    ↓
ResultWindow  →  (muestra el resultado)
```

---

## Workflow de la lógica

```
solve(model)
    │
    ├─ Convertir Min → Max (negando c)
    ├─ _build_tableau()
    │       ├─ Normalizar b < 0
    │       └─ Agregar holguras y artificiales
    │
    ├─ ¿Hay artificiales?
    │       └─ _phase1() → ¿Z=0? → Factible / Infeasible
    │
    └─ _phase2()
            ├─ _simplex_iterations()
            │       ├─ Dantzig (columna entrante)
            │       ├─ Razón mínima (fila saliente)
            │       └─ _pivot()
            └─ Leer resultados del tableau
```

---

## Estructura interna del solver

```
SimplexSolver
    ├── solve()                  ← punto de entrada, orquesta todo
    ├── _build_tableau()         ← prepara la estructura de datos
    ├── _phase1()                ← encuentra una solución básica factible
    ├── _phase2()                ← optimiza la función objetivo original
    ├── _simplex_iterations()    ← núcleo del algoritmo (reutilizado en ambas fases)
    └── _pivot()                 ← operación elemental de fila (Gauss-Jordan)
```

---

## Decisiones de diseño

- **`Fraction` en lugar de `float`**: evita errores de redondeo en los pivoteos sucesivos.
- **Separación UI / solver**: la interfaz recibe el solver como `solve_callback`, por lo que pueden desarrollarse y testearse de forma independiente.
- **Dos Fases**: la Fase 1 solo se ejecuta cuando hay restricciones `>=` o `=`, ya que son las que requieren variables artificiales para obtener una solución básica inicial.