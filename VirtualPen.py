#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 17:19:27 2020

@author: shoumik
"""


# import the necessary packages
from color_labeler import ColorLabeler
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import tkinter as tk
import threading  # Importar el módulo threading

# Configurar la ventana de Tkinter
root = tk.Tk()
root.title("Virtual Pen")
root.geometry("300x200")  # Cambiar el tamaño de la ventana a 300x200

# Inicializar la variable que controla si el video está en ejecución
running = False
pts = deque(maxlen=1024)  # Inicializar puntos
line_color = (0, 0, 255)  # Color de línea por defecto (rojo)

# Configurar argumentos de la línea de comandos
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=1024, help="max buffer size")
args = vars(ap.parse_args())

# Definir límites de color en el espacio de color HSV
greenLower = (63, 114, 120)
greenUpper = (100, 255, 255)

# Inicializar el objeto ColorLabeler
cl = ColorLabeler()

def start_stream():
    global running
    running = True
    # Iniciar el hilo para la captura de video
    thread = threading.Thread(target=run_video_stream)
    thread.start()

def set_red():
    global line_color
    line_color = (0, 0, 255)  # Rojo

def set_blue():
    global line_color
    line_color = (255, 0, 0)  # Azul

def set_green():
    global line_color
    line_color = (0, 255, 0)  # Verde

def close_app():
    global running
    running = False
    root.quit()  # Cerrar la ventana de tkinter

def run_video_stream():
    global running
    # Si no se proporciona un archivo de video, iniciar la cámara
    if not args.get("video", False):
        vs = VideoStream(src=0).start()
    else:
        vs = cv2.VideoCapture(args["video"])
        
    # Permitir que la cámara o el archivo de video se calienten
    time.sleep(2.0)

    while running:
        # Captura y procesamiento del video
        frame = vs.read()
        frame = cv2.flip(frame, 1)

        # Redimensionar el marco, difuminarlo y convertirlo al espacio de color HSV
        frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Construir una máscara para el color "verde"
        mask = cv2.inRange(hsv, greenLower, greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Encontrar contornos en la máscara
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None

        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        
        # Actualizar la cola de puntos
        pts.appendleft(center)

        # Dibujar los puntos en el marco
        for i in range(1, len(pts)):
            if pts[i - 1] is None or pts[i] is None:
                continue
            thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
            cv2.line(frame, pts[i - 1], pts[i], line_color, thickness)  # Usar el color actual de la línea

        # Mostrar el marco en la ventana
        cv2.imshow("My Virtual Pen", frame)
        key = cv2.waitKey(1) & 0xFF

        # Si se presiona la tecla 'q', salir del bucle
        if key == ord("q"):
            break

    # Si no se utiliza un archivo de video, detener la transmisión de la cámara
    if not args.get("video", False):
        vs.stop()
    else:
        vs.release()

    # Cerrar todas las ventanas de OpenCV
    cv2.destroyAllWindows()

# Crear botones de la interfaz gráfica
start_button = tk.Button(root, text="Iniciar", command=start_stream)
start_button.pack(pady=10)

red_button = tk.Button(root, text="Línea Roja", command=set_red)
red_button.pack(pady=5)

blue_button = tk.Button(root, text="Línea Azul", command=set_blue)
blue_button.pack(pady=5)

green_button = tk.Button(root, text="Línea Verde", command=set_green)
green_button.pack(pady=5)

close_button = tk.Button(root, text="Cerrar", command=close_app)
close_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", close_app)

# Iniciar el bucle principal de Tkinter
root.mainloop()
