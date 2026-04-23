import math

# VETOR E12 COMPLETO (10R A 10M)
R_LIST = [
    1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700, 5600, 6800, 8200,
    10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
    100000, 120000, 150000, 180000, 220000, 270000, 330000, 390000, 470000, 560000, 680000, 820000,
    1000000, 1200000, 1500000, 1800000, 2200000, 2700000, 3300000, 3900000, 4700000, 5600000, 6800000, 8200000,
    10000000
]

# VETOR DE CONDENSADORES (Reduzido conforme pedido)
C_LIST = [
    1.0e-12, 1.5e-12, 2.2e-12, 3.3e-12, 4.7e-12, 6.8e-12,
    10e-12, 15e-12, 22e-12, 33e-12, 47e-12, 68e-12,
    100e-12, 150e-12, 220e-12, 330e-12, 470e-12, 680e-12,
    1.0e-9, 1.5e-9, 2.2e-9, 3.3e-9, 4.7e-9, 6.8e-9,
    10e-9, 15e-9, 22e-9, 33e-9, 47e-9, 68e-9,
    100e-9, 150e-9, 220e-9, 330e-9, 470e-9, 680e-9,
    1.0e-6, 1.5e-6, 2.2e-6, 3.3e-6, 4.7e-6, 6.8e-6,
    10e-6, 15e-6, 22e-6, 33e-6, 47e-6, 68e-6,
    100e-6, 150e-6
]

def formatar_r(v):
    if v >= 1e6: return f"{v/1e6:g}M"
    if v >= 1e3: return f"{v/1e3:g}k"
    return f"{v:g}"

def formatar_c(v):
    if v >= 1e-3: return f"{v*1e3:g}mF"
    if v >= 1e-6: return f"{v*1e6:g}uF"
    if v >= 1e-9: return f"{v*1e9:g}nF"
    return f"{v*1e12:g}pF"

def calcular_filtro():
    print("-" * 40)
    modo = input("Tipo de Filtro: Passa-Baixo [b] ou Passa-Alto [a]? ").lower()
    
    if modo not in ['b', 'a']:
        print("Erro: Escolha 'b' ou 'a'.")
        return

    try:
        f_alvo = abs(float(input("Introduza a frequência de corte alvo (Hz): ").replace(',', '.')))
        if f_alvo == 0:
            print("Erro: Frequência não pode ser zero.")
            return
    except ValueError:
        print("Erro: Entrada numérica inválida.")
        return

    resultados_unicos = {}

    for r in R_LIST:
        for c in C_LIST:
            # f_corte = 1 / (2 * pi * R * C)
            f_calc = 1 / (2 * math.pi * r * c)
            
            diff_abs = abs(f_calc - f_alvo)
            erro_relativo = (diff_abs / f_alvo) * 100
            
            # Usamos a frequência arredondada como chave para evitar redundâncias irrelevantes
            chave = round(f_calc, 4)
            
            if chave not in resultados_unicos or diff_abs < resultados_unicos[chave][0]:
                # Guardar: (erro_abs, r, c, f_calc, erro_relativo)
                resultados_unicos[chave] = (diff_abs, r, c, f_calc, erro_relativo)

    # Ordenar por erro absoluto (mais próximo do alvo primeiro)
    ordenados = sorted(resultados_unicos.values(), key=lambda x: x[0])

    tipo_s = "Passa-Baixo" if modo == 'b' else "Passa-Alto"
    print(f"\n--- Top 5 para Filtro {tipo_s} (Alvo: {f_alvo} Hz) ---")
    print(f"{'Pos.':<4} | {'R':<8} | {'C':<8} | {'F. Corte':<12} | {'Erro Rel.':<10}")
    print("-" * 60)

    for i, (erro_abs, r, c, val, erro_rel) in enumerate(ordenados[:5]):
        r_s = formatar_r(r)
        c_s = formatar_c(c)
        print(f"{i+1:>2}º   | {r_s:<8} | {c_s:<8} | {val:<12.2f} | {erro_rel:>8.2f}%")

if __name__ == "__main__":
    calcular_filtro()