#!/usr/bin/env python3
"""
Serveur pour "Analyse de Graphiques Scientifiques"
Installation : pip3 install flask anthropic gunicorn
Lancement    : python3 server.py   →   http://localhost:5000

Variable d'environnement optionnelle :
  ANTHROPIC_API_KEY  →  si définie, les élèves n'ont pas besoin de saisir leur clé
"""
from flask import Flask, request, jsonify, send_from_directory
import json, os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Clé API côté serveur (optionnelle — définie dans les variables d'environnement Render)
SERVER_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '').strip()


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/api/status')
def status():
    """Indique au frontend si une clé API est configurée côté serveur."""
    return jsonify({'server_key': bool(SERVER_API_KEY)})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data              = request.json
        student_text      = data.get('student_text', '').strip()
        exercise_context  = data.get('exercise_context', '')
        matiere           = data.get('matiere', 'svt').lower()
        iteration         = data.get('iteration', 1)
        previous_feedback = data.get('previous_feedback', None)

        # Priorité : clé serveur (variable d'env) > clé saisie par l'élève
        api_key = SERVER_API_KEY or data.get('api_key', '').strip()

        if not api_key:
            return jsonify({'error': 'Clé API Anthropic manquante. Renseignez-la dans ⚙ Paramètres.'}), 400
        if len(student_text) < 10:
            return jsonify({'error': 'Réponse trop courte. Rédigez une analyse complète.'}), 400

        try:
            import anthropic as ant
            client = ant.Anthropic(api_key=api_key)
        except ImportError:
            return jsonify({'error': 'Module anthropic non installé. Lancez : pip3 install anthropic'}), 500

        # ── Critères différenciés selon la matière ──────────────────────
        if 'physique' in matiere or 'physic' in matiere:
            discipline = "Physique-Chimie"
            criteres = """CRITÈRES D'ÉVALUATION (Physique-Chimie) :
1. L'élève RÉPOND À LA QUESTION POSÉE — pas juste une description de la courbe
2. Il utilise les données du graphique pour appuyer son explication (1 à 2 valeurs suffisent)
3. Il identifie correctement la relation de CAUSE À EFFET demandée
4. Il mobilise un principe, une loi ou un concept physique/chimique pertinent
5. Les unités sont présentes et correctes
NOTE : La "phrase_amelioree" doit être une réponse argumentée à la question, s'appuyant sur les données. Ce n'est PAS une simple description de courbe."""
        else:
            discipline = "SVT"
            criteres = """CRITÈRES D'ÉVALUATION (SVT) :
1. L'élève RÉPOND À LA QUESTION POSÉE — explication biologique, mécanisme, cause
2. Il décrit la tendance générale de la courbe (augmentation, diminution, plateau)
3. Il cite 1 ou 2 valeurs clés avec leurs unités (inutile de citer tous les points)
4. Il propose une explication biologique cohérente (le "pourquoi")
5. Il utilise un vocabulaire scientifique approprié
NOTE IMPORTANTE : Ne pas exiger une description chiffrée exhaustive. Une analyse générale
avec 1-2 valeurs caractéristiques suffit largement. Valoriser l'explication biologique."""

        # ── Contexte de la tentative précédente ─────────────────────────
        prev_ctx = ""
        if previous_feedback and iteration > 1:
            prev_ctx = f"""
CONTEXTE : Tentative n°{iteration}. Score précédent : {previous_feedback.get('score', 0)}/100.
Phrase modèle précédemment proposée :
"{previous_feedback.get('phrase_amelioree', '')}"
Signale les progrès réalisés dans le message d'encouragement."""

        prompt = f"""Tu es un professeur de {discipline} bienveillant et pédagogue,
spécialisé dans la correction d'exercices d'analyse de graphiques pour des élèves de collège.

DOCUMENT ET QUESTION :
{exercise_context}

RÉPONSE DE L'ÉLÈVE (tentative n°{iteration}) :
"{student_text}"
{prev_ctx}
{criteres}

Réponds UNIQUEMENT en JSON valide (sans texte avant ni après), format exact :

{{
  "score": <entier 0-100>,
  "niveau_global": "<Insuffisant|En progrès|Satisfaisant|Bien|Très bien|Excellent>",
  "points_positifs": ["<au moins 1 point positif>"],
  "points_ameliorer": ["<amélioration concrète 1>", "<amélioration concrète 2>"],
  "explication_score": "<1-2 phrases bienveillantes expliquant le score>",
  "phrase_amelioree": "<réponse complète et exemplaire à la question, en s'appuyant sur les données>",
  "encouragement": "<message court et chaleureux, personnalisé selon le score>"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        text = message.content[0].text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return jsonify(json.loads(text))

    except json.JSONDecodeError as e:
        return jsonify({'error': 'Erreur de format IA. Réessayez.', 'details': str(e)}), 500
    except Exception as e:
        err = str(e)
        if any(k in err.lower() for k in ['authentication', 'api_key', '401']):
            return jsonify({'error': 'Clé API invalide.'}), 401
        if 'rate_limit' in err.lower() or '429' in err:
            return jsonify({'error': 'Limite de requêtes atteinte. Patientez quelques secondes.'}), 429
        return jsonify({'error': f'Erreur : {err}'}), 500


if __name__ == '__main__':
    mode = "clé serveur active ✅" if SERVER_API_KEY else "clé à saisir dans l'app ⚙"
    print("\n" + "=" * 52)
    print("  📊  Analyse de Graphiques Scientifiques")
    print("=" * 52)
    print(f"  🌐  http://localhost:5000")
    print(f"  🔑  {mode}")
    print("=" * 52 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
