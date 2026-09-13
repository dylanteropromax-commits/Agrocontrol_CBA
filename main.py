import json
from datetime import datetime
from pathlib import Path

# --- 1. PERSISTENCIA Y CONFIGURACIÓN JSON ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True) 

archivos = {
    "productos": DATA_DIR / "productos.json",
    "lotes": DATA_DIR / "lotes.json",
    "movimientos": DATA_DIR / "movimientos.json",
    "ventas": DATA_DIR / "ventas.json"
}

datos = {
    "productos": [], "lotes": [], "movimientos": [], "ventas": []
}

def cargar_datos():
    for clave, ruta in archivos.items():
        if ruta.exists(): 
            with open(ruta, "r", encoding="utf-8") as f:
                datos[clave] = json.load(f)

def guardar_datos():
    for clave, ruta in archivos.items():
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos[clave], f, indent=4)


# --- 2. FUNCIONES AUXILIARES ---
def fmt_dinero(valor):
    return f"${int(valor)}"

def validar_fecha(fecha_str):
    try:
        datetime.strptime(fecha_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def generar_id(coleccion, prefijo):
    if not datos[coleccion]:
        return f"{prefijo}0001"
    ultimo_id = datos[coleccion][-1]["id"]
    numero = int(ultimo_id[1:]) + 1
    return f"{prefijo}{numero:04d}"

def calcular_stock(codigo):
    stock = 0
    for mov in datos["movimientos"]:
        if mov["producto_codigo"] == codigo:
            if mov["tipo"] == "ENTRADA":
                stock += mov["cantidad"]
            elif mov["tipo"] in ["SALIDA", "VENTA"]:
                stock -= mov["cantidad"]
    return stock


# --- 3. MÓDULOS DE NEGOCIO ---

# Productos
def gestion_productos():
    print("\n--- REGISTRAR NUEVO PRODUCTO ---")
    codigo = input("Código del producto (Ej: P001): ").strip().upper()
    if any(p["codigo"] == codigo for p in datos["productos"]):
        print("Error: Ya existe un producto con este código.")
        return
    nombre = input("Nombre del producto: ").strip()
    categoria = input("Categoría: ").strip()
    unidad = input("Unidad de medida: ").strip()
    
    while True:
        try:
            precio = float(input("Precio de venta: "))
            stock_min = int(input("Stock mínimo para alertas: "))
            if precio > 0 and stock_min >= 0: break
            print("Error: Precio > 0 y stock mínimo >= 0.")
        except ValueError:
            print("Error: Ingrese valores numéricos.")

    producto = {
        "codigo": codigo, "nombre": nombre, "categoria": categoria,
        "unidad": unidad, "precio": precio, "stock_minimo": stock_min, "activo": True
    }
    datos["productos"].append(producto)
    guardar_datos() 
    print(f"Producto registrado con éxito.")

def listar_productos():
    print("\n--- LISTA DE PRODUCTOS ACTIVOS ---")
    print(f"{'CÓDIGO':<8} | {'NOMBRE':<20} | {'PRECIO':<10} | {'STOCK MIN':<10} | {'STOCK ACTUAL':<12}")
    print("-" * 73)
    for p in datos["productos"]:
        if p["activo"]:
            stock_actual = calcular_stock(p["codigo"])
            print(f"{p['codigo']:<8} | {p['nombre']:<20} | {fmt_dinero(p['precio']):<10} | {p['stock_minimo']:<10} | {stock_actual:<12}")
    print("-" * 73)

# Lotes
def registrar_lote():
    print("\n--- REGISTRAR LOTE PRODUCTIVO ---")
    cod_prod = input("Código del producto a cultivar (Ej: P001): ").strip().upper()
    if not any(p["codigo"] == cod_prod and p["activo"] for p in datos["productos"]):
        print("Error: El producto no existe o está inactivo.")
        return
        
    id_lote = input("ID del Lote (Ej: L001): ").strip().upper()
    if any(l["id_lote"] == id_lote for l in datos["lotes"]):
        print("Error: Ya existe un lote con este ID.")
        return
        
    fecha = input("Fecha de siembra (dd/mm/yyyy): ").strip()
    if not validar_fecha(fecha):
        print("Error: Formato de fecha incorrecto.")
        return
    
    try:
        area = float(input("Área en m2: "))
    except ValueError:
        print("Error: Área inválida.")
        return

    lote = {
        "id_lote": id_lote, "producto_codigo": cod_prod, "fecha_siembra": fecha,
        "area_m2": area, "cantidad_producida": 0, "estado": "EN_PRODUCCION"
    }
    datos["lotes"].append(lote)
    guardar_datos()
    print("Lote registrado con éxito.")

def cosechar_lote():
    print("\n--- COSECHAR LOTE ---")
    id_lote = input("ID del lote a cosechar: ").strip().upper()
    lote = next((l for l in datos["lotes"] if l["id_lote"] == id_lote), None)
    
    if not lote:
        print("Error: El lote ingresado no existe.")
        return
    if lote["estado"] != "EN_PRODUCCION":
        print(f"Error: El lote ya fue cosechado o cancelado.")
        return

    try:
        cantidad = int(input("Cantidad producida: "))
        if cantidad <= 0:
            print("Error: La cantidad debe ser mayor a 0.")
            return
    except ValueError:
        print("Error: Ingrese un número válido.")
        return

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    lote["estado"] = "COSECHADO"
    lote["cantidad_producida"] = cantidad

    movimiento = {
        "id": generar_id("movimientos", "M"), "producto_codigo": lote["producto_codigo"],
        "tipo": "ENTRADA", "cantidad": cantidad, "motivo": f"Cosecha lote {id_lote}", "fecha": fecha_hoy
    }
    datos["movimientos"].append(movimiento)
    guardar_datos()
    print("¡Cosecha registrada! Se ha actualizado el inventario automáticamente.")


# (NUEVO PASO: MOVIMIENTOS MANUALES)
def registrar_movimiento():
    print("\n--- MOVIMIENTO MANUAL DE INVENTARIO ---")
    listar_productos()
    
    cod = input("\nCódigo del producto: ").strip().upper()
    if not any(p["codigo"] == cod and p["activo"] for p in datos["productos"]):
        print("Error: El producto no existe o está inactivo.")
        return

    tipo_op = input("Tipo de movimiento - (1) ENTRADA, (2) SALIDA: ").strip()
    if tipo_op not in ["1", "2"]:
        print("Error: Opción de movimiento no válida.")
        return

    try:
        cantidad = int(input("Cantidad: "))
        if cantidad <= 0:
            print("Error: La cantidad debe ser mayor a 0.")
            return
    except ValueError:
        print("Error: Ingrese un valor numérico válido.")
        return

    # Si es salida, validamos que haya suficiente stock (Prueba PF005)
    if tipo_op == "2":
        stock_actual = calcular_stock(cod)
        if cantidad > stock_actual:
            print(f"Error: Stock insuficiente. Stock actual: {stock_actual}, Intentó retirar: {cantidad}.")
            return
        tipo_str = "SALIDA"
    else:
        tipo_str = "ENTRADA"

    motivo = input("Motivo obligatorio del movimiento: ").strip()
    if not motivo:
        print("Error: El motivo es obligatorio.")
        return

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    
    movimiento = {
        "id": generar_id("movimientos", "M"),
        "producto_codigo": cod,
        "tipo": tipo_str,
        "cantidad": cantidad,
        "motivo": motivo,
        "fecha": fecha_hoy
    }
    
    datos["movimientos"].append(movimiento)
    guardar_datos()
    print(f"Movimiento de {tipo_str} registrado con éxito.")


# --- 4. SUBMENÚS Y MENÚ PRINCIPAL ---
def menu_productos():
    print("\n1. Registrar producto\n2. Listar productos activos")
    op = input("Opción: ")
    if op == "1": gestion_productos()
    elif op == "2": listar_productos()

def menu_lotes():
    print("\n1. Registrar lote\n2. Cosechar lote")
    op = input("Opción: ")
    if op == "1": registrar_lote()
    elif op == "2": cosechar_lote()

def menu():
    cargar_datos() 
    
    while True:
        print("\n==================== AGROCONTROL CBA ====================")
        print("1. Gestión de productos")
        print("2. Gestión de lotes productivos")
        print("3. Movimientos de inventario")
        print("4. Registrar venta (Próximo paso)")
        print("5. Consultar ventas (Próximo paso)")
        print("6. Alertas de stock (Próximo paso)")
        print("7. Reportes (Próximo paso)")
        print("8. Guardar datos")
        print("0. Salir")
        
        op = input("Seleccione una opción: ")
        
        if op == "1":
            menu_productos()
        elif op == "2":
            menu_lotes()
        elif op == "3":
            registrar_movimiento()
        elif op == "8":
            guardar_datos()
            print("Datos guardados manualmente con éxito.")
        elif op == "0":
            print("Saliendo del sistema...")
            guardar_datos()
            break
        elif op in ["4", "5", "6", "7"]:
            print("Esta función la haremos en el siguiente paso.")
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    menu()