from flask import Blueprint, request, jsonify,Response
from app import db
from app.models import Producto, Extraccion, DetalleExtraccion
from datetime import datetime
import json

productos_bp = Blueprint('productos', __name__)

#-------------------
# Rutas para Productos -------------------
#-------------------
@productos_bp.route('/productos', methods=['GET'])
def get_productos():
    productos = Producto.query.all()
    return jsonify([{
        "id": p.id,
        "descripcion": p.descripcion,
        "stock": p.stock,
        "stock_minimo": p.stock_minimo,
        "proveedor": p.proveedor,
        "categoria": p.categoria,
        "estado": p.estado
    } for p in productos])

@productos_bp.route('/productos', methods=['POST'])
def crear_productos_masivos():
    try:
        data = request.get_json()
        # Validación robusta
            
        nuevo_producto = Producto(
            descripcion=data['descripcion'],
            stock=int(data['stock']),
            stock_minimo=int(data['stock_minimo']),
            proveedor=data.get('proveedor', ''),
            categoria=data.get('categoria', 'General')
        )
        nuevo_producto.actualizar_estado()
        
        db.session.add(nuevo_producto)
        db.session.commit()
        
        return jsonify({
            "mensaje": "Producto creado exitosamente",
            "id": nuevo_producto.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": f"Error al crear producto: {str(e)}",
            "tipo_error": type(e).__name__
        }), 500

@productos_bp.route('/productos/<int:id>', methods=['PATCH'])
def modificar_producto(id):
    data = request.json
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({
            "error": f"No se encontró el producto"
        }), 404
    try:
        # Actualizar solo los campos proporcionados
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        if 'stock' in data:
            producto.stock = data['stock']
            producto.actualizar_estado()
        if 'stock_minimo' in data:
            producto.stock_minimo = data['stock_minimo']
            producto.actualizar_estado()
        if 'proveedor' in data:
            producto.proveedor = data['proveedor']
        if 'categoria' in data:
            producto.categoria = data['categoria']
        if 'estado' in data:
            producto.estado = data['estado']
        
        db.session.commit()
        return jsonify({
            "mensaje": "Producto actualizado correctamente",
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
   
@productos_bp.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({
            "error": f"No se encontró el producto"
        }), 404
    try:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({
            "mensaje": "Producto eliminado correctamente",
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
   
#-------------------
# Rutas para Extracciones -------------------
#-------------------
@productos_bp.route('/extracciones', methods=['GET'])
def listar_extracciones():
    extracciones = Extraccion.query.all()
    data = []
    
    for e in extracciones:
        detalles = []
        for d in e.detalles:
            detalles.append({
                "producto_id": d.producto_id,  # Orden explícito
                "cantidad": d.cantidad
            })
        
        data.append({
            "id": e.id,
            "descripcion": e.descripcion,
            "fecha": e.fecha.isoformat(),
            "detalles": detalles
        })
    
    # Serialización manual controlando el orden
    json_str = json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False)
    return Response(json_str, mimetype='application/json')

@productos_bp.route('/extracciones', methods=['POST'])
def crear_extraccion():
    data = request.json
    
    # Validación básica
    if not data or 'productos' not in data:
        return jsonify({"error": "Formato inválido. Se requiere 'productos' como lista"}), 400
    
    try:
        # 1. Validar stock antes de cualquier operación
        productos_con_error = []
        for item in data["productos"]:
            producto = Producto.query.get(item["producto_id"])
            if not producto:
                productos_con_error.append(f"Producto ID {item['producto_id']} no existe")
                continue
            if producto.stock < item["cantidad"]:
                productos_con_error.append(
                    f"Stock insuficiente para {producto.descripcion} (Stock actual: {producto.stock}, Se requieren: {item['cantidad']})"
                )
        
        if productos_con_error:
            return jsonify({"error": "Validación fallida", "detalles": productos_con_error}), 400
        
        # 2. Crear la extracción si todo está OK
        nueva_extraccion = Extraccion(
            descripcion=data.get('descripcion', 'Extracción sin descripción'),
            fecha= datetime.fromisoformat(data.get('fecha')) if data.get('fecha') else datetime.now()
        )
        db.session.add(nueva_extraccion)
        db.session.flush()  # Para obtener el ID

        # 3. Procesar productos y actualizar stock
        for item in data["productos"]:
            producto = Producto.query.get(item["producto_id"])
            
            # Actualizar stock (ya validado)
            producto.stock -= item["cantidad"]
            producto.actualizar_estado()
            # Registrar detalle
            detalle = DetalleExtraccion(
                extraccion_id=nueva_extraccion.id,
                producto_id=producto.id,
                cantidad=item["cantidad"]
            )
            db.session.add(detalle)
        
        db.session.commit()
        
          # Actualiza el estado del producto después de la extracción
        
        return jsonify({
            "mensaje": "Extracción registrada exitosamente",
            "extraccion_id": nueva_extraccion.descripcion,
            "stock_actualizado": [{
                "producto_id": item["producto_id"],
                "nuevo_stock": Producto.query.get(item["producto_id"]).stock
            } for item in data["productos"]]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@productos_bp.route('/extracciones/<int:id>', methods=['PATCH'])
def modificar_extraccion(id):
    extraccion = Extraccion.query.get(id)
    
    if not extraccion:
        return jsonify({
            "error": f"No se encontró ninguna extracción con ID {id}"
        }), 404

    data = request.json
    try:
        # Resto de la lógica de actualización igual que antes
        if 'descripcion' in data:
            extraccion.descripcion = data['descripcion']

            
        db.session.commit()
        return jsonify({
            "mensaje": "Extracción actualizada",
            "extraccion_id": extraccion.id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@productos_bp.route('/extracciones/<int:id>', methods=['DELETE'])
def eliminar_extraccion(id):
    try:
        data = request.get_json(silent=True) or {}
        devolver = data.get('devolver', 0)
        
        extraccion = Extraccion.query.get(id)
        if not extraccion:
            return jsonify({"error": f"No se encontró ninguna extracción con ID {id}"}), 404

        # Restaurar stock si corresponde
        if devolver == 1:
            for detalle in extraccion.detalles:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad
                    producto.actualizar_estado()
        # Eliminar detalles y extracción
        DetalleExtraccion.query.filter_by(extraccion_id=id).delete()
        db.session.delete(extraccion)
        
        db.session.commit()
        
        return jsonify({
            "mensaje": f"Extracción ID {id} eliminada",
            "stock_restaurado": devolver == 1,
            "detalles_eliminados": True
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar la extracción: {str(e)}"}), 500
    
#-------------------