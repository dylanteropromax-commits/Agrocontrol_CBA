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
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    datos[clave] = json.load(f)
            except Exception:
                datos[clave] = []

def guardar_datos():
    for clave, ruta in archivos.items():
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos[clave], f, indent=4)

def fmt_dinero(valor):
    return f"${int(valor):,}".replace(",", ".")

def validar_fecha(fecha_str):
    try:
        datetime.strptime(fecha_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def generar_id(coleccion, prefijo):
    if not datos[coleccion]:
        return f"{prefijo}0001"
    ultimo_id = datos[coleccion][-1]["id"] if "id" in datos[coleccion][-1] else datos[coleccion][-1].get("id_lote", f"{prefijo}0000")
    try:
        numero = int(''.join(filter(str.isdigit, ultimo_id))) + 1 if any(c.isdigit() for c in ultimo_id) else len(datos[coleccion]) + 1
    except Exception:
        numero = len(datos[coleccion]) + 1
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

def listar_productos_tabla():
    print("\n--- LISTA DE PRODUCTOS ACTIVOS ---")
    print(f"{'CÓDIGO':<8} | {'NOMBRE':<20} | {'PRECIO':<10} | {'STOCK MIN':<10} | {'STOCK ACTUAL':<12}")
    print("-" * 73)
    encontrados = 0
    for p in datos["productos"]:
        if p["activo"]:
            stock_actual = calcular_stock(p["codigo"])
            print(f"{p['codigo']:<8} | {p['nombre']:<20} | {fmt_dinero(p['precio']):<10} | {p['stock_minimo']:<10} | {stock_actual:<12}")
            encontrados += 1
    print("-" * 73)
    if encontrados == 0:
        print("No hay productos activos registrados.")

def listar_lotes_tabla():
    print("\n--- LISTA DE LOTES PRODUCTIVOS ---")
    if not datos["lotes"]:
        print("No hay lotes registrados.")
        return
    print(f"{'ID LOTE':<8} | {'PROD':<6} | {'SIEMBRA':<12} | {'ÁREA (m2)':<10} | {'ESTADO':<15} | {'CANT. PROD'}")
    print("-" * 75)
    for l in datos["lotes"]:
        print(f"{l['id_lote']:<8} | {l['producto_codigo']:<6} | {l['fecha_siembra']:<12} | {l['area_m2']:<10} | {l['estado']:<15} | {l['cantidad_producida']}")
    print("-" * 75)

def gestion_productos():
    while True:
        print("\n--- 1. GESTIÓN DE PRODUCTOS ---")
        print("1. Registrar nuevo producto")
        print("2. Listar productos activos")
        print("0. Volver al menú principal")
        op = input("Seleccione una sub-opción: ").strip()
        
        if op == "0":
            print("Regresando al menú principal...")
            break
        elif op == "1":
            print("\n[ Registrar Nuevo Producto ]")
            print("-> Consejo: Escriba '0' en cualquier momento para cancelar.")
            codigo = input("Código del producto (Ej: P001): ").strip().upper()
            if codigo == "0":
                print("Operación cancelada.")
                continue
            if any(p["codigo"] == codigo for p in datos["productos"]):
                print("Error: Ya existe un producto con este código.")
                continue
            nombre = input("Nombre del producto (Ej: Tomate chonto): ").strip()
            if nombre == "0":
                print("Operación cancelada.")
                continue
            categoria = input("Categoría (Ej: Verduras): ").strip()
            if categoria == "0":
                print("Operación cancelada.")
                continue
            unidad = input("Unidad de medida (Ej: Kg, unidad, g, etc.): ").strip()
            if unidad == "0":
                print("Operación cancelada.")
                continue
            
            try:
                precio_input = input("Precio de venta (Ej: 3500): ").strip()
                if precio_input == "0":
                    print("Operación cancelada.")
                    continue
                precio = float(precio_input)

                stock_input = input("Stock mínimo para alertas (Ej: 10): ").strip()
                if stock_input == "0":
                    print("Operación cancelada.")
                    continue
                stock_min = int(stock_input)

                if precio <= 0 or stock_min < 0:
                    print("Error: El precio debe ser mayor a 0 y el stock mínimo mayor o igual a 0.")
                    continue
            except ValueError:
                print("Error: Ingrese valores numéricos válidos.")
                continue

            producto = {
                "codigo": codigo, "nombre": nombre, "categoria": categoria,
                "unidad": unidad, "precio": precio, "stock_minimo": stock_min, "activo": True
            }
            datos["productos"].append(producto)
            guardar_datos() 
            print("¡Producto registrado con éxito!")
            
        elif op == "2":
            listar_productos_tabla()
        else:
            print("Opción inválida. Intente de nuevo.")

def gestion_lotes():
    while True:
        print("\n--- 2. GESTIÓN DE LOTES PRODUCTIVOS ---")
        print("1. Registrar lote de cultivo")
        print("2. Cosechar lote (Cambiar a COSECHADO)")
        print("3. Listar lotes y ver estados")
        print("4. Cancelar lote")
        print("5. Cambiar estado de lote manualmente")
        print("0. Volver al menú principal")
        op = input("Seleccione una sub-opción: ").strip()
        
        if op == "0":
            print("Regresando al menú principal...")
            break
        elif op == "1":
            print("\n[ Registrar Lote Productivo ] (Escriba '0' para cancelar)")
            cod_prod = input("Código del producto a cultivar (Ej: P001): ").strip().upper()
            if cod_prod == "0":
                print("Operación cancelada.")
                continue
            if not any(p["codigo"] == cod_prod and p["activo"] for p in datos["productos"]):
                print("Error: El producto no existe o está inactivo.")
                continue
                
            id_lote = input("ID del Lote (Ej: L001): ").strip().upper()
            if id_lote == "0":
                print("Operación cancelada.")
                continue
            if any(l["id_lote"] == id_lote for l in datos["lotes"]):
                print("Error: Ya existe un lote con este ID.")
                continue
                
            fecha = input("Fecha de siembra (DD/MM/YYYY) (Ej: 15/08/2026): ").strip()
            if fecha == "0":
                print("Operación cancelada.")
                continue
            if not validar_fecha(fecha):
                print("Error: Formato de fecha incorrecto (Use dd/mm/yyyy).")
                continue
            
            try:
                area_input = input("Área en m2 (Ej: 120.5): ").strip()
                if area_input == "0":
                    print("Operación cancelada.")
                    continue
                area = float(area_input)
                if area <= 0:
                    print("Error: El área debe ser mayor a 0.")
                    continue
            except ValueError:
                print("Error: Área inválida.")
                continue

            lote = {
                "id_lote": id_lote, "producto_codigo": cod_prod, "fecha_siembra": fecha,
                "area_m2": area, "cantidad_producida": 0, "estado": "EN_PRODUCCION"
            }
            datos["lotes"].append(lote)
            guardar_datos()
            print("¡Lote registrado con éxito!")
            
        elif op == "2":
            print("\n[ Cosechar Lote ] (Escriba '0' para cancelar)")
            id_lote = input("ID del lote a cosechar (Ej: L001): ").strip().upper()
            if id_lote == "0":
                print("Operación cancelada.")
                continue
            lote = next((l for l in datos["lotes"] if l["id_lote"] == id_lote), None)
            
            if not lote:
                print("Error: El lote ingresado no existe.")
                continue
            if lote["estado"] != "EN_PRODUCCION":
                print(f"Error: El lote se encuentra en estado '{lote['estado']}' y no se puede cosechar.")
                continue

            try:
                cant_input = input("Cantidad producida (Ej: 150): ").strip()
                if cant_input == "0":
                    print("Operación cancelada.")
                    continue
                cantidad = int(cant_input)
                if cantidad <= 0:
                    print("Error: La cantidad debe ser mayor a 0.")
                    continue
            except ValueError:
                print("Error: Ingrese un número válido.")
                continue

            fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            lote["estado"] = "COSECHADO"
            lote["cantidad_producida"] = cantidad

            movimiento = {
                "id": generar_id("movimientos", "M"), "producto_codigo": lote["producto_codigo"],
                "tipo": "ENTRADA", "cantidad": cantidad, "motivo": f"Cosecha lote {id_lote}", "fecha": fecha_hora
            }
            datos["movimientos"].append(movimiento)
            guardar_datos()
            print("¡Cosecha registrada! Se ha actualizado el inventario automáticamente.")

        elif op == "3":
            listar_lotes_tabla()

        elif op == "4":
            print("\n[ Cancelar Lote ] (Escriba '0' para cancelar)")
            id_lote = input("ID del lote a cancelar (Ej: L001): ").strip().upper()
            if id_lote == "0":
                print("Operación cancelada.")
                continue
            lote = next((l for l in datos["lotes"] if l["id_lote"] == id_lote), None)
            
            if not lote:
                print("Error: El lote no existe.")
                continue
            if lote["estado"] == "COSECHADO":
                print("Error: No se puede cancelar un lote que ya fue cosechado.")
                continue
                
            lote["estado"] = "CANCELADO"
            guardar_datos()
            print(f"¡El lote {id_lote} ha sido marcado como CANCELADO!")

        elif op == "5":
            print("\n[ Cambiar Estado de Lote Manualmente ]")
            listar_lotes_tabla()
            if not datos["lotes"]:
                continue
                
            id_lote = input("\nID del lote a modificar (o escriba '0' para cancelar): ").strip().upper()
            if id_lote == "0":
                print("Operación cancelada.")
                continue
            lote = next((l for l in datos["lotes"] if l["id_lote"] == id_lote), None)
            
            if not lote:
                print("Error: El lote no existe.")
                continue
                
            print(f"Estado actual: {lote['estado']}")
            print("Seleccione el nuevo estado:")
            print("  1. EN_PRODUCCION")
            print("  2. COSECHADO")
            print("  3. CANCELADO")
            print("  0. Volver / Cancelar")
            
            nuevo_op = input("Opción de estado [0-3]: ").strip()
            if nuevo_op == "0":
                print("Operación cancelada.")
                continue
                
            estados_map = {
                "1": "EN_PRODUCCION",
                "2": "COSECHADO",
                "3": "CANCELADO"
            }
            
            if nuevo_op in estados_map:
                lote["estado"] = estados_map[nuevo_op]
                guardar_datos()
                print(f"¡El lote {id_lote} ha sido actualizado exitosamente a '{lote['estado']}'!")
            else:
                print("Error: Opción de estado inválida.")
        else:
            print("Opción inválida. Intente de nuevo.")

def movimientos_inventario():
    while True:
        print("\n--- 3. MOVIMIENTOS DE INVENTARIO ---")
        print("1. Registrar movimiento (Entrada / Salida)")
        print("2. Consultar historial de movimientos (con fecha y hora)")
        print("0. Volver al menú principal")
        op = input("Seleccione una sub-opción: ").strip()
        
        if op == "0":
            print("Regresando al menú principal...")
            break
        elif op == "1":
            listar_productos_tabla()
            cod = input("\nCódigo del producto (o escriba '0' para cancelar): ").strip().upper()
            if cod == "0":
                print("Operación cancelada.")
                continue
            if not any(p["codigo"] == cod and p["activo"] for p in datos["productos"]):
                print("Error: El producto no existe o está inactivo.")
                continue

            print("Tipo de movimiento:")
            print("  1. ENTRADA (Ingreso manual)")
            print("  2. SALIDA (Retiro / Merma)")
            print("  0. Cancelar")
            tipo_op = input("Seleccione opción [0-2]: ").strip()
            
            if tipo_op == "0":
                print("Operación cancelada.")
                continue
            if tipo_op not in ["1", "2"]:
                print("Error: Opción no válida.")
                continue

            try:
                cant_input = input("Cantidad de unidades (o '0' para cancelar): ").strip()
                if cant_input == "0":
                    print("Operación cancelada.")
                    continue
                cantidad = int(cant_input)
                if cantidad <= 0:
                    print("Error: La cantidad debe ser mayor a 0.")
                    continue
            except ValueError:
                print("Error: Ingrese un valor numérico entero.")
                continue

            if tipo_op == "2":
                stock_actual = calcular_stock(cod)
                if cantidad > stock_actual:
                    print(f"Error: Stock insuficiente. Stock actual: {stock_actual}, Intentó retirar: {cantidad}.")
                    continue
                tipo_str = "SALIDA"
            else:
                tipo_str = "ENTRADA"

            motivo = input("Motivo del movimiento (Ej: Ajuste de inventario / Donación): ").strip()
            if motivo == "0" or not motivo:
                print("Operación cancelada.")
                continue

            movimiento = {
                "id": generar_id("movimientos", "M"),
                "producto_codigo": cod,
                "tipo": tipo_str,
                "cantidad": cantidad,
                "motivo": motivo,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            datos["movimientos"].append(movimiento)
            guardar_datos()
            print(f"¡Movimiento de {tipo_str} registrado con éxito!")

        elif op == "2":
            print("\n--- HISTORIAL DE MOVIMIENTOS ---")
            if not datos["movimientos"]:
                print("No hay movimientos registrados.")
                continue
            print(f"{'ID':<6} | {'FECHA Y HORA':<17} | {'TIPO':<8} | {'PROD':<6} | {'CANT':<6} | {'MOTIVO'}")
            print("-" * 75)
            for mov in datos["movimientos"]:
                fecha_str = mov.get("fecha", "N/A")
                print(f"{mov.get('id', 'N/A'):<6} | {fecha_str:<17} | {mov.get('tipo', 'N/A'):<8} | {mov.get('producto_codigo', 'N/A'):<6} | {mov.get('cantidad', 0):<6} | {mov.get('motivo', 'N/A')}")
            print("-" * 75)
        else:
            print("Opción inválida. Intente de nuevo.")

def registrar_venta():
    print("\n--- 4. REGISTRAR VENTA ---")
    items = []
    total_venta = 0
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

    while True:
        listar_productos_tabla()
        cod = input("\nCódigo del producto a vender (o escriba 'FIN' para terminar/cancelar): ").strip().upper()
        if cod == 'FIN':
            break

        prod = next((p for p in datos["productos"] if p["codigo"] == cod and p["activo"]), None)
        if not prod:
            print("Error: Producto no válido o inactivo.")
            continue

        stock_actual = calcular_stock(cod)
        try:
            cant_input = input(f"Cantidad a vender de {prod['nombre']} (Stock disponible: {stock_actual}) [0 para cancelar item]: ").strip()
            if cant_input == "0":
                print("Item omitido.")
                continue
            cant = int(cant_input)
            if cant < 0:
                print("Error: La cantidad debe ser mayor a 0.")
                continue
        except ValueError:
            print("Error: Ingrese un número entero válido.")
            continue

        if cant > stock_actual:
            print(f"Error: Stock insuficiente. El stock actual disponible es {stock_actual}.")
            continue

        subtotal = cant * prod["precio"]
        total_venta += subtotal
        items.append({
            "codigo": cod, 
            "cantidad": cant, 
            "precio_unitario": prod["precio"], 
            "subtotal": subtotal
        })

        mov = {
            "id": generar_id("movimientos", "M"), 
            "producto_codigo": cod, 
            "tipo": "VENTA",
            "cantidad": cant, 
            "motivo": "Venta directa en caja", 
            "fecha": fecha_hora_actual
        }
        datos["movimientos"].append(mov)
        print(f"-> ¡Agregado a la factura: {cant}x {prod['nombre']} ({fmt_dinero(subtotal)})!")

    if items: 
        id_v = f"V{len(datos['ventas'])+1:04d}"
        venta = {
            "id": id_v, 
            "fecha": fecha_hoy,
            "items": items, 
            "total": total_venta
        }
        datos["ventas"].append(venta)
        guardar_datos()
        
        print("\n================ FACTURA DE VENTA ================")
        print(f"ID Factura: {venta['id']} | Fecha: {fecha_hoy}")
        print(f"{'CÓDIGO':<8} | {'CANTIDAD':<10} | {'P. UNIT':<10} | {'SUBTOTAL':<10}")
        print("-" * 50)
        for i in items:
            print(f"{i['codigo']:<8} | {i['cantidad']:<10} | {fmt_dinero(i['precio_unitario']):<10} | {fmt_dinero(i['subtotal']):<10}")
        print("-" * 50)
        print(f"TOTAL A PAGAR: {fmt_dinero(total_venta)}")
        print("==================================================\n")
    else:
        print("Venta cancelada (no se agregaron productos).")

def consultar_ventas():
    print("\n--- 5. CONSULTAR VENTAS ---")
    
    if not datos["ventas"]:
        print("No hay ventas registradas en el sistema.")
        return

    print(f"Se encontraron {len(datos['ventas'])} venta(s) registrada(s).\n")
    
    for venta in datos["ventas"]:
        print("=" * 50)
        print(f"ID Factura : {venta.get('id', 'N/A')}")
        print(f"Fecha      : {venta.get('fecha', 'N/A')}")
        print("-" * 50)
        print(f"{'CÓDIGO':<8} | {'CANTIDAD':<10} | {'P. UNIT':<10} | {'SUBTOTAL':<10}")
        print("-" * 50)
        
        items = venta.get("items", [])
        
        if items:
            for item in items:
                print(f"{item.get('codigo', 'N/A'):<8} | {item.get('cantidad', 0):<10} | {fmt_dinero(item.get('precio_unitario', 0)):<10} | {fmt_dinero(item.get('subtotal', 0)):<10}")
        else:
            print("Esta venta no contiene detalle de productos.")
            
        print("-" * 50)
        print(f"TOTAL VENTA: {fmt_dinero(venta.get('total', 0))}")
        print("=" * 50)

def alertas_stock():
    print("\n--- 6. ALERTAS DE STOCK ---")
   

def reportes():
    print("\n--- 7. REPORTES ---")
   

def guardar_datos_manual():
    print("\n--- 8. GUARDAR DATOS ---")
    
def menu():
    cargar_datos() 
    
    while True:
        print("\n==================== AGROCONTROL CBA ====================")
        print("1. Gestión de productos")
        print("2. Gestión de lotes productivos")
        print("3. Movimientos de inventario")
        print("4. Registrar venta")
        print("5. Consultar ventas")
        print("6. Alertas de stock")
        print("7. Reportes")
        print("8. Guardar datos")
        print("0. Salir")
        
        op = input("Seleccione una opción: ").strip()
        
        if op == "1":
            gestion_productos()
        elif op == "2":
            gestion_lotes()
        elif op == "3":
            movimientos_inventario()
        elif op == "4":
            registrar_venta()
        elif op == "5":
            consultar_ventas()
        elif op == "6":
            alertas_stock()
        elif op == "7":
            reportes()
        elif op == "8":
            guardar_datos_manual()
        elif op == "0":
            print("Saliendo del sistema...")
            guardar_datos()
            break
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    menu()