#!/bin/bash
# ─────────────────────────────────────────────────────────
#  Lanceur – Analyse de Graphiques Scientifiques
#  Usage : double-cliquez sur ce fichier ou lancez
#          bash lancer.sh  dans votre Terminal
# ─────────────────────────────────────────────────────────

echo ""
echo "=================================================="
echo "  📊  Analyse de Graphiques Scientifiques"
echo "=================================================="
echo ""
echo "→ Vérification de Python 3…"

if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 non trouvé. Installez-le depuis https://python.org"
  read -p "Appuyez sur Entrée pour fermer."
  exit 1
fi

echo "✅ Python 3 trouvé : $(python3 --version)"
echo ""
echo "→ Installation des dépendances (flask, anthropic)…"
pip3 install flask anthropic --break-system-packages -q

echo "✅ Dépendances prêtes."
echo ""
echo "→ Démarrage du serveur…"
echo "   🌐  Ouvrez votre navigateur sur : http://localhost:5000"
echo "   ⌨️   Appuyez sur Ctrl+C pour arrêter"
echo "=================================================="
echo ""

cd "$(dirname "$0")"
python3 server.py
