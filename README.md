Обнови файл README.md в проекте, сделав его максимально дружелюбным и подробным. 

Используй следующий Markdown-текст:

# 🛡️ 2D Armor & Ballistics Simulator (v16)

> 🤖 **Fun Fact:** This entire project was created in collaboration with Artificial Intelligence! It started as an experimental ballistics concept and evolved into a fully functional 2D physical simulator.

Welcome to the **2D Armor & Ballistics Simulator**! This tool simulates real-world terminal ballistics, armor penetration mechanics, dynamic ERA behavior, and secondary spalling damage inside a tank compartment.

---

## ✨ Features
- 🚀 **Realistic Shell Types:** APFSDS ("Lom"), APCBC, APCR, and HEAT rounds.
- 🛡️️ **Advanced Armor & Defense:** Variable plate angles (up to 63°+), RHA thickness up to 1000mm, and functional ERA modules (**Kontakt-5**, **Relikt**, **Duplet**).
- 💥 **Pymunk Physical Spalling:** Dynamic secondary fragments with penetration, energy loss, overpenetration, and internal crew damage modeling.
- 👨‍✈️ **Crew & Module Management:** Scalable crew size, interactive module positioning, and damage tracking.
- ⏱️️ **Time Control:** Real-time physics calculation with fixed-step Slow-Motion mode ($0.1\text{x}$ – $1.0\text{x}$).

---

## 🤝 Open for Community & Modding!

Since this project was built alongside AI, it has huge potential for further community upgrades and modernization! 

If you are a developer, gamer, or physics enthusiast, **you are super welcome to fork this repository, tweak the physics, add new features, or refactor the code!**

### 💡 Ideas for modernization:
- 🎨 **Visuals & UI:** Better telemetry graphs, hit-cam closeups, or custom tank layouts.
- 🧱 **New Armor Types:** Composite armor layers, rubber spacers, or slat armor.
- 💣 **Ammunition & Explosions:** Tandem-charge HEAT warheads, HE fragmentation, and ricochet trajectories.
- ⚡ **Performance:** Further Pymunk particle optimizations.

---

## 🛠️ How to Run Locally

### Requirements
- Python 3.9+
- Pygame
- Pymunk

### Quick Start
```bash
# Clone the repository
git clone [https://github.com/YOUR_USERNAME/ArmorSim_v16.git](https://github.com/YOUR_USERNAME/ArmorSim_v16.git)

# Install dependencies
pip install -r requirements.txt

# Run the simulator
python main.py
