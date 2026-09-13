import json
from datetime import datetime
from pathlib import Path

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
    """Calcula el stock dinámicamente sumando entradas y restando salidas/ventas según las reglas de negocio."""
    stock = 0
    for mov in datos["movimientos"]:
        if mov["producto_codigo"] == codigo:
            if mov["tipo"] == "ENTRADA":
                stock += mov["cantidad"]
            elif mov["tipo"] in ["SALIDA", "VENTA"]:
                stock -= mov["cantidad"]
    return stock


def gestion_productos():
    print("\n--- REGISTRAR NUEVO PRODUCTO ---")
    codigo = input("Código del producto (Ej: P001): ").strip().upper()
    
    if any(p["codigo"] == codigo for p in datos["productos"]):
        print("Error: Ya existe un producto con este código.")
        return

    nombre = input("Nombre del producto: ").strip()
    categoria = input("Categoría: ").strip()
    unidad = input("Unidad de medida (Ej: kg, unidad): ").strip()
    
    while True:
        try:
            precio = float(input("Precio de venta: "))
            stock_min = int(input("Stock mínimo para alertas: "))
            if precio > 0 and stock_min >= 0:
                break
            print("Error: El precio debe ser > 0 y el stock mínimo >= 0.")
        except ValueError:
            print("Error: Ingrese valores numéricos válidos.")

    producto = {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "unidad": unidad,
        "precio": precio,
        "stock_minimo": stock_min,
        "activo": True
    }
    
    datos["productos"].append(producto)
    guardar_datos() 
    print(f"Producto '{nombre}' registrado y guardado con éxito.")

def listar_productos():
    print("\n--- LISTA DE PRODUCTOS ACTIVOS ---")
    print(f"{'CÓDIGO':<8} | {'NOMBRE':<20} | {'PRECIO':<10} | {'STOCK MIN':<10} | {'STOCK ACTUAL':<12}")
    print("-" * 73)
    
    hay_productos = False
    for p in datos["productos"]:
        if p["activo"]:
            hay_productos = True
            stock_actual = calcular_stock(p["codigo"])
            print(f"{p['codigo']:<8} | {p['nombre']:<20} | {fmt_dinero(p['precio']):<10} | {p['stock_minimo']:<10} | {stock_actual:<12}")
    
    if not hay_productos:
        print("No hay productos registrados o activos.")
    print("-" * 73)



def menu():
    cargar_datos() 
    
    while True:
        print("\n==== AGROCONTROL CBA ====")
        print("1. Registrar producto")
        print("2. Listar productos")
        print("0. Salir")
        
        op = input("Seleccione una opción: ")
        
        if op == "1":
            gestion_productos()
        elif op == "2":
            listar_productos()
        elif op == "0":
            print("Saliendo del sistema...")
            guardar_datos()
            break
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    menu()