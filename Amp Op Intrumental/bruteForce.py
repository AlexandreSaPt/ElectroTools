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


bestScore = 0
VD_winners = [-1, 0, 0, 0]

def calc_ganho(r0, r1, r2, rf):
   return (r2 / r1) * (1 + (2*rf / r0))

def calculations(r0, r1, r2, rf, bestScore, VD_winners):
  ganho = calc_ganho(r0, r1, r2, rf) # (V_bias - V_in)

  amp = ganho * (Vin_max - Vin_min)
  constrain_1 = amp <= Amp_max
  

  if (constrain_1):
    if amp > bestScore :
        bestScore = amp
        VD_winners = [r0, r1, r2, rf]

  return [bestScore, VD_winners]



#LEXY VERSION
#AKA BRUTE FORCE
R_LIST = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
1000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000, 68000, 82000,
100000, 120000, 150000, 180000, 220000, 270000, 330000, 390000, 470000, 560000, 680000, 820000,
1000000, 12000000, 15000000, 18000000, 22000000, 27000000, 33000000, 39000000, 47000000, 56000000, 68000000, 82000000,
10000000]

R_LIST = list(filter(lambda r: r <= 33000, R_LIST))
R_LIST = list(filter(lambda r: r >= 0, R_LIST))

R_MAX = 10000 #Ohms
R_STEP = 100

V_BIAS_MAX = 24 #V

print("Iniciando simulação...")

for r0 in R_LIST:
  print(".", end='', flush=True)
  for r1 in R_LIST:
    for r2 in R_LIST:
        #r2 = r1
        for rf in R_LIST:
            helper = calculations(r0, r1, r2, rf, bestScore, VD_winners)
            bestScore = helper[0]
            VD_winners = helper[1]

print("\n\n--------------Resultados--------------")


print("\nParametros da Simulação:")
print(f"I_extensometro = {I} A")
print(f"R_min = {R_min} Ohms")
print(f"R_max = {R_max} Ohms")
print(f"Vcc = {Vcc} V")
print(f"Amp_max = {Amp_max} V")
print()
print(f"Vin_min = {Vin_min} V")
print(f"Vin_max = {Vin_max} V")
print("\n\n")


print(f"Melhor amplitude encontrada: {bestScore}")
print(f"Configuração:")
print(f"\t r0 - {VD_winners[0]}")
print(f"\t r1 - {VD_winners[1]}")
print(f"\t r2 - {VD_winners[2]}")
print(f"\t rf - {VD_winners[3]}")

print("\n")

print(f"Se Vb = {Vin_max}:")
ganhoFinal = calc_ganho(VD_winners[0], VD_winners[1], VD_winners[2], VD_winners[3])
print(f"V Mínimo Output - {ganhoFinal * (Vin_max - Vin_max)}")
print(f"V máximo Output - {ganhoFinal* (Vin_max - Vin_min)}")
print(f"Ganho Ampop: {ganhoFinal}")
