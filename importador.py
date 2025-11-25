import pandas as pd
import pymysql
import sys

#  CONFIGURACIÓN 
NOMBRE_EXCEL = '0611.xlsx'  
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '$Adb4242', 
    'database': 'mercadito_o'
}

def buscar_columna(df, posibles_nombres):
    
    columnas_reales = [c.lower().strip() for c in df.columns]
    for opcion in posibles_nombres:
        if opcion.lower().strip() in columnas_reales:
           
            indice = columnas_reales.index(opcion.lower().strip())
            return df.columns[indice]
    return None

def migrar_datos():
    print(f" Leyendo el archivo: {NOMBRE_EXCEL}...")
    
    try:
        
        df = pd.read_excel(NOMBRE_EXCEL, dtype=str)
        
       
        df.columns = [c.strip() for c in df.columns]
        print(f"   Columnas encontradas: {list(df.columns)}")
        
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return

    print(" Conectando a MySQL...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Exception as e:
        print(f" Error conectando a BBDD: {e}")
        return

    print(" Insertando productos...")
    productos_nuevos = 0
    errores = 0

   
    col_sku = buscar_columna(df, ['codigo', 'código', 'sku', 'cod'])
    col_nombre = buscar_columna(df, ['producto', 'nombre', 'descripcion', 'descripción'])
    col_costo = buscar_columna(df, ['p.costo', 'costo', 'precio costo', 'p costo'])
    col_precio = buscar_columna(df, ['p.venta', 'precio', 'precio venta', 'p venta'])
    col_cat = buscar_columna(df, ['departamento', 'categoria', 'categoría'])
    col_tipo = buscar_columna(df, ['tipo de venta', 'tipo', 'unidad', 'medida'])

   
    if not col_sku or not col_nombre:
        print(" ERROR CRÍTICO: No pude encontrar la columna de 'Código' o 'Producto'.")
        print(f"   Busqué: código/sku y producto/nombre")
        print(f"   Encontré en tu Excel: {list(df.columns)}")
        return

    print(f"   -> Usando columna '{col_sku}' para el SKU")
    print(f"   -> Usando columna '{col_nombre}' para el Nombre")

    for index, row in df.iterrows():
        try:
            
            sku = str(row[col_sku]).strip()
            if sku == 'nan' or sku == '': continue # Saltar filas vacías

            
            nombre = str(row[col_nombre]).strip()

           
            try:
                costo_raw = str(row[col_costo]).replace('$', '').replace(',', '') if col_costo else '0'
                costo = float(costo_raw)
            except: costo = 0.0

           
            try:
                precio_raw = str(row[col_precio]).replace('$', '').replace(',', '') if col_precio else '0'
                precio = float(precio_raw)
            except: precio = 0.0

            
            categoria = str(row[col_cat]).strip() if col_cat else 'General'

           
            tipo_raw = str(row[col_tipo]).lower() if col_tipo else 'unidad'
            tipo_final = 'Granel' if 'granel' in tipo_raw else 'Unidad'

           
            sql = """
                INSERT INTO productos (sku, nombre, costo, precio, categoria, tipo_venta)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nombre=%s, costo=%s, precio=%s, categoria=%s, tipo_venta=%s
            """
            val = (sku, nombre, costo, precio, categoria, tipo_final,
                   nombre, costo, precio, categoria, tipo_final)
            
            cursor.execute(sql, val)
            productos_nuevos += 1

        except Exception as err:
            print(f"Error en fila {index}: {err}")
            errores += 1

    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "="*40)
    print(f" IMPORTACIÓN FINALIZADA")
    print(f"   Procesados: {productos_nuevos}")
    print(f"   Errores: {errores}")
    print("="*40)

if __name__ == '__main__':
    migrar_datos()