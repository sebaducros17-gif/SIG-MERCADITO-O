# Sistema de Gestión (SIG) - Mercadito "O"

**Asignatura:** ICN292 - Sistemas de Información para la Gestión  
**Entrega:** Trabajo Final (2025/02)  
**Descripción:** Sistema POS (Punto de Venta) y Gestión de Inventario con arquitectura relacional, desarrollado en Python y MySQL.

---

## Estructura del Proyecto

El entregable se organiza de la siguiente manera:

* **`Base_de_Datos/`**: Contiene el script SQL para la creación de tablas y usuarios.
* **`Codigo_Fuente/`**: Contiene el script principal (`final_mercadito.py`), el importador de datos (`importador.py`) y el archivo Excel base.
* **`Ejecutable_Portatil/`**: Versión compilada (.exe) para ejecución directa en Windows sin instalación de Python.
* **`requirements.txt`**: Lista de dependencias necesarias.

---

## Requisitos de Instalación (Para ejecutar código fuente)

Si desea ejecutar el sistema desde el código fuente (Python), asegúrese de tener instalado:

1.  **Python 3.8+**
2.  **Servidor MySQL** (XAMPP o MySQL Workbench) corriendo en el puerto 3306.
3.  **Librerías de Python**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Si no usa el archivo, instale manual: `pip install pymysql PyQt5 matplotlib reportlab cryptography pandas openpyxl`)*

---

##  Guía de Configuración (Paso a Paso)

Para un despliegue limpio, siga este orden:

### Paso 1: Crear la Base de Datos
1.  Abra su gestor de base de datos (Workbench).
2.  Abra el archivo **"Mercadit_O.sql"**.
3.  Ejecute todo el script.
    * *Esto creará la base de datos "mercadito_o", las tablas relacionales y el usuario administrador.*

### Paso 2: Cargar el Inventario Inicial
El sistema inicia vacío. Para cargar los productos del cliente:
1.  Abra una terminal en la carpeta **`Codigo_Fuente`**.
2.  Asegúrese de que el archivo `0611.xlsx` (Excel de productos) esté en esa misma carpeta.
3.  Ejecute el importador:
    ```bash
    python importador.py
    ```
    * *Este script leerá el Excel, creará las categorías dinámicamente y vinculará los productos.*

### Paso 3: Verificar Conexión
1.  Abra el archivo `final_mercadito.py` con un editor de texto.
2.  Verifique la configuración en las primeras líneas:
    ```python
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  #Ingresar su constraseña de MySQL
        'database': 'mercadito_o'
    }
    ```

---

## Ejecución del Sistema

### Opción A: Desde Código Fuente
Estando en la carpeta `Codigo_Fuente`, ejecute:
```bash
python final_mercadito.py