#!/bin/bash

# Script para executar detecção YOLO em fullscreen
# Uso: detection_fullscreen.sh <nome_do_objeto>

# Verifica se foi fornecido um argumento para o objeto alvo
if [ $# -eq 0 ]; then
    echo "Uso: $0 <nome_do_objeto>"
    echo "Exemplo: $0 router_simples_vermelho"
    exit 1
fi

TARGET_OBJECT=$1

# 1. Fecha janelas YOLO anteriores (opcional)
pkill -f yolo_detect.py

# 2. Aguarda 1s
sleep 1

# 3. Executa o script de detecção com caminhos absolutos
cd "$HOME/netmaster_menu/object_detection"

# 3.1. Ativa o ambiente virtual
source venv/bin/activate

python yolo_detect.py \
    --model="/home/joaorebolo2/netmaster_menu/object_detection/best_ncnn_model" \
    --source=picamera0 \
    --resolution=360x480 \
    --target_object="$TARGET_OBJECT"

# 4. O programa terminou automaticamente após deteção bem-sucedida
echo "Detection script finished"

# 4.1. Desativa o ambiente virtual
deactivate

# 5. Não é necessário ajustar janela pois o programa já terminou
# Comentado pois o programa terminou automaticamente
# if command -v xdotool > /dev/null 2>&1; then
#     xdotool getactivewindow windowmove 0 0 windowsize 360 480
# else
#     echo "xdotool não encontrado - janela não será redimensionada automaticamente"
# fi
