# VETOR E12 COMPLETO (10R A 10M)
R_LIST = [
    10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
    100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
    1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700, 5600, 6800, 8200,
    10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
    100000, 120000, 150000, 180000, 220000, 270000, 330000, 390000, 470000, 560000, 680000, 820000,
    1000000, 1200000, 1500000, 1800000, 2200000, 2700000, 3300000, 3900000, 4700000, 5600000, 6800000, 8200000,
    10000000
]

def formatar(v):
    if v >= 1e6: return f"{v/1e6:g}M"
    if v >= 1e3: return f"{v/1e3:g}k"
    return f"{v:g}"

def calcular():
    print("-" * 30)
    modo = input("Modo: Inversor [i] (R1/R2) ou Não Inversor [n] (1+R1/R2)? ").lower()
    
    if modo not in ['i', 'n']:
        print("Erro: Escolha 'i' ou 'n'.")
        return

    try:
        # abs() garante que o valor é tratado em módulo
        alvo = abs(float(input("Introduza o valor alvo: ").replace(',', '.')))
        
        if modo == 'n' and alvo < 1:
            print("Aviso: Ganho Não Inversor é sempre >= 1. O resultado será o mais próximo possível.")
    except ValueError:
        print("Erro: Entrada numérica inválida.")
        return

    resultados_unicos = {}

    for r1 in R_LIST:
        for r2 in R_LIST:
            # Seleção da fórmula baseada no modo
            valor_calc = (r1 / r2) if modo == 'i' else (1 + r1 / r2)
            
            diferenca = valor_calc - alvo
            erro_abs = abs(diferenca)
            chave = round(valor_calc, 6)
            
            if chave not in resultados_unicos or erro_abs < resultados_unicos[chave][0]:
                resultados_unicos[chave] = (erro_abs, r1, r2, valor_calc, diferenca)

    # Ordenar por proximidade ao alvo
    ordenados = sorted(resultados_unicos.values(), key=lambda x: x[0])

    titulo = "R1 / R2" if modo == 'i' else "1 + R1 / R2"
    print(f"\n--- Top 5 para {titulo} = {alvo} ---")
    print(f"{'Pos.':<5} | {'R1':<8} | {'R2':<8} | {'Resultado':<10} | {'Diferença':<12}")
    print("-" * 55)

    for i, (erro, r1, r2, val, diff) in enumerate(ordenados[:5]):
        sinal = "+" if diff > 0 else ""
        r1_s = formatar(r1)
        r2_s = formatar(r2)
        print(f"{i+1:>2}º    | {r1_s:<8} | {r2_s:<8} | {val:<10.5f} | {sinal}{diff:.5f}")

if __name__ == "__main__":
    calcular()