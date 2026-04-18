from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple


@dataclass(frozen=True)
class Item:
    """
    Representa un ítem LR(0): A → α · β
    
    Ejemplo: S → a · B c  se representa como:
      head = 'S'
      body = ('a', 'B', 'c')
      dot  = 1 
    """
    head: str
    body: tuple
    dot: int

    def symbol_after_dot(self):
        """Retorna el símbolo después del punto, o None si está al final."""
        if self.dot < len(self.body):
            return self.body[self.dot]
        return None

    def is_complete(self):
        """Un ítem es completo (de reducción) cuando el punto está al final."""
        return self.dot >= len(self.body)

    def __str__(self):
        body_list = list(self.body)
        body_with_dot = body_list[:self.dot] + ['·'] + body_list[self.dot:]
        body_str = ' '.join(body_with_dot) if body_with_dot != ['·'] else '·'
        return f"{self.head} → {body_str}"

    def __repr__(self):
        return str(self)


class Grammar:
    """Representa una gramática libre de contexto."""

    def __init__(self, productions: List[Tuple[str, List[str]]]):
        """
        productions: lista de (cabeza, cuerpo)
        Ejemplo: [('S', ['a', 'b']), ('S', ['c'])]
        """
        self.productions = productions
        self.start_symbol = productions[0][0]
        self._build_index()

    def _build_index(self):
        """Índice de producciones por no-terminal."""
        self.rules: Dict[str, List[tuple]] = {}
        for head, body in self.productions:
            if head not in self.rules:
                self.rules[head] = []
            self.rules[head].append(tuple(body))

    def is_nonterminal(self, symbol: str) -> bool:
        return symbol in self.rules

    def initial_items(self) -> Set[Item]:
        """Ítems iniciales del símbolo de inicio."""
        items = set()
        for body in self.rules.get(self.start_symbol, []):
            items.add(Item(self.start_symbol, body, 0))
        return items


# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIÓN CERRADURA
# ─────────────────────────────────────────────────────────────────────────────

def closure(items: Set[Item], grammar: Grammar, verbose: bool = True) -> Set[Item]:
    """
    Calcula la cerradura (CLOSURE) de un conjunto de ítems LR(0).

    Regla: Si  A → α · B β  está en el conjunto,
           y   B → γ  es una producción,
           entonces  B → · γ  se agrega al conjunto.
    Se repite hasta no agregar más ítems.
    """
    result = set(items)

    if verbose:
        print("  Ítems de entrada:")
        for item in sorted(items, key=str):
            print(f"    {item}")
        print()
        print("  Aplicando regla de cerradura")

    changed = True
    while changed:
        changed = False
        new_items = set()

        for item in result:
            B = item.symbol_after_dot()
            if B is not None and grammar.is_nonterminal(B):
                for body in grammar.rules.get(B, []):
                    new_item = Item(B, body, 0)
                    if new_item not in result:
                        new_items.add(new_item)
                        if verbose:
                            print(f"    Punto antes de '{B}' en [{item}]")
                            print(f"      Agrego: {new_item}")

        if new_items:
            result |= new_items
            changed = True

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIÓN GOTO
# ─────────────────────────────────────────────────────────────────────────────

def goto(items: Set[Item], symbol: str, grammar: Grammar, verbose: bool = False) -> Set[Item]:
    """
    Calcula GOTO(I, X): mueve el punto sobre el símbolo X y aplica cerradura.
    """
    moved = set()
    for item in items:
        if item.symbol_after_dot() == symbol:
            moved.add(Item(item.head, item.body, item.dot + 1))
    return closure(moved, grammar, verbose=verbose)


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTRUCCIÓN DEL AUTÓMATA LR(0)
# ─────────────────────────────────────────────────────────────────────────────

def build_lr0_automaton(grammar: Grammar):
    """
    Construye todos los estados (conjuntos de ítems) del autómata LR(0).
    Retorna: (estados, transiciones)
    """
    start_items = closure({Item(grammar.start_symbol, list(grammar.rules[grammar.start_symbol])[0], 0)}, grammar, verbose=False)
    
    all_bodies = grammar.rules[grammar.start_symbol]
    initial_set = set()
    for body in all_bodies:
        initial_set.add(Item(grammar.start_symbol, body, 0))
    
    I0 = frozenset(closure(initial_set, grammar, verbose=False))

    states = [I0]
    state_index = {I0: 0}
    transitions = {}  

    queue = [I0]
    while queue:
        current = queue.pop(0)
        idx = state_index[current]

        symbols = set()
        for item in current:
            s = item.symbol_after_dot()
            if s is not None:
                symbols.add(s)

        for sym in sorted(symbols):
            next_state = frozenset(goto(current, sym, grammar, verbose=False))
            if not next_state:
                continue
            if next_state not in state_index:
                state_index[next_state] = len(states)
                states.append(next_state)
                queue.append(next_state)
            transitions[(idx, sym)] = state_index[next_state]

    return states, transitions


def print_automaton(states, transitions, grammar_name=""):
    """Imprime el autómata LR(0) de forma legible."""
    SEP = "─" * 60
    print(f"\n{'═'*60}")
    print(f"  AUTÓMATA LR(0) — {grammar_name}")
    print(f"{'═'*60}")

    for i, state in enumerate(states):
        items = sorted(state, key=str)
        has_reduction = any(item.is_complete() for item in items)
        marker = " [REDUCCIÓN]" if has_reduction else ""
        print(f"\n  I{i}{marker}")
        print(f"  {SEP[:40]}")
        for item in items:
            tag = " ← reduce" if item.is_complete() else ""
            print(f"    {item}{tag}")

    print(f"\n  {'─'*40}")
    print("  TABLA DE TRANSICIONES")
    print(f"  {'─'*40}")
    print(f"  {'Estado':<10} {'Símbolo':<15} {'→ Estado'}")
    print(f"  {'─'*40}")
    for (from_s, sym), to_s in sorted(transitions.items()):
        print(f"  I{from_s:<9} {sym:<15} I{to_s}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  DEMOSTRACIÓN INTERACTIVA DE CLOSURE
# ─────────────────────────────────────────────────────────────────────────────

def demo_closure(grammar: Grammar, item: Item, label: str):
    """Muestra el cálculo de cerradura paso a paso."""
    print(f"\n{'═'*60}")
    print(f"  CERRADURA — {label}")
    print(f"{'═'*60}")
    result = closure({item}, grammar, verbose=True)
    print(f"\n  Conjunto final (cerradura completa):")
    for i in sorted(result, key=str):
        tag = "  REDUCCIÓN" if i.is_complete() else ""
        print(f"    {i}{tag}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  GRAMÁTICAS DEL PROBLEMA
# ─────────────────────────────────────────────────────────────────────────────

def gramatica_clase():
    """
    Gramática vista en clase:
    E' → E
    E  → E + T | T
    T  → T * F | F
    F  → ( E ) | id
    """
    return Grammar([
        ("E'", ["E"]),
        ("E",  ["E", "+", "T"]),
        ("E",  ["T"]),
        ("T",  ["T", "*", "F"]),
        ("T",  ["F"]),
        ("F",  ["(", "E", ")"]),
        ("F",  ["id"]),
    ])


def gramatica1():
    """
    S → S S + | S S * | a
    """
    return Grammar([
        ("S", ["S", "S", "+"]),
        ("S", ["S", "S", "*"]),
        ("S", ["a"]),
    ])


def gramatica2():
    """
    S → ( S ) | ε
    """
    return Grammar([
        ("S", ["(", "S", ")"]),
        ("S", []),         
    ])


def gramatica3():
    """
    S → L
    L → a L | a
    """
    return Grammar([
        ("S", ["L"]),
        ("L", ["a", "L"]),
        ("L", ["a"]),
    ])


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
#  MODO INTERACTIVO
# ─────────────────────────────────────────────────────────────────────────────

def ingresar_gramatica() -> Grammar:
    """Permite al usuario ingresar una gramática desde la terminal."""
    print("\n  Ingresa las producciones una por una.")
    print("  Formato: CABEZA simbolo1 simbolo2")
    print("  Para epsilon (ε) deja el cuerpo vacío y presiona Enter.")
    print("  Escribe 'listo' cuando termines.\n")

    producciones = []
    while True:
        linea = input("  Producción: ").strip()
        if linea.lower() == "listo":
            if not producciones:
                print("  Debes ingresar al menos una producción.")
                continue
            break
        partes = linea.split()
        if not partes:
            continue
        head = partes[0]
        body = partes[1:] 
        producciones.append((head, body))
        print(f"  Registrado: {head} → {' '.join(body) if body else 'ε'}")

    return Grammar(producciones)


def ingresar_item(grammar: Grammar) -> Item:
    """Permite al usuario ingresar un ítem inicial."""
    print("\n  Ingresa el ítem inicial.")
    print("  Formato: CABEZA simbolo1 simbolo2")
    print("  Ejemplo:  S DOT L   →  S → · L  (punto al inicio)")
    print("  Ejemplo:  L a DOT L →  L → a · L (punto en medio)\n")

    while True:
        linea = input("  Ítem: ").strip().split()
        if not linea:
            continue
        head = linea[0]
        rest = linea[1:]
        if "DOT" not in rest:
            print("  Error: debes incluir DOT para indicar la posición del punto.")
            continue
        dot_pos = rest.index("DOT")
        body = [s for s in rest if s != "DOT"]
        if head not in grammar.rules:
            print(f"  Error: '{head}' no es un no-terminal de la gramática.")
            continue
        if tuple(body) not in grammar.rules.get(head, []):
            print(f"  Advertencia: {head} → {' '.join(body) if body else 'ε'} no está en la gramática, pero se calculará igual.")
        item = Item(head, tuple(body), dot_pos)
        print(f"  Ítem ingresado: {item}")
        return item


def modo_interactivo():
    """Menú principal del modo interactivo."""
    print("\n" + "="*60)
    print("  MODO INTERACTIVO — CERRADURA LR(0)")
    print("="*60)

    grammar = ingresar_gramatica()

    print(f"\n  Gramática registrada ({len(grammar.productions)} producción(es)):")
    for head, body in grammar.productions:
        print(f"    {head} → {' '.join(body) if body else 'ε'}")

    while True:
        print("\n  ¿Qué deseas hacer?")
        print("  1) Calcular cerradura de un ítem")
        print("  2) Construir autómata LR(0) completo")
        print("  3) Ingresar otra gramática")
        print("  4) Salir")
        opcion = input("\n  Opción: ").strip()

        if opcion == "1":
            item = ingresar_item(grammar)
            print()
            result = closure({item}, grammar, verbose=True)
            print(f"\n  Conjunto final (cerradura completa):")
            for i in sorted(result, key=str):
                tag = "  ← REDUCCIÓN" if i.is_complete() else ""
                print(f"    {i}{tag}")

        elif opcion == "2":
            states, transitions = build_lr0_automaton(grammar)
            print_automaton(states, transitions, "Gramática ingresada")

        elif opcion == "3":
            grammar = ingresar_gramatica()

        elif opcion == "4":
            print("\n  FIN\n")
            break
        else:
            print("  Opción no válida.")


if __name__ == "__main__":

    print("\n" + "="*60)
    print("  FUNCIÓN CERRADURA LR(0)")
    print("="*60)
    print("\n  ¿Qué modo deseas usar?")
    print("  1) Demo automática")
    print("  2) Modo interactivo")
    modo = input("\n  Opción: ").strip()

    if modo == "2":
        modo_interactivo()
        exit()

    print("\n" + "="*60)
    print("  MODO DEMO — GRAMÁTICAS DEL PROBLEMA")
    print("="*60)

    # ── Gramática de clase ────────────────────────────────────────
    g_clase = gramatica_clase()

    demo_closure(g_clase,
                 Item("E'", ("E",), 0),
                 "Gramática de clase — Ítem inicial E' → · E")

    demo_closure(g_clase,
                 Item("E", ("E", "+", "T"), 1),
                 "Gramática de clase — E → E · + T  (punto en posición 1)")

    demo_closure(g_clase,
                 Item("F", ("(", "E", ")"), 1),
                 "Gramática de clase — F → ( · E )  (punto antes de E)")

    # ── Gramática 1 ───────────────────────────────────────────────
    g1 = gramatica1()

    demo_closure(g1,
                 Item("S", ("S", "S", "+"), 0),
                 "Gramática 1 — Ítem inicial S → · S S +")

    demo_closure(g1,
                 Item("S", ("S", "S", "+"), 1),
                 "Gramática 1 — S → S · S +  (punto en posición 1)")

    # ── Gramática 2 ───────────────────────────────────────────────
    g2 = gramatica2()

    demo_closure(g2,
                 Item("S", ("(", "S", ")"), 0),
                 "Gramática 2 — Ítem inicial S → · ( S )")

    demo_closure(g2,
                 Item("S", ("(", "S", ")"), 1),
                 "Gramática 2 — S → ( · S )  (punto antes de S)")

    # ── Gramática 3 ───────────────────────────────────────────────
    g3 = gramatica3()

    demo_closure(g3,
                 Item("S", ("L",), 0),
                 "Gramática 3 — Ítem inicial S → · L")

    demo_closure(g3,
                 Item("L", ("a", "L"), 1),
                 "Gramática 3 — L → a · L  (punto antes de L)")

    # ─────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  AUTÓMATAS LR(0) COMPLETOS")
    print("="*60)

    for g, name in [
        (g_clase, "Gramática de clase (expresiones)"),
        (g1,      "Gramática 1: S → SS+ | SS* | a"),
        (g2,      "Gramática 2: S → (S) | ε"),
        (g3,      "Gramática 3: S → L, L → aL | a"),
    ]:
        states, transitions = build_lr0_automaton(g)
        print_automaton(states, transitions, name)