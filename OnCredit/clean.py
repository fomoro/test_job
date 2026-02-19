import os
import shutil

def eliminar_git_folders(ruta):
    for root, dirs, files in os.walk(ruta, topdown=False):
        for nombre in dirs:
            if nombre == '.git':
                ruta_completa = os.path.join(root, nombre)
                print(f"Eliminando: {ruta_completa}")
                shutil.rmtree(ruta_completa)
        for nombre in files:
            if nombre == '.git':
                ruta_completa = os.path.join(root, nombre)
                print(f"Eliminando: {ruta_completa}")
                os.remove(ruta_completa)

if __name__ == "__main__":
    ruta_base = 'jobs'  # Cambia esto a la ruta de tu carpeta 'jobs'
    eliminar_git_folders(ruta_base)
    print("Limpieza completada.")