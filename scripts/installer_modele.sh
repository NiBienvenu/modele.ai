#!/usr/bin/env bash
# Installe un modèle .zip (sortie Kaggle/Colab) dans la plateforme Docker.
#
#   ./scripts/installer_modele.sh ../outputs/modele_zero_fr_rn.zip
#   ./scripts/installer_modele.sh ../outputs/modele_un_fr_rn.zip
#
# Étapes :
#   0. vérifie que Docker est allumé (sinon l'allume) et que le conteneur existe (sinon le crée)
#   1. décompresse le zip dans models/local/<nom>  (ex: modele-zero-fr-rn)
#   2. ajoute prompt_style.yaml
#   3. convertit au format LitGPT (lit_model.pth) dans le conteneur
#   4. met à jour MODEL_NAME et MODEL_PATH dans .env
#   5. redémarre le conteneur et affiche les adresses (machine + réseau)
set -euo pipefail

ZIP="${1:?Usage: $0 chemin/vers/modele_xxx.zip}"
[ -f "$ZIP" ] || { echo "Fichier introuvable : $ZIP"; exit 1; }
ZIP="$(realpath "$ZIP")"

cd "$(dirname "$0")/.."   # racine litgpt/

# ---- 0. Docker -----------------------------------------------------------------
echo "==> Vérification de Docker"
if ! command -v docker >/dev/null; then
  echo "Docker n'est pas installé. Installe-le d'abord : https://docs.docker.com/engine/install/"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "    Docker est éteint, démarrage (mot de passe sudo possible)..."
  sudo systemctl start docker
  for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 1; done
  docker info >/dev/null 2>&1 || { echo "Docker ne démarre pas."; exit 1; }
fi
echo "    Docker est allumé."

mkdir -p backend/conversations && chmod a+rwx backend/conversations
if [ -z "$(docker compose ps -a -q app)" ]; then
  echo "    Le conteneur n'existe pas, création..."
  if docker image inspect "$(docker compose config --images | head -1)" >/dev/null 2>&1; then
    docker compose up -d
  else
    docker compose up -d --build   # pas d'image : on la construit depuis le code
  fi
else
  docker compose up -d   # le rallume s'il est arrêté
fi

# ---- 1-2. Décompression -----------------------------------------------------------
NOM="$(basename "$ZIP" .zip | tr '_' '-')"
DOSSIER="models/local/$NOM"

echo "==> Modèle : $NOM"
if [ -d "$DOSSIER" ]; then
  echo "    Le dossier $DOSSIER existe déjà, il sera remplacé."
  rm -rf "$DOSSIER"
fi
mkdir -p "$DOSSIER"

echo "==> Décompression"
unzip -q -j "$ZIP" -d "$DOSSIER"   # -j : ignore les sous-dossiers du zip
for f in config.json model.safetensors tokenizer.json; do
  [ -f "$DOSSIER/$f" ] || { echo "Il manque $f dans le zip"; exit 1; }
done

echo "class_path: inference.prompt_styles.FrRnChat" > "$DOSSIER/prompt_style.yaml"
chmod -R a+rwX "$DOSSIER"

# ---- 3. Conversion ----------------------------------------------------------------
echo "==> Conversion LitGPT (dans le conteneur)"
# On envoie la version locale du script (celle de l'image peut être ancienne)
docker compose exec -T app python - "$DOSSIER" < scripts/convert_local_model.py

# ---- 4. .env ----------------------------------------------------------------------
echo "==> Mise à jour de .env"
cp .env .env.bak
sed -i "s|^MODEL_NAME=.*|MODEL_NAME=local/$NOM|" .env
sed -i "s|^MODEL_PATH=.*|MODEL_PATH=$DOSSIER|" .env
grep -E '^MODEL_(NAME|PATH)=' .env

# ---- 5. Redémarrage -----------------------------------------------------------------
echo "==> Redémarrage"
docker compose up -d --force-recreate

PORT="$(grep -E '^FRONTEND_PORT=' .env | cut -d= -f2)"; PORT="${PORT:-5555}"
IP="$(hostname -I | awk '{print $1}')"
echo
echo "OK. Teste le modèle :"
echo "   sur cette machine  : http://localhost:$PORT"
echo "   sur le réseau      : http://$IP:$PORT   (téléphone, autre PC...)"
if command -v ufw >/dev/null && sudo -n ufw status 2>/dev/null | grep -q "Status: active"; then
  echo "   Pare-feu actif : si le réseau ne marche pas, lance  sudo ufw allow $PORT/tcp"
fi
echo "(ancien .env sauvé dans .env.bak)"
