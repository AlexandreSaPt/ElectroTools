def solve_voltage_divider():
    # Lista de resistências fornecida
    R_LIST = [
        10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
        100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
        1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700, 5600, 6800, 8200,
        10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
        100000, 120000, 150000, 180000, 220000, 270000, 330000, 390000, 470000, 560000, 680000, 820000,
        1000000, 1200000, 1500000, 1800000, 2200000, 2700000, 3300000, 3900000, 4700000, 5600000, 6800000, 8200000,
        10000000
    ]

    try:
        vcc = float(input("Vcc (Alimentação): "))
        vout_target = float(input("Vout (Pretendido): "))
    except ValueError:
        print("Erro: Insira valores numéricos.")
        return

    results = []
    seen_ratios = set()

    for r1 in R_LIST:
        for r2 in R_LIST:
            # Razão única (evita 10/20 ser diferente de 100/200)
            ratio = r2 / (r1 + r2)
            ratio_key = round(ratio, 8)

            if ratio_key not in seen_ratios:
                vout_calc = ratio * vcc
                diff = vout_calc - vout_target
                abs_error = abs(diff)
                rel_error = (abs_error / vout_target) * 100
                
                results.append({
                    'r1': r1,
                    'r2': r2,
                    'vout': vout_calc,
                    'diff': diff,
                    'abs_error': abs_error,
                    'rel_error': rel_error
                })
                seen_ratios.add(ratio_key)

    # Ordenar pelo erro absoluto
    results.sort(key=lambda x: x['abs_error'])

    # Título e Tabela
    print(f"\nTop 5 combinações para Vout = {vout_target}V (Vcc = {vcc}V)")
    print("-" * 75)
    print(f"{'Pos.':<6} | {'R1':<10} | {'R2':<10} | {'Resultado':<11} | {'Diferença':<12} | {'Erro Rel.'}")
    print("-" * 75)

    for i, res in enumerate(results[:5], 1):
        pos = f"{i}º"
        diff_str = f"{res['diff']:+.5f}"
        print(f"{pos:<6} | {res['r1']:<10g} | {res['r2']:<10g} | {res['vout']:<11.5f} | {diff_str:<12} | {res['rel_error']:.2f}%")

if __name__ == "__main__":
    solve_voltage_divider()