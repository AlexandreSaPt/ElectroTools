#parametros
I = 0.0005 # A
R_min = 100 # Ohms
R_max = 5000 # Ohms
Vcc = 5 #V

Amp_max = 3.3 #V

#pre cálculo
Vdrop_min = I * R_min #V
Vdrop_max = I * R_max #V

Vin_min = 5 - Vdrop_max #V
Vin_max = 5 - Vdrop_min #V


v_bias = Vin_max
amp = v_bias - Vin_min

R_LIST = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
1000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
100000, 120000, 150000, 180000, 220000, 270000, 330000, 390000, 470000, 560000, 680000, 820000,
1000000, 12000000, 15000000, 18000000, 22000000, 27000000, 33000000, 39000000, 47000000, 56000000, 68000000, 82000000,
10000000]

#bely version
def calc_ganho(rg):
   return (((49400) / (rg)) + 1)


bestScore = [0, 0] # melhor amplitude, resistencia

print("Iniciando simulação...")

for rg in R_LIST:
  outputmaximo = calc_ganho(rg)*(amp)
  if(outputmaximo < Amp_max):
    if(outputmaximo > bestScore[0]):
      bestScore[0] = outputmaximo
      bestScore[1] = rg


print("\n\n--------------Resultados--------------")

print("\nParametros da Simulação:")
print(f"I na resistencia variavel = {I} A")
print(f"R_min = {R_min} Ohms")
print(f"R_max = {R_max} Ohms")
print(f"Vcc = {Vcc} V")
print(f"Amp_max = {Amp_max} V")
print()
print(f"Vin_min = {Vin_min} V")
print(f"Vin_max = {Vin_max} V")
print("\n\n")

print(f"Melhor amplitude encontrada: {bestScore[0]:.2f}")
print(f"Melhor ganho encontrado: {bestScore[0]/amp:.2f}")

print(f"Configuração:")
print(f"\t rg - {bestScore[1]}")
print(f"\t Vbias - {v_bias:.2f}")

print("\n")

print(f"OUTPUT minimo: {(v_bias-Vin_max)*bestScore[0]/amp:.2f}")
print(f"OUTPUT maximo: {(amp)*bestScore[0]/amp:.2f}")
