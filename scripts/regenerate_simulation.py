import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Dados de 2022 (SINASC) - TFT por raça
races_data = {
    'Parda': {'tft': 2.19, 'geracao': 28.1, 'pop_2022': 97_800_000},
    'Branca': {'tft': 1.58, 'geracao': 31.4, 'pop_2022': 90_800_000},
    'Preta': {'tft': 1.77, 'geracao': 27.2, 'pop_2022': 20_900_000},
    'Amarela': {'tft': 1.51, 'geracao': 33.2, 'pop_2022': 2_400_000},
    'Indígena': {'tft': 2.64, 'geracao': 26.5, 'pop_2022': 1_700_000},
}

rcParams['font.family'] = 'sans-serif'
rcParams['font.size'] = 11

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

colors = {
    'Parda': '#E75C9F',
    'Branca': '#F2A900',
    'Preta': '#1F7C40',
    'Amarela': '#1F7C40',  # verde escuro
    'Indígena': '#0066CC',
}

years = np.array([0, 25, 50, 75, 100, 125, 150, 175, 200])

# ============ ESCALA LOGARÍTMICA (original) ============
for race, data in races_data.items():
    tft = data['tft']
    generation = data['geracao']
    r = tft / 2  # taxa líquida de reprodução

    # População no início normalizada para log
    p0_log = 100
    populations_log = [p0_log * (r ** (year / generation)) for year in years]

    ax1.semilogy(years, populations_log, marker='o', linewidth=2.5, label=race, color=colors.get(race, '#000'))

ax1.set_xlabel('Anos a partir de 2022', fontsize=12, fontweight='bold')
ax1.set_ylabel('População (milhões, escala log)', fontsize=12, fontweight='bold')
ax1.set_title('ESCALA LOGARÍTMICA (original)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, which='both')
ax1.legend(loc='best', fontsize=11)
ax1.set_ylim([0.1, 1000])

# ============ ESCALA LINEAR (corrigida, proporção real) ============
for race, data in races_data.items():
    tft = data['tft']
    generation = data['geracao']
    r = tft / 2  # taxa líquida de reprodução

    # Usar população REAL de 2022 como base
    p0_real = data['pop_2022'] / 1_000_000  # em milhões
    populations_real = [p0_real * (r ** (year / generation)) for year in years]

    ax2.plot(years, populations_real, marker='o', linewidth=2.5, label=race, color=colors.get(race, '#000'))

ax2.set_xlabel('Anos a partir de 2022', fontsize=12, fontweight='bold')
ax2.set_ylabel('População (milhões)', fontsize=12, fontweight='bold')
ax2.set_title('ESCALA LINEAR (ajustado ao tamanho real)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(loc='best', fontsize=11)
ax2.set_ylim([0, 120])

plt.suptitle('Simulação de 200 anos — população por raça/cor, mantido o TFT de 2022\nTaxa líquida de reprodução = TFT/2 | Geração = idade média da mãe (SINASC 2022)',
             fontsize=13, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig('/Users/polux/Projetos/rodado/fertilidade_raca_simulacao_200anos_linear.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico com escala linear salvo como 'fertilidade_raca_simulacao_200anos_linear.png'")

# Mostrar valores ao ano 200
print("\n=== Projeção ao ano 200 ===")
print("Raça        | Pop 2022 (Mi) | Pop 2222 (Mi) | Mudança (%) | Fold")
print("-" * 70)
for race, data in races_data.items():
    tft = data['tft']
    generation = data['geracao']
    r = tft / 2
    p0 = data['pop_2022'] / 1_000_000
    p200 = p0 * (r ** (200 / generation))
    change = ((p200 - p0) / p0) * 100
    fold = p200 / p0
    print(f"{race:12} | {p0:13.1f} | {p200:13.1f} | {change:10.1f}% | {fold:5.2f}x")
