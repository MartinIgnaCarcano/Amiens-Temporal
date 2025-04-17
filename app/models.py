from app import db
from datetime import datetime

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200))
    stock = db.Column(db.Integer)
    stock_minimo = db.Column(db.Integer)
    proveedor = db.Column(db.String(100))
    categoria = db.Column(db.String(50))
    estado = db.Column(db.String(30))
    
    def actualizar_estado(self):
        if self.stock<=0:
            self.estado = 'Sin Stock'
        elif self.stock<self.stock_minimo:
            self.estado = 'Bajo Stock'
        else:
            self.estado = 'En Stock'
    
class Extraccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    descripcion = db.Column(db.String(200))
    detalles = db.relationship(
        'DetalleExtraccion', 
        backref='extraccion', 
        cascade="all, delete-orphan"  # Elimina detalles al borrar la extracción
    )

class DetalleExtraccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraccion_id = db.Column(db.Integer, db.ForeignKey('extraccion.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    cantidad = db.Column(db.Integer)
    producto = db.relationship('Producto', backref='detalles_extraccion')